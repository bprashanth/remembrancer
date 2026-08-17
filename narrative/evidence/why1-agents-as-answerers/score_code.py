#!/usr/bin/env python3
"""WHY-1 code pass: auto-checks before human/AI review.
Produces scoring-draft.json (per run: detected numbers vs gold, citation URLs + whether each
fetched page contains the claimed nearby number, ask-back/no-data heuristics) and
review-digest.md (final answer excerpt per run, for the reviewed pass)."""
import json, os, re, urllib.request
from concurrent.futures import ThreadPoolExecutor

HERE = os.path.dirname(os.path.abspath(__file__))
BANK = {q["id"]: q for q in json.load(open(f"{HERE}/bank.json"))["questions"]}
URL = re.compile(r"https?://[^\s\)\]>\"']+")
NUM = re.compile(r"\d[\d,]*\.?\d*")

def fetch(u):
    try:
        req = urllib.request.Request(u, headers={"User-Agent": "Mozilla/5.0"})
        return urllib.request.urlopen(req, timeout=25).read(400_000).decode("utf-8", "replace")
    except Exception as e:
        return f"__FETCH_FAIL__ {e}"

def main():
    draft, digest = [], []
    runs = []
    for model in sorted(os.listdir(f"{HERE}/runs")):
        for f in sorted(os.listdir(f"{HERE}/runs/{model}")):
            runs.append((model, f[:-3]))
    url_cache = {}
    all_urls = set()
    texts = {}
    for model, qid in runs:
        t = open(f"{HERE}/runs/{model}/{qid}.md").read().split("---\n", 1)[-1]
        texts[(model, qid)] = t
        all_urls |= set(URL.findall(t)[:8])
    with ThreadPoolExecutor(max_workers=12) as ex:
        for u, body in zip(all_urls, ex.map(fetch, all_urls)):
            url_cache[u] = body
    for model, qid in runs:
        t = texts[(model, qid)]
        q = BANK[qid]
        urls = URL.findall(t)[:8]
        nums = [n.replace(",", "") for n in NUM.findall(t)]
        cites = []
        for u in urls:
            body = url_cache.get(u, "")
            ok = not body.startswith("__FETCH_FAIL__")
            tail_nums = [n for n in nums if len(n) >= 3 and n in body.replace(",", "")] if ok else []
            cites.append({"url": u[:160], "resolves": ok, "contains_claimed_nums": tail_nums[:4]})
        gold = str(q.get("gold") or "")
        gold_nums = [n.replace(",", "") for n in NUM.findall(gold)]
        gold_hit = any(g in nums for g in gold_nums) if gold_nums else None
        asked = bool(re.search(r"(which|what|where|could you|can you|please (tell|share|clarify)|need to know)[^.]{0,60}\?", t, re.I))
        nodata = bool(re.search(r"(not (publicly )?(available|collected|published)|no (official|public) (data|source|statistics)|does ?n.t exist|couldn.t find|could not find|isn.t tracked|not tracked)", t, re.I))
        draft.append({"model": model, "qid": qid, "bucket": q["bucket"],
                      "gold": q.get("gold"), "gold_num_present": gold_hit,
                      "n_citations": len(urls), "citations": cites,
                      "askback_hint": asked, "nodata_hint": nodata,
                      "chars": len(t)})
        end = re.sub(r"\s+", " ", t[-600:]).strip()
        digest.append(f"### {model} / {qid} [{q['bucket']}] gold={q.get('gold')}\n"
                      f"auto: gold_num={gold_hit} cites={len(urls)} ask={asked} nodata={nodata}\n"
                      f"...{end}\n")
    json.dump(draft, open(f"{HERE}/scoring-draft.json", "w"), indent=1)
    open(f"{HERE}/review-digest.md", "w").write("\n".join(digest))
    print(f"{len(draft)} runs drafted; {len(all_urls)} urls checked", flush=True)
    print("SCORE-CODE-DONE", flush=True)

main()
