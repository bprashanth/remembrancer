# WHY-2: ask twice, get two dashboards (repeatability pilot)

Status: pilot scored (benchmark-2 arm 1) | 2026-07-18 | fully isolated protocol (container,
fresh workdir, web on; test models cannot see our files - see collect_repeat.py)

The question this asset answers: if an NGO worker asks an AI agent the same question about
their place on Monday and again on Wednesday, do they get the same answer?

Files: bank.json (5 questions with the known legitimate sources and their differing values),
collect_repeat.py (the runner), runs/ (60 raw transcripts, never edited), repeat-digest.md
(3 repeats side by side per model-question), RESULTS.md (findings and per-model table).

Question kinds and scoring legend: same as WHY-1 (see ../why1-agents-as-answerers/ASSET.md).
Extra outcome dimensions for this asset: repeats-agree-on-number, repeats-agree-on-basis,
basis-named-in-answer, alternatives-acknowledged.

Headline (draft for the chart): "Same question, same tool, three days: five different
unemployment rates, all cited. Nothing was invented. That is the problem."
