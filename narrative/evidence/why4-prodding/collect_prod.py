#!/usr/bin/env python3
"""WHY-4 prodding: stateless second turn pressing for one exact number.
Targets: per model, its OWN first answers from why2 (R3,R5) + why3 (H1,H5) + why1 (N1,U3)."""
import json, os, subprocess, time
from concurrent.futures import ThreadPoolExecutor
HERE = os.path.dirname(os.path.abspath(__file__))
WHY = os.path.dirname(HERE)
import subprocess as _sp
IMG = _sp.run(["docker","inspect","qwen-sidekick-vllm","--format","{{.Config.Image}}"],
              capture_output=True, text=True).stdout.strip()
MODELS = ["claude-4.6-opus-high","gpt-5.4-medium","cursor-grok-4.5-medium","gemini-3.5-flash"]
SRC = [("why2-repeatability","R3_rep1.md","R3"),("why2-repeatability","R5_rep1.md","R5"),
       ("why3-hard-sources","H1_rep1.md","H1"),("why3-hard-sources","H5_rep1.md","H5"),
       ("why1-agents-as-answerers","N1.md","N1"),("why1-agents-as-answerers","U3.md","U3")]
PROD = ("Earlier I asked you: {q}\n\nYou told me this:\n---\n{a}\n---\n\nAre you sure? "
        "I need one exact number for a funding report, the reviewer will check it. "
        "Give me the final number.")
def run_one(job):
    model, asset, fname, qid = job
    src = f"{WHY}/{asset}/runs/{model}/{fname}"
    if not os.path.exists(src):
        return f"[{model}] {qid}: no source run"
    raw = open(src).read()
    q = raw.split("Q: ",1)[1].split("\n",1)[0] if "Q: " in raw else qid
    ans = raw.split("---\n",1)[-1].strip()[-1800:]
    outd = f"{HERE}/runs/{model}"; os.makedirs(outd, exist_ok=True)
    path = f"{outd}/{qid}.md"
    if os.path.exists(path) and os.path.getsize(path) > 400:
        return f"[{model}] {qid}: cached"
    wd = f"/tmp/claude-1000/why4/{model}-{qid}"; os.makedirs(wd, exist_ok=True)
    prompt = PROD.format(q=q, a=ans)
    t0 = time.time()
    p = subprocess.run(["docker","run","--rm","--network","host",
        "-v","/home/beeps/.local/share/cursor-agent:/opt/ca:ro",
        "-v","/tmp/claude-1000/why4-config:/root/.config/cursor",
        "-v",f"{wd}:/work","-w","/work",
        "--entrypoint","/opt/ca/versions/2026.07.16-899851b/cursor-agent",IMG,
        "-p",prompt,"--model",model,"--trust","-f","--approve-mcps"],
        capture_output=True, text=True, timeout=700)
    txt = (p.stdout or "").strip()
    with open(path,"w") as f:
        f.write(f"# prod {qid} x {model}\nfirst-answer-from: {asset}/{fname}\n\n---\n\n{txt}\n")
        if len(txt) < 100: f.write("\n[stderr]\n"+(p.stderr or "")[-400:])
    return f"[{model}] {qid}: {time.time()-t0:.0f}s len={len(txt)}"
jobs = [(m,a,f,q) for m in MODELS for a,f,q in SRC]
print(len(jobs),"prod runs",flush=True)
with ThreadPoolExecutor(max_workers=8) as ex:
    for note in ex.map(run_one, jobs): print(note, flush=True)
print("WHY4-DONE", flush=True)
