from flask import Blueprint, jsonify
from crypto import (
    global_setup, user_setup, trace_auth_setup, auth_auth_setup,
    demo_unlinkability, demo_unforgeability, _PARAMS
)

bp = Blueprint("security", __name__)


@bp.route("/unlinkability", methods=["POST"])
def api_unlink():
    if not _PARAMS:
        global_setup()
    user = user_setup("TestUser")
    ta   = trace_auth_setup()
    r    = demo_unlinkability(user, ta)
    return jsonify({"ok": True, **r})


@bp.route("/unforgeability", methods=["POST"])
def api_unforge():
    if not _PARAMS:
        global_setup()
    aa = auth_auth_setup("AA_test")
    r  = demo_unforgeability(aa, [aa["PK_j"]], "test_kw", "2025-Q1")
    return jsonify({"ok": True, **r})
