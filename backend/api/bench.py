from flask import Blueprint, jsonify, request
from crypto import benchmark as _bench

bp = Blueprint("bench", __name__)

PAPER_REF = {
    10: {"Global_Setup":3.8,"Reg_Auth_Setup":0.8,"Auth_Auth_Setup":11.58,
         "Trace_Auth_Setup":0.43,"User_Setup":0.40,"Regist":1.80,
         "Gen_Pseudonym":0.5,"Enc":32.37,"Acc_Req":1369.87,
         "Acc_Agg":0.03,"Dec":33.20,"Trace":0.42},
    20: {"Global_Setup":3.8,"Reg_Auth_Setup":0.8,"Auth_Auth_Setup":22.50,
         "Trace_Auth_Setup":0.43,"User_Setup":0.40,"Regist":1.80,
         "Gen_Pseudonym":0.5,"Enc":38.43,"Acc_Req":2691.11,
         "Acc_Agg":0.05,"Dec":39.36,"Trace":0.42},
    30: {"Global_Setup":3.8,"Reg_Auth_Setup":0.8,"Auth_Auth_Setup":33.23,
         "Trace_Auth_Setup":0.43,"User_Setup":0.40,"Regist":1.80,
         "Gen_Pseudonym":0.5,"Enc":45.67,"Acc_Req":3885.79,
         "Acc_Agg":0.07,"Dec":46.25,"Trace":0.42},
}

# Nasiraee et al. [23] reference data
# Acc_Req: lighter (no ZK proof, no unforgeability), Dec: similar pairing cost
SCHEME23_REF = {
    10: {"Acc_Req":12.5, "Dec":28.1},
    20: {"Acc_Req":25.0, "Dec":56.2},
    30: {"Acc_Req":37.5, "Dec":84.3},
}

@bp.route("/run", methods=["POST"])
def api_bench():
    results = {}
    for n in [10, 20, 30]:
        results[n] = _bench(n)
    return jsonify({
        "ok": True,
        "simulated":    {str(k): v for k, v in results.items()},
        "paper_ref":    {str(k): v for k, v in PAPER_REF.items()},
        "scheme23_ref": {str(k): v for k, v in SCHEME23_REF.items()},
        "note": "参考值来自真实PBC环境（HP i5-8300H，Type-F曲线）；仿真值反映相对计算量",
    })
