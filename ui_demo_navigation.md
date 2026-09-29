# UI demo navigation (current frontend)

| Demo task | Where to go | Current behavior and limits |
|---|---|---|
| Enter product | Start a case → choose jurisdiction → Product Intake Questionnaire. | Name, target, composition, intended use, classical basis, novelty, ingredient source, known origin, development status, and objectives are collected. Some fields appear progressively based on target. |
| View classification | Submit intake → Classification screen. | Displays the deterministic classification result. The main case flow then proceeds to the workspace. |
| View ABS | Workspace → **ABS Helper** tab. | Calls `POST /abs/assess`. The screen shows relevance, reasoning, selected authority guidance, IPR note, and disclaimer. It does not render all detailed forms, benefit-sharing, missing-information, citation, or human-escalation fields. |
| View TKDL | Workspace → **TKDL Match** tab. | Calls `POST /tkdl/search` against the offline archive. UI banner states it is not connected to live TKDL. |
| Ask legal question | Workspace → **Ask & Explore** tab. | Calls `POST /query`. Results depend on the corpus index, retrieval, and LLM credentials. |
| Open legal citation | Click a citation chip in an answer. | Opens citation detail with cached source/excerpt and overlap-based verified flag. This is not a legal correctness certification. |
| Inspect evidence/confidence | Ask & Explore answer card/confidence panel. | Displays RAG confidence and citation-oriented details. ABS/TKDL evidence is not shown in that unified panel. |
| See uncertainty/abstention | Query answer card or intake/classification state. | The RAG answer card displays abstention reason/notes. ABS structured missing facts and conflict state are not fully presented in the ABS UI. |
| See conflict | No dedicated conflict-resolution screen found. | A cross-source conflict flow is unverified and not currently editable through the frontend's ABS request. |
| See human escalation | Generic escalation UI component exists, but structured ABS escalation is not rendered in `ABSHelper`. | Use backend response/test evidence only; do not present the current screen as showing the full escalation case. |
| Export/share | No export or share control/API found. | Not implemented in the inspected frontend/API. |

The workspace tabs run separate requests. Do not describe the current UI as one integrated one-click assessment.
