#!/usr/bin/env python3
"""Reverse-generate a paperroast paper template from an ODK/Kobo/SurveyCTO
XLSForm — the BRIEF's data source (b).

Mapping:
  settings.form_title            -> template title
  top-level text/integer/decimal/date/select_one questions -> header fields
  the FIRST `begin repeat` group -> the table:
      each inner question -> a column (serial column prepended)
      select_one <list>   -> choice column, domain = the choices sheet's
                             `name` codes for that list (the short codes an
                             enumerator would write), legend from labels
  repeat_count            -> row count when it is a literal number

Skipped: meta/device/calculate/note/geopoint/audio/image rows, groups other
than the repeat.

Usage:
  .venv/bin/python3 eval/xlsform_import.py <form.xlsx> [--rows 15] [--render]
"""
import argparse
import json
import re
import sys
from pathlib import Path

import openpyxl

sys.path.insert(0, str(Path(__file__).parent.parent))

META = {"start", "end", "deviceid", "phonenumber", "subscriberid", "simserial",
        "caseid", "today", "username", "email", "audit", "calculate",
        "calculate_here", "note", "image", "audio", "video", "file",
        "geopoint", "geotrace", "geoshape", "barcode", "hidden",
        "begin group", "end group", "begin_group", "end_group", "rank"}

TYPE_MAP = {"text": "text", "integer": "int", "decimal": "dec",
            "date": "date", "datetime": "date", "time": "text"}


def _clean_label(s):
    s = re.sub(r"<[^>]+>", "", str(s or "")).strip()
    s = re.sub(r"\$\{[^}]+\}", "", s).strip(" :?")
    return s[:40]


def _sheet_dicts(ws):
    rows = list(ws.iter_rows(values_only=True))
    if not rows:
        return []
    hdr = [str(h).strip().lower() if h else "" for h in rows[0]]
    out = []
    for r in rows[1:]:
        d = {hdr[i]: r[i] for i in range(min(len(hdr), len(r))) if hdr[i]}
        if any(v is not None and str(v).strip() for v in d.values()):
            out.append(d)
    return out


def import_xlsform(path: Path, rows_default=15) -> dict:
    wb = openpyxl.load_workbook(str(path), data_only=True)
    survey = _sheet_dicts(wb["survey"])
    choices = _sheet_dicts(wb["choices"]) if "choices" in wb.sheetnames else []
    settings = _sheet_dicts(wb["settings"]) if "settings" in wb.sheetnames else []

    lists = {}
    for c in choices:
        ln = str(c.get("list_name") or c.get("list name") or "").strip()
        if not ln:
            continue
        # ODK/Kobo use `name`; SurveyCTO exports use `value`
        nm = c.get("name") if c.get("name") is not None else c.get("value")
        nm = str(nm).strip() if nm is not None else ""
        lab = _clean_label(c.get("label") or c.get("label::english") or nm)
        if nm:
            lists.setdefault(ln, []).append((nm, lab))

    def paperize(entries):
        """Long word codes don't fit a paper cell; real registers print
        single-letter codes with a legend. Abbreviate when unambiguous."""
        codes = [nm for nm, _ in entries]
        if codes and all(len(c) > 3 for c in codes):
            initials = [c[0].upper() for c in codes]
            if len(set(initials)) == len(initials):
                return [(i, lab or nm) for i, (nm, lab)
                        in zip(initials, entries)]
        return entries

    title = None
    if settings:
        title = settings[0].get("form_title") or settings[0].get("form_id")
    title = _clean_label(title) or path.stem.replace("_", " ").title()

    def q_to_field(q, for_table):
        t = str(q.get("type") or "").strip()
        base = t.split()[0].lower()
        label = _clean_label(q.get("label") or q.get("label::english")
                             or q.get("name"))
        if not label or base in META or t.lower() in META:
            return None
        if base in ("select_one", "select one"):
            ln = t.split()[-1].strip()
            entries = paperize(lists.get(ln, [])[:8])
            dom = [nm for nm, _ in entries]
            if not dom:
                return None
            legend = ", ".join(f"{nm}={lab}" for nm, lab in entries
                               if lab and lab.lower() != nm.lower())
            f = {"label": label, "type": "choice", "domain": dom}
            if legend and max(len(d) for d in dom) <= 4:
                f["legend"] = legend
            # yes/no lists become yn columns
            if {d.lower() for d in dom} <= {"y", "n", "yes", "no", "0", "1"}:
                f = {"label": label, "type": "yn"}
            return f
        if base in ("select_multiple", "select multiple"):
            return {"label": label, "type": "text"}
        if base in TYPE_MAP:
            f = {"label": label, "type": TYPE_MAP[base]}
            if for_table and TYPE_MAP[base] == "text" and \
                    re.search(r"\bname\b", label.lower()):
                f["type"] = "name"
            return f
        return None

    header_fields, columns, rows = [], [], rows_default
    in_repeat = done_repeat = False
    for q in survey:
        t = str(q.get("type") or "").strip().lower()
        if t.replace("_", " ") == "begin repeat" and not done_repeat:
            in_repeat = True
            rc = q.get("repeat_count")
            try:
                rows = int(str(rc).strip())
                rows = max(4, min(30, rows))
            except (TypeError, ValueError):
                pass
            continue
        if t.replace("_", " ") == "end repeat" and in_repeat:
            in_repeat = False
            done_repeat = True
            continue
        f = q_to_field(q, in_repeat)
        if not f:
            continue
        if in_repeat:
            columns.append(f)
        elif not done_repeat and len(header_fields) < 6 and \
                f["type"] in ("text", "date", "int", "name"):
            header_fields.append({"label": f["label"], "type":
                                  "name" if "name" in f["label"].lower()
                                  else f["type"]})
    if not columns:
        raise SystemExit("no repeat group found — nothing table-shaped to lay out")
    columns.insert(0, {"label": "S.No", "type": "serial"})
    spec = {"title": title, "rows": rows,
            "orientation": "landscape" if len(columns) > 7 else "portrait",
            "header_fields": header_fields, "columns": columns}
    return spec


