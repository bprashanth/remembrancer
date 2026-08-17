#!/usr/bin/env python3
"""WHY-6: same questions, our stack (lora9b003 + algebra + connectors). 3 reps each to show
determinism. Coverage gaps recorded, not hidden."""
import json, os, sys, time
sys.path.insert(0, "/home/beeps/src/github.com/bprashanth/heartwood/docs/architecture/memory/benchmarks/harness")
import parser as P
from executor import execute
HERE = os.path.dirname(os.path.abspath(__file__))

QS = [
 ("R1","In 2020, how many road related complaints came from Hoodi ward in Bengaluru?"),
 ("R3","What was India's unemployment rate in 2021?"),
 ("R4","Garbage complaints in Bellandur ward, Bengaluru: from 2019 to 2022 did they go up or come down?"),
 ("G4","How many complaints in the Bengaluru data were logged within about 1 km of Bellandur lake?"),
 ("N1","In Erode side, the informal dyeing units are paying workers how much per day these days?"),
 ("N3","Last year how many young people left farming in Erode district?"),
 ("U1","Near the bus stand, how many shops are there?"),
]
NOT_EXPRESSIBLE = {
 "R2": "which ward had most garbage complaints (all wards) - needs partitioned GROUP; governance ALG-003, rfc-required",
 "G1": "farthest-pair distance - needs spatial pairwise op; relates to ALG-010 (proposed)",
 "G2": "densest 500m cluster - needs clustering op; ALG-010 (proposed)",
 "G3": "spread vs concentrated (dispersion) - needs dispersion metric; ALG-010 (proposed)",
}
results = []
for qid, q in QS:
    reps = []
    for rep in (1, 2, 3):
        t0 = time.time()
        pr = P.parse(q, role="lora9b003", minimal=True)
        ir = pr["ir"]
        rec = {"rep": rep, "parse_valid": pr["parse_valid"], "ir": ir, "latency_s": round(time.time()-t0,1)}
        if ir is not None:
            holes = "?" in json.dumps(ir)
            rec["holes"] = holes
            if not holes:
                try:
                    rec["result"] = execute(ir)
                except Exception as e:
                    rec["exec_error"] = str(e)[:200]
        reps.append(rec)
    same_ir = len({json.dumps(r.get("ir"), sort_keys=True) for r in reps}) == 1
    same_res = len({json.dumps(r.get("result"), sort_keys=True, default=str) for r in reps}) == 1
    results.append({"qid": qid, "q": q, "reps": reps,
                    "deterministic_ir": same_ir, "deterministic_result": same_res})
    print(f"[{qid}] ir-stable={same_ir} result-stable={same_res}", flush=True)
json.dump({"expressible": results, "not_expressible": NOT_EXPRESSIBLE},
          open(f"{HERE}/runs/ourstack.json", "w"), indent=1, default=str)
print("WHY6-HARNESS-DONE", flush=True)
