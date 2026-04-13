from flask import Blueprint, jsonify, request
from crypto import (
    global_setup, reg_auth_setup, auth_auth_setup,
    trace_auth_setup, user_setup, regist, _session
)

bp = Blueprint("setup", __name__)

S = _session   # shorthand


@bp.route("/global", methods=["POST"])
def api_global():
    p = global_setup()
    return jsonify({"ok": True, "params": p, "msg": "双线性群公共参数初始化完成"})


@bp.route("/ra", methods=["POST"])
def api_ra():
    ra = reg_auth_setup()
    return jsonify({"ok": True, "PK_RA_hex": ra["PK_RA_hex"], "msg": "RA 密钥对生成完成"})


@bp.route("/ta", methods=["POST"])
def api_ta():
    ta = trace_auth_setup()
    return jsonify({"ok": True, "PK_TA_hex": ta["PK_TA_hex"], "msg": "TA 密钥对生成完成"})


@bp.route("/aa", methods=["POST"])
def api_aa():
    n = int((request.json or {}).get("n", 3))
    aas = [auth_auth_setup(f"AA{i+1}") for i in range(n)]
    S()["aas"] = aas
    return jsonify({
        "ok": True,
        "aas": [{"aa_id": a["aa_id"], "PK_j_hex": a["PK_j_hex"]} for a in aas],
        "msg": f"{n} 个授权机构密钥对生成完成",
    })


@bp.route("/user", methods=["POST"])
def api_user():
    uid = (request.json or {}).get("user_id", "Alice")
    u = user_setup(uid)
    users = S().setdefault("users", {})
    users[uid] = u
    return jsonify({"ok": True, "user_id": uid, "PK_U_hex": u["PK_U_hex"], "msg": f"用户 {uid} 密钥对生成完成"})


@bp.route("/regist", methods=["POST"])
def api_regist():
    uid = (request.json or {}).get("user_id", "Alice")
    s = S()
    u  = s.get("users", {}).get(uid)
    ra = s.get("ra")
    if not u or not ra:
        return jsonify({"ok": False, "error": "请先完成全局初始化和用户密钥生成"}), 400
    cred = regist(u, ra)
    u["cred"] = cred
    return jsonify({
        "ok": True, "user_id": uid,
        "sigma_U_hex": cred["sigma_U_hex"],
        "zk_verified": cred["zk_verified"],
        "credential_type": cred["credential_type"],
        "msg": f"RA 已向用户 {uid} 颁发匿名凭证 σ_U",
    })


@bp.route("/state", methods=["GET"])
def api_state():
    s = S()
    return jsonify({
        "has_params": bool(s.get("ra")),
        "has_ra":     "ra" in s,
        "has_ta":     "ta" in s,
        "num_aas":    len(s.get("aas", [])),
        "users":      [{"user_id": uid, "has_cred": "cred" in u}
                       for uid, u in s.get("users", {}).items()],
    })
