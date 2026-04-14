"""
PPDSBAC Cryptographic Core — Simulation Mode
==============================================
Implements ALL algorithms from:
  Han, Chen, Susilo — "Privacy-Preserving Decentralized Signature-Based
  Access Control", IEEE TDSC Vol.22 No.5, 2025

Algorithms implemented (Section III, Fig.2):
  Global_Setup · Reg_Auth_Setup · Auth_Auth_Setup · Trace_Auth_Setup
  User_Setup · Regist · Enc · Acc_Req · Access_Agg · Dec · Trace

Cryptographic primitives simulated:
  - Bilinear groups (G1, G2, GT) over Zp
  - Multi-signature [Boneh, Drijvers, Neven 2018] — Ref [36]
  - OSBE [Li, Du, Boneh 2003] — Ref [42]
  - ZK Proof of Knowledge (Camenisch et al.) — Ref [60]
  - Fiat-Shamir heuristic (non-interactive) — Ref [61]
  - ElGamal pseudonym encryption for Trace
"""

import hashlib
import json
import os
import secrets
import time

try:
    import pypbc  # type: ignore[import-not-found]
except Exception:
    pypbc = None

# ---------------------------------------------------------------------------
# Field / Group arithmetic over Zp (simulated)
# ---------------------------------------------------------------------------

# Use a 256-bit prime as group order
P = 0xFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFEFFFFFC2F  # secp256k1 p


def modd(x: int) -> int:
    return x % P


def inv(x: int) -> int:
    """Modular inverse via Fermat's little theorem."""
    return pow(x, P - 2, P)


# Group elements are represented as {"g": "G1"|"G2"|"GT", "e": int}
# All group operations are done in the exponent (discrete-log simulation).
# This preserves the bilinear structure: e(g^a, g'^b) = ehat^(ab).

def G1(exp: int) -> dict:
    return {"g": "G1", "e": modd(exp)}


def G2(exp: int) -> dict:
    return {"g": "G2", "e": modd(exp)}


def GT(exp: int) -> dict:
    return {"g": "GT", "e": modd(exp)}


def g1mul(a: dict, b: dict) -> dict:
    return G1(modd(a["e"] + b["e"]))


def g1pow(a: dict, s: int) -> dict:
    return G1(modd(a["e"] * s))


def pairing(a: dict, b: dict) -> dict:
    """e: G1 × G2 → GT.  e(g^a, g'^b) = ê^(ab)."""
    return GT(modd(a["e"] * b["e"]))


def gt_mul(a: dict, b: dict) -> dict:
    return GT(modd(a["e"] + b["e"]))


def gt_eq(a: dict, b: dict) -> bool:
    return a["e"] == b["e"]


def to_hex(elem: dict) -> str:
    return f"0x{elem['e']:064x}"


def _elem_hex(elem) -> str:
    """Stable hex-like fingerprint for debug/JSON output."""
    if isinstance(elem, dict) and "e" in elem:
        return to_hex(elem)
    return "0x" + hashlib.sha256(str(elem).encode()).hexdigest()


def _pbc_enabled() -> bool:
    return pypbc is not None and bool(_PARAMS.get("pypbc"))


def _pbc_ctx() -> dict:
    ctx = _PARAMS.get("pypbc")
    if not ctx:
        raise RuntimeError("pypbc context is unavailable; run global_setup first")
    return ctx


def _pbc_hash_payload(*args) -> bytes:
    return json.dumps(args, sort_keys=True, default=str).encode()


def _pbc_hash_to_group(group: int, *args):
    ctx = _pbc_ctx()
    digest = hashlib.sha256(_pbc_hash_payload(*args)).digest()
    return pypbc.Element.from_hash(ctx["pairing"], group, digest)


def _pbc_zr(v: int):
    return pypbc.Element(_pbc_ctx()["pairing"], pypbc.Zr, value=int(v))


def _sim_scalar(elem_or_int) -> int:
    if isinstance(elem_or_int, dict) and "e" in elem_or_int:
        return int(elem_or_int["e"])
    return int(elem_or_int)


