#!/usr/bin/env python3
import json, os, subprocess, time
from concurrent.futures import ThreadPoolExecutor
HERE = os.path.dirname(os.path.abspath(__file__))
MODELS = ["claude-4.6-opus-high", "gpt-5.4-medium", "cursor-grok-4.5-medium", "gemini-3.5-flash"]
import subprocess as _sp
IMG = _sp.run(["docker","inspect","qwen-sidekick-vllm","--format","{{.Config.Image}}"],
              capture_output=True, text=True).stdout.strip()
_b = json.load(open(f"{HERE}/bank.json"))
BANK = _b["questions"] if isinstance(_b, dict) else _b
def run_one(job):
    model, qq, rep = job
    out = f"{HERE}/runs/{model}"
    os.makedirs(out, exist_ok=True)
    path = f"{out}/{qq['id']}_rep{rep}.md"
    if os.path.exists(path) and os.path.getsize(path) > 400:
        return f"[{model}] {qq['id']}r{rep}: cached"
    wd = f"/tmp/claude-1000/why5/{model}-{qq['id']}-r{rep}"
    os.makedirs(wd, exist_ok=True)  # FRESH dir per run: contamination fix
    t0 = time.time()
    # CONTAINER ISOLATION (2026-07-18): test models must not reach the host filesystem where
    # gold answers, packs and our benchmark docs live. Proven: host paths invisible inside.
    try:
        p = subprocess.run(["docker", "run", "--rm", "--network", "host",
        "-v", "/home/beeps/.local/share/cursor-agent:/opt/ca:ro",
        "-v", "/tmp/claude-1000/why5-config:/root/.config/cursor",
        "-v", f"{wd}:/work", "-w", "/work",
        "--entrypoint", "/opt/ca/versions/2026.07.16-899851b/cursor-agent", IMG,
        "-p", qq["q"], "--model", model, "--trust", "-f", "--approve-mcps"],
        capture_output=True, text=True, timeout=900)
    except subprocess.TimeoutExpired:
        open(path, "w").write(f"# {qq['id']} rep{rep} x {model}\nQ: {qq['q']}\n\n---\n\n[TIMEOUT after 900s]\n")
        return f"[{model}] {qq['id']}r{rep}: TIMEOUT"
    txt = (p.stdout or "").strip()
    with open(path, "w") as f:
        f.write(f"# {qq['id']} rep{rep} x {model}\nQ: {qq['q']}\nelapsed:{time.time()-t0:.0f}s\n\n---\n\n{txt}\n")
        if len(txt) < 100:
            f.write("\n[stderr]\n" + (p.stderr or "")[-400:])
    return f"[{model}] {qq['id']}r{rep}: {time.time()-t0:.0f}s len={len(txt)}"
jobs = [(m, q, r) for m in MODELS for q in BANK for r in (1,)]
print(len(jobs), "runs", flush=True)
with ThreadPoolExecutor(max_workers=8) as ex:
    for note in ex.map(run_one, jobs):
        print(note, flush=True)
print("WHY5-DONE", flush=True)
