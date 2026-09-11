# legal-corpus dedup pass — 2026-09-11, round 3

This round is cleanup only — no new legal content. Two teammates independently built the same two
docs in parallel with different folder names, and there were two leftover empty placeholder folders
from a failed scaffold. All fixed. Everything else from the spec §6 minimum viable set was already
in place.

## Removed (duplicates / garbage)

- `india/drugs-cosmetics-act/` — older, thinner duplicate of `india/drugs-and-cosmetics-act/`
  (same `doc_id: IN-5`). The surviving version is more thorough: it includes the Rule 158B licensing
  distinction and correctly flags that the spec's "2016 Rule amendment" is actually the 2015 Eighth
  Amendment Rules (G.S.R. 918(E)) — a real catch, kept it.
- `international/trips/` — older, thinner duplicate of `international/trips-agreement/`, and the two
  copies even disagreed on `doc_id` (`INTL-1` vs `INT-1`). Kept `trips-agreement/`, corrected its
  `doc_id` to the corpus-standard `INTL-1`.
- `international/{trips,cbd,nagoya-protocol,wipo-gratk,pct}/` — a literal directory with that exact
  name, empty. Leftover from a shell that didn't expand `{a,b,c}` brace syntax. Deleted.
- `international/wipo-gratk-treaty/` — empty, never populated. A second attempt at the GRATK folder
  that duplicated the already-complete `international/wipo-gratk/`. Deleted.

## Fixed (gaps, not duplicates)

- `india/trade-marks-act-1999/meta.json` — was missing an entry for `registrability-basics.md`
  (a real, non-duplicate file covering the "trade mark" definition and §18 filing basics that someone
  added but never wired into the metadata). Added.
- `india/fssai-ayurveda-aahar/` — both files' `status_note` were `null`; the only pair in the whole
  corpus without one. Added a note for consistency with everything else.

## Rebuilt

- `manifest.json` — now 22 chunks across exactly 12 documents, zero duplicate (doc_id, section) pairs,
  zero doc_id collisions. Validated programmatically before packaging.
- `corpus_validation.csv` — one row per document, all now marked done, dedup history noted in the
  `notes` column for the two docs that needed it.
- `README.md` — documents the dedup itself, so nobody re-adds either removed folder by accident.

## Validation run before packaging (all clean)

- Every `.json` file parses.
- Zero empty files, zero empty directories.
- Every `.md` file (except README) has a YAML frontmatter block.
- `manifest.json` and `corpus_validation.csv` agree on the exact same 12 `doc_id`s.
- No two entries in `manifest.json` share the same `(doc_id, section_or_article)` pair.

## Still open (unchanged from before)

1. Nobody with legal training has reviewed any of this corpus yet.
2. WIPO GRATK ratification count (4/15 last checked) needs re-verification close to demo day.
3. If anyone adds a new doc going forward: check `manifest.json` for the doc_id and folder name
   *first* — this whole dedup pass only happened because two people didn't know the other had started
   the same doc.