def _init_pypbc_params(a0_seed: int, a1_seed: int, a2_seed: int, b0_seed: int, b1_seed: int) -> dict:
    """
    Initialize pypbc pairing parameters using Parameters(qbits, rbits),
    which is the standard generator API exposed by pypbc.
    """
    if pypbc is None:
        return {}

    qbits = int(os.getenv("PYPBC_QBITS", "512"))
    rbits = int(os.getenv("PYPBC_RBITS", "160"))
    if qbits <= rbits:
        raise ValueError("Invalid pypbc parameters: qbits must be greater than rbits")

    params = pypbc.Parameters(qbits=qbits, rbits=rbits)
    pairing_obj = pypbc.Pairing(params)

    g = pypbc.Element.random(pairing_obj, pypbc.G1)
    g_bar = pypbc.Element.random(pairing_obj, pypbc.G2)
    a0 = pypbc.Element(pairing_obj, pypbc.Zr, value=int(a0_seed))
    a1 = pypbc.Element(pairing_obj, pypbc.Zr, value=int(a1_seed))
    a2 = pypbc.Element(pairing_obj, pypbc.Zr, value=int(a2_seed))
    b0 = pypbc.Element(pairing_obj, pypbc.Zr, value=int(b0_seed))
    b1 = pypbc.Element(pairing_obj, pypbc.Zr, value=int(b1_seed))

    return {
        "params": params,
        "pairing": pairing_obj,
        "qbits": qbits,
        "rbits": rbits,
        "g": g,
        "g_bar": g_bar,
        "g0": g ** a0,
        "g1": g ** a1,
        "g2": g ** a2,
        "h0": g ** b0,
        "h1": g ** b1,
    }


# ---------------------------------------------------------------------------
# Hash functions (SHA-256 based, domain-separated)
# ---------------------------------------------------------------------------

def _sha256(*args) -> int:
    data = json.dumps(args, sort_keys=True, default=str).encode()
    return int(hashlib.sha256(data).hexdigest(), 16) % P


def H1(keyword: str, time_period: str) -> dict:
    """H1: {0,1}* → G1  (hash-to-group)"""
    return G1(_sha256("H1", keyword, time_period))


def H2(*args) -> int:
    """H2: {0,1}* → Zp"""
    return _sha256("H2", *args)


def H3(*args) -> int:
    """H3: {0,1}* → Zp"""
    return _sha256("H3", *args)


# ---------------------------------------------------------------------------
# Global state (single session, in-memory)
# ---------------------------------------------------------------------------

_PARAMS: dict = {}
_SESSION: dict = {}   # stores RA, TA, AAs, Users, Ciphertext


def _session() -> dict:
    return _SESSION


# ---------------------------------------------------------------------------
# Global_Setup(1^λ) → params
# ---------------------------------------------------------------------------

def global_setup() -> dict:
    """
    Generates public parameters:
      params = (e, p, G1, G2, GT, g, g', g0, g1, h0, h1, H1, H2, H3)
    where g0=g^a0, g1=g^a1, h0=g^b0, h1=g^b1  (random exponents)
    """
    a0 = _sha256("fixed_a0_generator")
    a1 = _sha256("fixed_a1_generator")
    a2 = _sha256("fixed_a2_generator")
    b0 = _sha256("fixed_b0_generator")
    b1 = _sha256("fixed_b1_generator")

    pypbc_ctx = _init_pypbc_params(a0, a1, a2, b0, b1) if pypbc is not None else {}

    _PARAMS.clear()
    _PARAMS.update({
        "p":  P,
        "g":  G1(1),        # generator of G1
        "g_": G2(1),        # generator of G2
        "g0": G1(a0),       # g^a0
        "g1": G1(a1),       # g^a1
        "g2": G1(a2),       # g^a2
        "h0": G1(b0),       # g^b0
        "h1": G1(b1),       # g^b1
        "gt": GT(1),        # e(g, g')
        "pypbc": pypbc_ctx,
    })
    _SESSION.clear()

    out = {
        "p":    f"0x{P:064x}",
        "g":    to_hex(_PARAMS["g"]),
        "g_":   to_hex(_PARAMS["g_"]),
        "g0":   to_hex(_PARAMS["g0"]),
        "g1":   to_hex(_PARAMS["g1"]),
        "g2":   to_hex(_PARAMS["g2"]),
        "h0":   to_hex(_PARAMS["h0"]),
        "h1":   to_hex(_PARAMS["h1"]),
        "H1":   "SHA-256 → G1 (hash-to-group)",
        "H2":   "SHA-256 → Zp",
        "H3":   "SHA-256 → Zp",
        "curve": "Simulated Type-III pairing (demo mode)",
    }
    if pypbc_ctx:
        out["pypbc"] = {
            "enabled": True,
            "curve_type": "Type A",
            "qbits": pypbc_ctx["qbits"],
            "rbits": pypbc_ctx["rbits"],
            "generator_api": "Parameters(qbits, rbits)",
        }
    else:
        out["pypbc"] = {
            "enabled": False,
            "reason": "pypbc unavailable in current environment",
        }
    return out


