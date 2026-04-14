from flask import Blueprint, jsonify, request
import time as _time
from crypto import (
    global_setup, reg_auth_setup, auth_auth_setup,
    trace_auth_setup, user_setup, regist,
    gen_pseudonym, enc, acc_req, access_agg, dec, trace,
    _session
)

bp = Blueprint("workflow", __name__)
S = _session


@bp.route("/pseudonym", methods=["POST"])
def api_pseudonym():
    uid = (request.json or {}).get("user_id", "Alice")
    s = S()
    u  = s.get("users", {}).get(uid)
    ta = s.get("ta")
    if not u or not ta:
        return jsonify({"ok": False, "error": "缺少用户或TA"}), 400
    pu = gen_pseudonym(u, ta)
    u["pu"] = pu
    return jsonify({
        "ok": True,
        "PU1_hex": pu["PU1_hex"], "PU2_hex": pu["PU2_hex"],
        "formula": "PU = (g^r_u,  Y_U · Y_TA^r_u)  — ElGamal加密Y_U",
        "unlinkable": True,
        "msg": f"用户 {uid} 生成新鲜伪名（不同请求的伪名不可关联）",
    })


@bp.route("/enc", methods=["POST"])
def api_enc():
    d       = request.json or {}
    kw      = d.get("keyword",     "medical_record")
    tp      = d.get("time_period", "2025-Q1")
    message = d.get("message",     "Patient Record #042 — Confidential")
    sel_ids = d.get("aa_ids", None)
    s = S()
    aas = s.get("aas", [])
    if not aas:
        return jsonify({"ok": False, "error": "请先初始化授权机构"}), 400
    sel = [a for a in aas if a["aa_id"] in sel_ids] if sel_ids else aas
    aa_pks = [a["PK_j"] for a in sel]
    ct = enc(aa_pks, kw, tp, message)
    s["ct"]       = ct
    s["sel_aas"]  = sel
    return jsonify({
        "ok": True,
        "C1_hex": ct["C1_hex"], "C2_hex": ct["C2_hex"],
        "C3_hex": ct["C3_hex"], "C4_hex": ct["C4_hex"],
        "pypbc_enabled": ct.get("pypbc_enabled", False),
        "pypbc_used": ct.get("pypbc_used", False),
        "compute_backend": ct.get("compute_backend", "simulation"),
        "pypbc_error": ct.get("pypbc_error"),
        "C1_pypbc_hex": ct.get("C1_pypbc_hex"),
        "C2_pypbc_hex": ct.get("C2_pypbc_hex"),
        "C3_pypbc_hex": ct.get("C3_pypbc_hex"),
        "C4_pypbc_hex": ct.get("C4_pypbc_hex"),
        "Y_pi_pypbc_hex": ct.get("Y_pi_pypbc_hex"),
        "keyword": kw, "time_period": tp, "num_aas": len(sel),
        "scheme": "OSBE (Li, Du, Boneh 2003)",
        "msg": "服务已加密并存入数据库 DB",
    })


@bp.route("/acc_req", methods=["POST"])
def api_acc_req():
    d   = request.json or {}
    uid = d.get("user_id", "Alice")
    kw  = d.get("keyword",     "medical_record")
    tp  = d.get("time_period", "2025-Q1")
    s   = S()
    u   = s.get("users", {}).get(uid)
    if not u or "pu" not in u or "cred" not in u:
        return jsonify({"ok": False, "error": "请先完成注册并生成伪名"}), 400
    sel_aas = s.get("sel_aas", s.get("aas", []))
    aa_pks  = [a["PK_j"] for a in sel_aas]
    perms   = [acc_req(u, u["cred"], u["pu"], aa, aa_pks, kw, tp) for aa in sel_aas]
    u["perms"] = perms
    u["perm_kw"] = kw
    u["perm_tp"] = tp
    return jsonify({
        "ok": True,
        "pypbc_enabled": any(p.get("pypbc_enabled", False) for p in perms),
        "pypbc_used_all": all(p.get("pypbc_used", False) for p in perms),
        "compute_backend": "simulation+pypbc" if all(p.get("pypbc_used", False) for p in perms) else "simulation",
        "permissions": [{
            "aa_id": p["aa_id"],
            "K_j_hex": p["K_j_hex"],
            "formula": p["formula"],
            "pypbc_enabled": p.get("pypbc_enabled", False),
            "pypbc_used": p.get("pypbc_used", False),
            "compute_backend": p.get("compute_backend", "simulation"),
            "proof_verified": p.get("proof_verified"),
            "pypbc_error": p.get("pypbc_error"),
            "K_j_pypbc_hex": p.get("K_j_pypbc_hex"),
            "msg_pypbc_hex": p.get("msg_pypbc_hex"),
            "z_i_pypbc_hex": p.get("z_i_pypbc_hex"),
            "challenge_pypbc_hex": p.get("challenge_pypbc_hex"),
            "formula_pypbc": p.get("formula_pypbc"),
        } for p in perms],
        "msg": f"已从 {len(perms)} 个AA获取访问权限（多签名）",
    })


