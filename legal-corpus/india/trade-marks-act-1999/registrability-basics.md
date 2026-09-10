---
doc_id: IN-7
jurisdiction: india
legal_regime: trademark_law
document_name: "Trade Marks Act 1999"
document_type: act
section_or_article: "Section 2(1)(zb) (definition of 'trade mark'); Section 18(1) (application for registration)"
product_class_tags: ["all"]
date_enacted: "1999"
last_verified_date: "2026-09-11"
source_url: "https://www.wipo.int/wipolex/en/text/128107"
status_note: null
---

## Section 2(1)(zb) — "trade mark"

"trade mark" means a mark capable of being represented graphically and which is capable of distinguishing the goods or services of one person from those of others and may include shape of goods, their packaging and combination of colours; and —

(i) in relation to Chapter XII (other than section 107), a registered trade mark or a mark used in relation to goods or services for the purpose of indicating or so as to indicate a connection in the course of trade between the goods or services, as the case may be, and some person having the right as proprietor to use the mark; and

(ii) in relation to other provisions of this Act, a mark used or proposed to be used in relation to goods or services for the purpose of indicating or so to indicate a connection in the course of trade between the goods or services, as the case may be, and some person having the right, either as proprietor or by way of permitted user, to use the mark whether with or without any indication of the identity of that person, and includes a certification trade mark or collective mark.

## Section 2(1)(m) — "mark"

"mark" includes a device, brand, heading, label, ticket, name, signature, word, letter, numeral, shape of goods, packaging or combination of colours or any combination thereof.

## Section 18(1) — Application for registration

Any person claiming to be the proprietor of a trade mark used or proposed to be used by him, who is desirous of registering it, shall apply in writing to the Registrar in the prescribed manner for the registration of his trade mark.

## Why this matters for routing (per build spec §5)

This document is what the retriever pulls whenever `objective` includes `trademark`, regardless of the six-category product classification — routing to this doc_id is gated on the *objective the user selected*, not on `classification.category`. It answers "what counts as a mark, and what's the basic filing act" — the disqualifying grounds (why a mark might be refused) sit in `section-9-absolute-grounds.md`, which is the file that actually determines registrability outcomes and should usually be retrieved alongside this one for a "can I trademark this" question.