# ---------------------------------------------------------------------------
# Reg_Auth_Setup(1^λ) → (SK_RA, PK_RA)
# ---------------------------------------------------------------------------

def reg_auth_setup() -> dict:
    x_ra = secrets.randbelow(P)
    Y_RA = G2(x_ra)          # g'^x_ra  ∈ G2  (for pairing with G1 credentials)
    ra = {"SK_RA": x_ra, "PK_RA": Y_RA, "PK_RA_hex": to_hex(Y_RA)}
    _SESSION["ra"] = ra
    return ra


# ---------------------------------------------------------------------------
# Auth_Auth_Setup(1^λ) → (SK_j, PK_j)  for each AA_j
# ---------------------------------------------------------------------------

def auth_auth_setup(aa_id: str) -> dict:
    x_j = secrets.randbelow(P)
    Y_j = G1(x_j)            # g^x_j ∈ G1
    return {"aa_id": aa_id, "SK_j": x_j, "PK_j": Y_j, "PK_j_hex": to_hex(Y_j)}


# ---------------------------------------------------------------------------
# Trace_Auth_Setup(1^λ) → (SK_TA, PK_TA)
# ---------------------------------------------------------------------------

def trace_auth_setup() -> dict:
    x_ta = secrets.randbelow(P)
    Y_TA = G1(x_ta)
    ta = {"SK_TA": x_ta, "PK_TA": Y_TA, "PK_TA_hex": to_hex(Y_TA)}
    _SESSION["ta"] = ta
    return ta


# ---------------------------------------------------------------------------
# User_Setup(1^λ) → (SK_U, PK_U)
# ---------------------------------------------------------------------------

def user_setup(user_id: str) -> dict:
    x_u = secrets.randbelow(P)
    Y_U = G1(x_u)
    return {"user_id": user_id, "SK_U": x_u, "PK_U": Y_U, "PK_U_hex": to_hex(Y_U)}


# ---------------------------------------------------------------------------
# Regist(U ↔ RA) → (Π_U, σ_U)
#
# Credential: σ_U = (g0 · Y_U · g1^e_u)^(1/(x_ra + d_u))
# Proof Π_U: PoK{x_u : Y_U = g^x_u}  (Schnorr, Fiat-Shamir)
# ---------------------------------------------------------------------------

def regist(user: dict, ra: dict) -> dict:
    x_u   = user["SK_U"]
    Y_U   = user["PK_U"]
    x_ra  = ra["SK_RA"]
    g0    = _PARAMS["g0"]
    g1p   = _PARAMS["g1"]

    # --- Step 1: User → ZK proof of x_u ---
    r_zk   = secrets.randbelow(P)
    R_zk   = G1(r_zk)                                   # commitment R = g^r
    c_zk   = H2("regist_pi", to_hex(Y_U), to_hex(R_zk)) # challenge c = H(Y_U, R)
    s_zk   = modd(r_zk - c_zk * x_u)                    # response s = r - c·x_u

    # RA verifies: g^s · Y_U^c == R
    lhs = g1mul(G1(s_zk), g1pow(Y_U, c_zk))
    assert lhs["e"] == R_zk["e"], "ZK proof invalid"

    # --- Step 2: RA issues credential ---
    e_u = secrets.randbelow(P)
    d_u = secrets.randbelow(P)
    # numerator exp = g0.e + x_u + g1.e * e_u
    num_exp  = modd(g0["e"] + x_u + modd(g1p["e"] * e_u))
    inv_exp  = inv(modd(x_ra + d_u))
    sigma_e  = modd(num_exp * inv_exp)
    sigma_U  = G1(sigma_e)

    return {
        "pi_U": {
            "R_hex": to_hex(R_zk), "challenge": hex(c_zk), "s": hex(s_zk),
            "statement": "PoK{ x_u : Y_U = g^x_u }",
        },
        "sigma_U": sigma_U,
        "sigma_U_hex": to_hex(sigma_U),
        "e_u": e_u, "d_u": d_u,
        "zk_verified": True,
        "credential_type": "BBS+-style anonymous credential",
    }


# ---------------------------------------------------------------------------
# Pseudonym generation  PU = (PU1, PU2) = ElGamal enc of Y_U under Y_TA
#   PU1 = g^r_u,   PU2 = Y_U · Y_TA^r_u
# ---------------------------------------------------------------------------

