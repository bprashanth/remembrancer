# Paperroast evidence snapshot

This folder is the local evidence behind the Form data narratives. A reader
should not need another repository just to inspect the benchmark.

Included here:

- `FINDINGS.md` and `FINDINGS_from_formidable.md`: the written findings;
- `core/`: rendering, filling, extraction and scoring code;
- `eval/`: benchmark and XLSForm import code;
- `results/`: checked-in model and cell benchmark outputs;
- `data/cellbench/`: the cell crops and answer manifest used by the cell
  benchmark;
- `data/specs/`: small template and vocabulary inputs;
- `data/xlsforms/harvest/census.json`: the form census behind the 41% and 79%
  coverage claims;
- `tests/`: scorer tests;
- `app/main.py`: the local API, including design-from-sample;
- `LICENSE.source` and `UPSTREAM_README.md`: source licence and original setup
  note.

The 60 MB generated form corpus, model weights, private partner forms and local
runtime outputs are not copied. They are either reproducible, too large for
this evidence cut, or not publishable. The code, small benchmark data, answer
manifests and aggregate results are here so the claims can still be checked.

This is a snapshot. Do not edit it to improve the story. Copy a fresh evidence
cut when the producer changes and record what changed.
