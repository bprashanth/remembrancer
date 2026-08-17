# chronology — the paperroast narrative

Ordered documents for the write-up. ⟨form-idable⟩ markers are hand-off
points for the blind-detection agent to fill from his side.

1. [01-form-landscape.md](01-form-landscape.md) — where real survey forms
   come from, the flattenability census (41% register today, ~79% with two
   layout extensions, 21% blocked — cascading selects being the one
   semantic blocker).
2. [02-form-generation.md](02-form-generation.md) — three paths to a
   template (hand design; model-proposed from a photo, local 8B suffices;
   deterministic import from Kobo/ODK/SurveyCTO XLSForms) and what the
   renderer + synthetic filler add.
3. [03-detection-problems.md](03-detection-problems.md) — why this is
   hard: layout isomorphism, position-blind metrics, page bow and row
   identity, real ink / pencil / OOV vocabulary / ambiguous codes,
   interpretation-not-transcription, honest refusal — plus the blind-side
   dead ends (fingerprinting, print subtraction, tail trimming, coverage
   failure, metric traps). ⟨form-idable⟩ **filled**.
4. [04-models-and-solution.md](04-models-and-solution.md) — the two-bucket
   framing (unknown form → frontier model + harness engineering; known
   layout → regenerate the form and use a small model), measured model
   findings, the twelve solution pieces, and the landing: template + QR +
   OMR dots + LoRA'd small model — plus the measured frontier-model
   ranking and cost for bucket 1, and the LoRA data recipe.
   ⟨form-idable⟩ **filled**.
5. [05-coverage-brainstorm.md](05-coverage-brainstorm.md) — what we can /
   can't handle and candidate solutions (print-time specialisation for
   cascades, linked registers for nested repeats, presence-only signature
   cells, comb boxes for amounts…).