def gen_pseudonym(user: dict, ta: dict) -> dict:
    r_u  = secrets.randbelow(P)
    Y_U  = user["PK_U"]
    Y_TA = ta["PK_TA"]
    PU1  = G1(r_u)
    PU2  = g1mul(Y_U, g1pow(Y_TA, r_u))
    return {
        "PU1": PU1, "PU1_hex": to_hex(PU1),
        "PU2": PU2, "PU2_hex": to_hex(PU2),
        "_r_u": r_u,
    }


def _enc_pypbc(aa_pks: list, keyword: str, time_period: str, message: str) -> dict:
    ctx = _pbc_ctx()
    pairing_obj = ctx["pairing"]

    aa_Y = [ctx["g_bar"] ** _pbc_zr(_sim_scalar(pk)) for pk in aa_pks]
    aa_hex = [_elem_hex(y) for y in aa_Y]

    z_vals = [_pbc_hash_to_group(pypbc.Zr, "H2", "z_coeff", aa_hex[i], *aa_hex)
              for i in range(len(aa_Y))]

    Y_pi = pypbc.Element.one(pairing_obj, pypbc.G2)
    for y_i, z_i in zip(aa_Y, z_vals):
        Y_pi = Y_pi * (y_i ** z_i)

    t = pypbc.Element.random(pairing_obj, pypbc.Zr)
    h1_wt = _pbc_hash_to_group(pypbc.G1, "H1", keyword, time_period)
    M = _pbc_hash_to_group(pypbc.GT, "MSG", message)

    C1 = M * (pairing_obj.apply(h1_wt, Y_pi) ** t)
    C2 = ctx["g_bar"] ** t
    C3 = ctx["h0"] ** t
    C4 = ctx["h1"] ** t

    return {
        "C1": C1, "C1_hex": _elem_hex(C1),
        "C2": C2, "C2_hex": _elem_hex(C2),
        "C3": C3, "C3_hex": _elem_hex(C3),
        "C4": C4, "C4_hex": _elem_hex(C4),
        "Y_pi_hex": _elem_hex(Y_pi),
        "z_hex": [_elem_hex(z) for z in z_vals],
        "policy_size": len(aa_pks),
    }


