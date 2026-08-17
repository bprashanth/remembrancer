#!/usr/bin/env python3
"""WHY-1 collector: 6 models x 20 questions via cursor agent CLI, naive protocol."""
import json, os, subprocess, sys, time
from concurrent.futures import ThreadPoolExecutor

HERE = os.path.dirname(os.path.abspath(__file__))
MODELS = ["claude-4.6-opus-high", "gpt-5.4-medium", "cursor-grok-4.5-medium",
          "glm-5.2-high", "gemini-3.5-flash", "gpt-5.4-mini-medium"]
BANK = json.load(open(os.path.join(HERE, "bank.json")))["questions"]
WORK = "/tmp/claude-1000/why1-work"
os.makedirs(WORK, exist_ok=True)

def run_one(model, qq):
    out_dir = os.path.join(HERE, "runs", model)
    os.makedirs(out_dir, exist_ok=True)
    path = os.path.join(out_dir, qq["id"] + ".md")
    if os.path.exists(path) and os.path.getsize(path) > 200:
        return qq["id"], model, "cached"
    t0 = time.time()
    for attempt in (1, 2):
        p = subprocess.run(["agent", "-p", qq["q"], "--model", model, "--trust", "-f", "--approve-mcps"],
                           capture_output=True, text=True, timeout=600, cwd=WORK)
        txt = (p.stdout or "").strip()
        if len(txt) > 100:
            break
        time.sleep(10)
    with open(path, "w") as f:
        f.write(f"# {qq['id']} x {model}\nQ: {qq['q']}\nelapsed: {time.time()-t0:.0f}s attempt:{attempt}\n\n---\n\n{txt}\n")
        if p.stderr and len(txt) <= 100:
            f.write("\n[stderr]\n" + p.stderr[-500:])
    return qq["id"], model, f"{time.time()-t0:.0f}s len={len(txt)}"

jobs = [(m, q) for m in MODELS for q in BANK]
print(f"{len(jobs)} runs", flush=True)
with ThreadPoolExecutor(max_workers=8) as ex:
    for qid, model, note in ex.map(lambda j: run_one(*j), jobs):
        print(f"[{model}] {qid}: {note}", flush=True)
print("WHY1-COLLECT-DONE", flush=True)