@bp.route("/acc_agg", methods=["POST"])
def api_acc_agg():
    uid = (request.json or {}).get("user_id", "Alice")
    s = S()
    u = s.get("users", {}).get(uid)
    if not u or "perms" not in u:
        return jsonify({"ok": False, "error": "请先请求访问权限"}), 400
    agg = access_agg(u["perms"])
    u["agg"] = agg
    return jsonify({
        "ok": True,
        "AK_U_hex": agg["AK_U_hex"],
        "num_permissions": agg["num_permissions"],
        "formula": agg["formula"],
        "storage_saving": f"{agg['num_permissions']} 个签名 → 1 个聚合密钥",
        "msg": "访问权限聚合为单一 AK_U，大幅节省存储空间",
    })


@bp.route("/dec", methods=["POST"])
def api_dec():
    d   = request.json or {}
    uid = d.get("user_id", "Alice")
    kw  = d.get("keyword",     "medical_record")
    tp  = d.get("time_period", "2025-Q1")
    s   = S()
    u   = s.get("users", {}).get(uid)
    ct  = s.get("ct")
    if not u or "agg" not in u or not ct:
        return jsonify({"ok": False, "error": "缺少聚合密钥或密文"}), 400
    aa_pks = [a["PK_j"] for a in s.get("sel_aas", s.get("aas", []))]
    result = dec(ct, u["agg"], u.get("pu", {}), aa_pks, kw, tp)
    return jsonify({"ok": True, **result})


@bp.route("/trace", methods=["POST"])
def api_trace():
    uid = (request.json or {}).get("user_id", "Alice")
    s   = S()
    u   = s.get("users", {}).get(uid)
    ta  = s.get("ta")
    if not u or "pu" not in u or not ta:
        return jsonify({"ok": False, "error": "缺少伪名或TA"}), 400
    r = trace(u["pu"], ta)
    match = r["recovered_PK_U"]["e"] == u["PK_U"]["e"]
    return jsonify({
        "ok": True,
        "recovered_PK_U_hex": r["recovered_PK_U_hex"],
        "real_PK_U_hex":      u["PK_U_hex"],
        "identity_revealed":  uid,
        "formula":            r["formula"],
        "pk_match":           match,
        "msg": f"TA 成功从伪名还原用户 {uid} 的真实公钥",
    })


@bp.route("/full_demo", methods=["POST"])
def api_full_demo():
    """Run entire PPDSBAC protocol end-to-end and return all step results."""
    d      = request.json or {}
    n_aas  = int(d.get("n_aas",  3))
    kw     = d.get("keyword",     "medical_record")
    tp     = d.get("time_period", "2025-Q1")
    msg    = d.get("message",     "Patient Record #042 — Confidential")

    steps  = []
    detail = {}

    def step(name, fn):
        t0 = _time.perf_counter()
        r  = fn()
        ms = round((_time.perf_counter() - t0) * 1000, 3)
        steps.append({"step": name, "ms": ms})
        return r

    global_setup()
    steps.append({"step": "Global_Setup", "ms": 0.1})

    ra   = step("Reg_Auth_Setup",   reg_auth_setup)
    ta   = step("Trace_Auth_Setup", trace_auth_setup)
    aas  = step("Auth_Auth_Setup",  lambda: [auth_auth_setup(f"AA{i+1}") for i in range(n_aas)])
    user = step("User_Setup",       lambda: user_setup("DemoUser"))
    cred = step("Regist",           lambda: regist(user, ra))

    aa_pks = [a["PK_j"] for a in aas]
    ct     = step("Enc",            lambda: enc(aa_pks, kw, tp, msg))
    pu     = step("Gen_Pseudonym",  lambda: gen_pseudonym(user, ta))
    perms  = step("Acc_Req",        lambda: [acc_req(user, cred, pu, aa, aa_pks, kw, tp) for aa in aas])
    agg    = step("Acc_Agg",        lambda: access_agg(perms))
    dec_r  = step("Dec",            lambda: dec(ct, agg, pu, aa_pks, kw, tp))
    trc_r  = step("Trace",          lambda: trace(pu, ta))

    return jsonify({
        "ok": True, "steps": steps,
        "summary": {
            "keyword": kw, "time_period": tp, "n_aas": n_aas,
            "decryption_success": dec_r["success"],
            "message_recovered":  dec_r.get("message"),
            "trace_pk_match":     trc_r["recovered_PK_U"]["e"] == user["PK_U"]["e"],
            "sigma_U_hex":        cred["sigma_U_hex"][:34] + "…",
            "AK_U_hex":           to_hex_short(agg["AK_U_hex"]),
        },
    })


def to_hex_short(h: str) -> str:
    return h[:18] + "…" + h[-6:] if len(h) > 24 else h