def _acc_req_pypbc(user: dict, credential: dict, pseudonym: dict,
                   aa: dict, all_aa_pks: list,
                   keyword: str, time_period: str) -> dict:
    if "ra" not in _SESSION or "ta" not in _SESSION:
        raise ValueError("Acc_Req(pypbc) requires RA and TA in session")

    ctx = _pbc_ctx()
    pairing_obj = ctx["pairing"]
    g = ctx["g"]
    g_bar = ctx["g_bar"]
    g0 = ctx["g0"]
    g1 = ctx["g1"]
    g2 = ctx["g2"]
    h0 = ctx["h0"]
    h1 = ctx["h1"]

    x_u = _pbc_zr(user["SK_U"])
    e_u = _pbc_zr(credential["e_u"])
    d_u = _pbc_zr(credential["d_u"])
    x_j = _pbc_zr(aa["SK_j"])
    x_ra = _pbc_zr(_SESSION["ra"]["SK_RA"])
    x_ta = _pbc_zr(_SESSION["ta"]["SK_TA"])

    Y_RA = g_bar ** x_ra
    Y_TA = g ** x_ta
    Y_U = g ** x_u

    r_u = _pbc_zr(pseudonym.get("_r_u", secrets.randbelow(P)))
    s_u = pypbc.Element.random(pairing_obj, pypbc.Zr)
    y_u = s_u * d_u

    PU1 = g ** r_u
    PU2 = Y_U * (Y_TA ** r_u)

    # Recompute sigma_U in pypbc domain to avoid cross-domain mismatch with
    # legacy simulation credential representation.
    denom = x_ra + d_u
    if int(denom) == 0:
        raise ValueError("invalid credential: x_ra + d_u == 0 in Zr")
    sigma_u = (g0 * Y_U * (g1 ** e_u)) ** (~denom)
    sigma_prime = sigma_u * (g2 ** s_u)

    v_x = pypbc.Element.random(pairing_obj, pypbc.Zr)
    v_r = pypbc.Element.random(pairing_obj, pypbc.Zr)
    v_s = pypbc.Element.random(pairing_obj, pypbc.Zr)
    v_e = pypbc.Element.random(pairing_obj, pypbc.Zr)
    v_d = pypbc.Element.random(pairing_obj, pypbc.Zr)
    v_y = pypbc.Element.random(pairing_obj, pypbc.Zr)

    R1 = g ** v_r
    R2 = (g ** v_x) * (Y_TA ** v_r)
    R3 = (pairing_obj.apply(g, g_bar) ** v_x) \
        * (pairing_obj.apply(g1, g_bar) ** v_e) \
        * (pairing_obj.apply(sigma_prime, g_bar) ** (-v_d)) \
        * (pairing_obj.apply(g2, g_bar) ** v_y) \
        * (pairing_obj.apply(g2, Y_RA) ** v_s)

    c = _pbc_hash_to_group(
        pypbc.Zr,
        "H3", "AccReqChallenge",
        _elem_hex(PU1), _elem_hex(PU2), _elem_hex(sigma_prime),
        _elem_hex(R1), _elem_hex(R2), _elem_hex(R3)
    )

    z_x = v_x + (c * x_u)
    z_r = v_r + (c * r_u)
    z_s = v_s + (c * s_u)
    z_e = v_e + (c * e_u)
    z_d = v_d + (c * d_u)
    z_y = v_y + (c * y_u)

    R1_p = (g ** z_r) * (PU1 ** (-c))
    R2_p = (g ** z_x) * (Y_TA ** z_r) * (PU2 ** (-c))

    R3_p = (pairing_obj.apply(g, g_bar) ** z_x) \
        * (pairing_obj.apply(g1, g_bar) ** z_e) \
        * (pairing_obj.apply(sigma_prime, g_bar) ** (-z_d)) \
        * (pairing_obj.apply(g2, g_bar) ** z_y) \
        * (pairing_obj.apply(g2, Y_RA) ** z_s) \
        * (pairing_obj.apply(sigma_prime, Y_RA) ** (-c)) \
        * (pairing_obj.apply(g0, g_bar) ** c)

    c_check = _pbc_hash_to_group(
        pypbc.Zr,
        "H3", "AccReqChallenge",
        _elem_hex(PU1), _elem_hex(PU2), _elem_hex(sigma_prime),
        _elem_hex(R1_p), _elem_hex(R2_p), _elem_hex(R3_p)
    )
    proof_ok = (c == c_check)
    if not proof_ok:
        raise ValueError(
            "Acc_Req proof verification failed under pypbc "
            f"(c={_elem_hex(c)}, c_check={_elem_hex(c_check)})"
        )

    all_Y = [g_bar ** _pbc_zr(_sim_scalar(pk)) for pk in all_aa_pks]
    all_Y_hex = [_elem_hex(y) for y in all_Y]
    Y_j = g_bar ** x_j
    z_i = _pbc_hash_to_group(pypbc.Zr, "H2", "z_coeff", _elem_hex(Y_j), *all_Y_hex)

    h_id = _pbc_hash_to_group(pypbc.Zr, "H3", "PU", _elem_hex(PU1), _elem_hex(PU2))
    msg = _pbc_hash_to_group(pypbc.G1, "H1", keyword, time_period) * h0 * (h1 ** h_id)
    K_i = msg ** (x_j * z_i)

    return {
        "proof_verified": proof_ok,
        "PU1_hex": _elem_hex(PU1),
        "PU2_hex": _elem_hex(PU2),
        "sigma_prime_hex": _elem_hex(sigma_prime),
        "K_j_hex": _elem_hex(K_i),
        "msg_hex": _elem_hex(msg),
        "z_i_hex": _elem_hex(z_i),
        "challenge_hex": _elem_hex(c),
        "formula": f"K_i = (H1({keyword}||{time_period})*h0*h1^H3(PU))^(x_i*z_i)",
    }


# ---------------------------------------------------------------------------
# Acc_Req(U ↔ AA_j) → K_j
#
# z_j = H2(Y_j ‖ Y_λ1 ‖ … ‖ Y_λk)         (rogue-key protection, [36])
# msg = H1(W‖TP) · h0 · h1^H2(PU1‖PU2)
# K_j = msg^(x_j · z_j)
# ---------------------------------------------------------------------------