def analyze(path: Path) -> dict:
    """Flattenability census for one XLSForm — features + verdict + reasons.

    Verdicts:
      register        — one repeat group with 2-12 paper-mappable columns:
                        imports as-is into the current builder
      multi_region    — several sibling repeats: needs the multi-subtable
                        descriptor (each region gets its own fiducials)
      register_wide   — a repeat with >12 mappable columns: needs column
                        splitting across pages
      card            — no repeat but >=4 scalar questions: needs a
                        card-style (label:value per respondent) layout
      not_flattenable — nested repeats, media/geo-centric, or too little
                        paper-mappable content
    """
    out = {"file": path.name, "error": None}
    try:
        wb = openpyxl.load_workbook(str(path), data_only=True)
    except Exception as e:  # noqa: BLE001
        return {**out, "error": f"unreadable: {type(e).__name__}",
                "verdict": "not_xlsform"}
    if "survey" not in wb.sheetnames:
        return {**out, "verdict": "not_xlsform", "error": "no survey sheet"}
    survey = _sheet_dicts(wb["survey"])
    hdrs = set().union(*(set(d) for d in survey)) if survey else set()
    feats = {
        "questions": 0, "repeats": 0, "max_repeat_depth": 0,
        "repeat_cols": [], "select_one": 0, "select_multiple": 0,
        "media_geo": 0, "skip_logic": sum(1 for q in survey
                                          if str(q.get("relevant") or "").strip()),
        "constraints": sum(1 for q in survey
                           if str(q.get("constraint") or "").strip()),
        "cascading": sum(1 for q in survey
                         if str(q.get("choice_filter") or "").strip()),
        "languages": sum(1 for h in hdrs
                         if str(h).startswith("label::")),
    }
    depth = 0
    cur_cols = 0
    for q in survey:
        t = str(q.get("type") or "").strip().lower().replace("_", " ")
        base = t.split()[0] if t else ""
        if t == "begin repeat":
            feats["repeats"] += 1
            depth += 1
            feats["max_repeat_depth"] = max(feats["max_repeat_depth"], depth)
            cur_cols = 0
            continue
        if t == "end repeat":
            if depth == 1:
                feats["repeat_cols"].append(cur_cols)
            depth = max(0, depth - 1)
            continue
        if base in ("select", "text", "integer", "decimal", "date",
                    "datetime", "time"):
            feats["questions"] += 1
            if depth >= 1:
                cur_cols += 1
            if base == "select":
                if "multiple" in t:
                    feats["select_multiple"] += 1
                else:
                    feats["select_one"] += 1
        if base in ("image", "audio", "video", "geopoint", "geotrace",
                    "geoshape", "file", "barcode"):
            feats["media_geo"] += 1
    out.update(feats)
    reasons = []
    if feats["max_repeat_depth"] >= 2:
        reasons.append("nested repeats")
    if feats["media_geo"] > feats["questions"] / 2:
        reasons.append("media/geo-centric")
    if feats["cascading"]:
        reasons.append(f"{feats['cascading']} cascading selects "
                       f"(domains become context-dependent)")
    n_reg = [c for c in feats["repeat_cols"] if c >= 2]
    if feats["max_repeat_depth"] >= 2 or \
            (feats["media_geo"] > max(2, feats["questions"] / 2)):
        v = "not_flattenable"
    elif len(n_reg) == 1 and n_reg[0] <= 12:
        v = "register"
    elif len(n_reg) > 1:
        v = "multi_region"
        reasons.append(f"{len(n_reg)} sibling repeat groups")
    elif len(n_reg) == 1:
        v = "register_wide"
        reasons.append(f"repeat has {n_reg[0]} columns")
    elif feats["questions"] >= 4:
        v = "card"
        reasons.append("no repeat group — card layout needed")
    else:
        v = "not_flattenable"
        reasons.append("too little paper-mappable content")
    out["verdict"] = v
    out["reasons"] = reasons
    return out


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("xlsx")
    ap.add_argument("--rows", type=int, default=15)
    ap.add_argument("--render", action="store_true")
    ap.add_argument("--classify", action="store_true")
    a = ap.parse_args()
    if a.classify:
        print(json.dumps(analyze(Path(a.xlsx)), indent=2))
        return
    spec = import_xlsform(Path(a.xlsx), a.rows)
    print(json.dumps(spec, indent=2))
    if a.render:
        from core.render import render_from_spec
        t = render_from_spec(spec)
        print(f"\nrendered template {t.form_id} "
              f"-> data/templates/{t.form_id}/blank.pdf")


if __name__ == "__main__":
    main()