def acc_req(user: dict, credential: dict, pseudonym: dict,
            aa: dict, all_aa_pks: list,
            keyword: str, time_period: str) -> dict:
    x_j  = aa["SK_j"]
    Y_j  = aa["PK_j"]
    PU1  = pseudonym["PU1"]
    PU2  = pseudonym["PU2"]
    h0   = _PARAMS["h0"]
    h1   = _PARAMS["h1"]

    # z_j: rogue-key protection coefficient
    pk_exps = [to_hex(Y_j)] + [to_hex(pk) for pk in all_aa_pks]
    z_j = H2("z_coeff", *pk_exps)

    # msg element
    h1_wt  = H1(keyword, time_period)
    h2_pu  = H2("pu_hash", to_hex(PU1), to_hex(PU2))
    msg    = g1mul(h1_wt, g1mul(h0, g1pow(h1, h2_pu)))

    # Signature K_j = msg^(x_j * z_j)
    K_j = g1pow(msg, modd(x_j * z_j))

    out = {
        "aa_id":   aa["aa_id"],
        "K_j":     K_j,
        "K_j_hex": to_hex(K_j),
        "z_j":     z_j,
        "keyword": keyword, "time_period": time_period,
        "msg_hex": to_hex(msg),
        "formula": f"K_j = (H1({keyword}‖{time_period})·h0·h1^H2(PU))^(x_j·z_j)",
        "pypbc_enabled": _pbc_enabled(),
        "pypbc_used": False,
        "compute_backend": "simulation",
    }

    if out["pypbc_enabled"]:
        try:
            pbc_out = _acc_req_pypbc(user, credential, pseudonym, aa, all_aa_pks, keyword, time_period)
            out.update({
                "pypbc_used": True,
                "compute_backend": "simulation+pypbc",
                "proof_verified": pbc_out["proof_verified"],
                "K_j_pypbc_hex": pbc_out["K_j_hex"],
                "msg_pypbc_hex": pbc_out["msg_hex"],
                "z_i_pypbc_hex": pbc_out["z_i_hex"],
                "challenge_pypbc_hex": pbc_out["challenge_hex"],
                "formula_pypbc": pbc_out["formula"],
            })
        except Exception as exc:
            out.update({
                "pypbc_used": False,
                "proof_verified": False,
                "pypbc_error": str(exc),
            })

    return out


# ---------------------------------------------------------------------------
# Access_Agg(K1,…,Kk) → AK_U = ∏ K_i  (BLS aggregation)
# ---------------------------------------------------------------------------

def access_agg(permissions: list) -> dict:
    agg_e = 0
    for p in permissions:
        agg_e = modd(agg_e + p["K_j"]["e"])
    AK_U = G1(agg_e)
    return {
        "AK_U": AK_U, "AK_U_hex": to_hex(AK_U),
        "num_permissions": len(permissions),
        "formula": "AK_U = K_1 · K_2 · … · K_k  (BLS aggregate in G1)",
    }


# ---------------------------------------------------------------------------
# Enc(params, PK_λ1,…,PK_λk, W, TP_E, M) → CT = (C1,C2,C3,C4)
#
# OSBE scheme [Li, Du, Boneh 2003]:
#   γ ←$ Zp
#   C2 = g^γ,  C3 = h0^γ,  C4 = h1^γ
#   C1 = M_gt · e(H1(W‖TP), ∏ Y_λi^z_i)^γ
# ---------------------------------------------------------------------------

def enc(aa_pks: list, keyword: str, time_period: str, message: str) -> dict:
    h0  = _PARAMS["h0"]
    h1  = _PARAMS["h1"]
    g_  = _PARAMS["g_"]
    gamma = secrets.randbelow(P)

    # z_i coefficients
    pk_exps = [to_hex(pk) for pk in aa_pks]
    z_vals  = [H2("z_coeff", to_hex(pk), *pk_exps) for pk in aa_pks]

    # ∏ Y_λi^z_i  ∈ G1
    agg_pk_e = sum(modd(pk["e"] * z) for pk, z in zip(aa_pks, z_vals)) % P
    agg_pk   = G1(agg_pk_e)

    # e(H1(W‖TP), agg_pk)^γ  ∈ GT
    h1_wt     = H1(keyword, time_period)
    pair_base = pairing(h1_wt, G2(agg_pk["e"]))
    pair_gam  = GT(modd(pair_base["e"] * gamma))

    # Encode message as GT element (XOR-style in log-space)
    M_int = int(hashlib.sha256(message.encode()).hexdigest(), 16) % P
    C1    = GT(modd(M_int + pair_gam["e"]))

    C2 = G1(gamma)
    C3 = g1pow(h0, gamma)
    C4 = g1pow(h1, gamma)

    out = {
        "C1": C1, "C1_hex": to_hex(C1),
        "C2": C2, "C2_hex": to_hex(C2),
        "C3": C3, "C3_hex": to_hex(C3),
        "C4": C4, "C4_hex": to_hex(C4),
        "keyword": keyword, "time_period": time_period,
        "_message": message, "_M_int": M_int,
        "_pair_gam_e": pair_gam["e"],
        "pypbc_enabled": _pbc_enabled(),
        "pypbc_used": False,
        "compute_backend": "simulation",
    }

    if out["pypbc_enabled"]:
        try:
            pbc_ct = _enc_pypbc(aa_pks, keyword, time_period, message)
            out.update({
                "pypbc_used": True,
                "compute_backend": "simulation+pypbc",
                "C1_pypbc_hex": pbc_ct["C1_hex"],
                "C2_pypbc_hex": pbc_ct["C2_hex"],
                "C3_pypbc_hex": pbc_ct["C3_hex"],
                "C4_pypbc_hex": pbc_ct["C4_hex"],
                "Y_pi_pypbc_hex": pbc_ct["Y_pi_hex"],
                "policy_size": pbc_ct["policy_size"],
            })
        except Exception as exc:
            out.update({
                "pypbc_used": False,
                "pypbc_error": str(exc),
            })

    return out


# ---------------------------------------------------------------------------
# Dec(params, AK_U, CT) → M
#
# Check TP_E |= TP_U first, then:
#   M = C1 · e(AK_U, C2)^(-1) · [correction terms for C3,C4]
# Simplified correctness proof (Section III, equation at bottom of page):
#   e(K_U, C2) == e(H1·h0·h1^H2(PU), ∏Y_λi^z_i)^γ
# ---------------------------------------------------------------------------

def dec(ct: dict, agg_key: dict, pseudonym: dict,
        aa_pks: list, keyword: str, time_period: str) -> dict:
    """
    Dec(params, AK_U, CT) → M

    Correctness equation (Section III, paper):
      M = C1 · e(C3·C4^H2(PU), agg_pk)^(-1) · e(AK_U, C2)^(-1) ... simplified as:

    In log-space simulation:
      pair_AK  = AK_U.e * C2.e   (= e(AK_U, g)^γ in real scheme)
      correction = (h0.e + h1.e*H2(PU)) * agg_pk.e * γ
                 (= e(C3·C4^H2(PU), agg_pk) in real scheme)
      net_pair = pair_AK - correction  == enc_pair_gam
      M_rec    = C1.e - net_pair
    """
    if ct["time_period"] != time_period:
        return {"success": False, "reason": f"时间段不匹配：密文为 '{ct['time_period']}'，权限时间段为 '{time_period}'"}
    if ct["keyword"] != keyword:
        return {"success": False, "reason": f"关键词不匹配：密文为 '{ct['keyword']}'，请求关键词为 '{keyword}'"}

    p    = _PARAMS
    AK_U = agg_key["AK_U"]
    C2   = ct["C2"]
    C1   = ct["C1"]
    PU1  = pseudonym.get("PU1", {})
    PU2  = pseudonym.get("PU2", {})

    # Recompute z_i and agg_pk_e (same as enc)
    pk_exps  = [to_hex(pk) for pk in aa_pks]
    z_vals   = [H2("z_coeff", to_hex(pk), *pk_exps) for pk in aa_pks]
    agg_pk_e = sum(modd(pk["e"] * z) for pk, z in zip(aa_pks, z_vals)) % P
    gamma    = C2["e"]

    # H2(PU1 || PU2) — same hash used in Acc_Req
    h2_pu = H2("pu_hash", to_hex(PU1) if PU1 else "", to_hex(PU2) if PU2 else "")

    # e(AK_U, C2) in log-space
    pair_ak = modd(AK_U["e"] * gamma)

    # Correction: e(C3 * C4^H2(PU), agg_pk) = (h0^γ * (h1^γ)^H2(PU), agg_pk)
    #           = e(h0·h1^H2(PU), agg_pk)^γ
    correction = modd((p["h0"]["e"] + modd(p["h1"]["e"] * h2_pu)) * agg_pk_e % P * gamma)

    net_pair  = modd(pair_ak - correction)
    M_rec     = modd(C1["e"] - net_pair)

    success = (M_rec == ct["_M_int"])
    return {
        "success": success,
        "message": ct["_message"] if success else None,
        "non_interactive": True,
        "time_period_check": f"TP_E='{ct['time_period']}' |= TP_U='{time_period}' ✓",
        "note": "服务提供商无需在线——OSBE实现非交互式认证",
    }


# ---------------------------------------------------------------------------
# Trace(params, SK_TA, PU, Π_U) → PK_U
#
# PK_U = PU2 / PU1^x_ta = Y_U · Y_TA^r_u / (g^r_u)^x_ta = Y_U
# ---------------------------------------------------------------------------

def trace(pseudonym: dict, ta: dict) -> dict:
    x_ta = ta["SK_TA"]
    PU1  = pseudonym["PU1"]
    PU2  = pseudonym["PU2"]
    # PK_U = PU2 · PU1^(-x_ta)
    rec  = g1mul(PU2, g1pow(PU1, modd(P - x_ta)))
    return {
        "recovered_PK_U": rec,
        "recovered_PK_U_hex": to_hex(rec),
        "formula": "PK_U = PU2 · PU1^(-x_ta) = Y_U·Y_TA^r / g^(r·x_ta) = Y_U",
    }


# ---------------------------------------------------------------------------
# Security property demos
# ---------------------------------------------------------------------------

def demo_unlinkability(user: dict, ta: dict) -> dict:
    """Two requests → two unlinkable pseudonyms (DDH)."""
    pu1 = gen_pseudonym(user, ta)
    pu2 = gen_pseudonym(user, ta)
    return {
        "request_1": {"PU1": pu1["PU1_hex"], "PU2": pu1["PU2_hex"]},
        "request_2": {"PU1": pu2["PU1_hex"], "PU2": pu2["PU2_hex"]},
        "are_linked": pu1["PU1"]["e"] == pu2["PU1"]["e"],
        "explanation": (
            "每次访问请求随机选取 r_u ← Zp，生成 PU1=g^r_u 不同。"
            "即使 RA、所有 AA 联合也无法判断两次请求是否来自同一用户（DDH假设）。"
        ),
    }


def demo_unforgeability(aa: dict, all_aa_pks: list,
                        keyword: str, time_period: str) -> dict:
    """Forgery without SK_j fails bilinear pairing check (Co-CDH)."""
    h0 = _PARAMS["h0"]
    h1 = _PARAMS["h1"]

    fake_exp = secrets.randbelow(P)
    forged_K = G1(fake_exp)

    Y_j = aa["PK_j"]
    pk_exps = [to_hex(pk) for pk in all_aa_pks]
    z_j = H2("z_coeff", to_hex(Y_j), *pk_exps)

    PU1 = G1(secrets.randbelow(P))
    PU2 = G1(secrets.randbelow(P))
    h2_pu = H2("pu_hash", to_hex(PU1), to_hex(PU2))
    h1_wt = H1(keyword, time_period)
    msg   = g1mul(h1_wt, g1mul(h0, g1pow(h1, h2_pu)))

    # Verify: e(K_j, g') == e(msg^z_j, Y_j)
    lhs = pairing(forged_K, G2(1))
    rhs = pairing(g1pow(msg, z_j), G2(aa["SK_j"]))
    forgery_ok = gt_eq(lhs, rhs)

    return {
        "forged_K_hex": to_hex(forged_K),
        "forgery_succeeds": forgery_ok,
        "verify_eq": "e(K_j, g') =? e(H1(W‖TP)·h0·h1^H2(PU), Y_j^z_j)",
        "explanation": (
            "伪造者没有 SK_j，无法产生满足双线性对验证等式的 K_j，"
            "安全性归约至 Co-CDH 假设。"
        ),
    }


# ---------------------------------------------------------------------------
# Benchmark
# ---------------------------------------------------------------------------

def benchmark(n_aas: int = 10) -> dict:
    """Run full protocol and return per-algorithm timings (ms)."""
    t = {}

    def timed(name, fn):
        t0 = time.perf_counter()
        r  = fn()
        t[name] = round((time.perf_counter() - t0) * 1000, 3)
        return r

    timed("Global_Setup",     global_setup)
    ra   = timed("Reg_Auth_Setup",  reg_auth_setup)
    ta   = timed("Trace_Auth_Setup", trace_auth_setup)
    aas  = timed("Auth_Auth_Setup", lambda: [auth_auth_setup(f"AA{i+1}") for i in range(n_aas)])
    user = timed("User_Setup",      lambda: user_setup("BenchUser"))
    cred = timed("Regist",          lambda: regist(user, ra))
    aa_pks = [a["PK_j"] for a in aas]
    ct   = timed("Enc",             lambda: enc(aa_pks, "kw", "T1", "BenchMsg"))
    pu   = timed("Gen_Pseudonym",   lambda: gen_pseudonym(user, ta))
    perms= timed("Acc_Req",         lambda: [acc_req(user, cred, pu, aa, aa_pks, "kw", "T1") for aa in aas])
    agg  = timed("Acc_Agg",         lambda: access_agg(perms))
    timed("Dec",   lambda: dec(ct, agg, pu, aa_pks, "kw", "T1"))
    timed("Trace", lambda: trace(pu, ta))

    return {"n_aas": n_aas, "timings_ms": t}
