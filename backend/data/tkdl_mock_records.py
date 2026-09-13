"""
TKDL-01 — Hand-curated MOCK TKDL sample dataset.

Per build spec section 19: "Use clearly labelled sample data. The interface
must make it obvious that this is not live TKDL." Every record below sets
is_mock=True (the model default) and none of these record_ids are real TKDL
IDs — they follow TKDL's naming convention purely for demo realism.

WHY THESE SIX RECORDS:
Chosen to give the demo's three ingredient categories (plant / mineral /
animal-processed) and a spread of overlap scenarios against the classifier's
test compositions (backend/logic/classification.py, tests/test_classification.py
both already use "Ashwagandha ..." compositions), so Scenario 1 (classification)
and Scenario 3 (citation/evidence inspection) have a real, demonstrable TKDL
match without any extra setup:

  - TKDL-BP-1025   mineral + plant mix  -> exact-match / Case-1 demo path
  - TKDL-AS-0007   single-herb plant    -> matches the classifier's own
                                            Ashwagandha test fixtures directly
  - TKDL-TR-0014   three-herb plant     -> partial-match / Case-2 demo path
                                            (add one extra ingredient live in-demo)
  - TKDL-CH-0031   complex multi-herb   -> low-overlap / "no strong match" path
                                            for products that share only 1-2
                                            ingredients with a big classical formula
  - TKDL-SR-0042   mineral-heavy        -> shows mineral/metal classification
                                            distinct from plant records
  - TKDL-NP-0058   plant + processed    -> cosmetic-type formulation, shows
                                            "processing" field in a non-fever context

Extend this list by adding another TKDLRecord(...) entry — nothing else needs
to change; logic/tkdl_search.py iterates this list generically.
"""

from backend.models.tkdl import TKDLIngredient, TKDLRecord

TKDL_MOCK_RECORDS: list[TKDLRecord] = [
    TKDLRecord(
        record_id="TKDL-BP-1025",
        formulation_name="Jvaraghna Gutika",
        source_text="Bhaisajya Ratnavali",
        formulation_type="Gutika (tablet/pill)",
        knowledge_known_since_years=500,
        therapeutic_use=["fever", "pyrexia"],
        ingredients=[
            TKDLIngredient(
                name="Mercury",
                traditional_name="Parada",
                source_category="mineral",
                processing="Purified (Shuddha)",
            ),
            TKDLIngredient(
                name="Sulphur",
                traditional_name="Gandhaka",
                source_category="mineral",
                processing="Purified (Shuddha)",
            ),
            TKDLIngredient(
                name="Aloe",
                scientific_name="Aloe barbadensis Mill.",
                traditional_name="Kumari",
                source_category="plant",
                part_used="Leaf (Patra)",
            ),
            TKDLIngredient(
                name="Piper longum",
                scientific_name="Piper longum Linn.",
                traditional_name="Pippali",
                source_category="plant",
                part_used="Fruit (Phala)",
            ),
            TKDLIngredient(
                name="Terminalia chebula",
                scientific_name="Terminalia chebula",
                traditional_name="Haritaki",
                source_category="plant",
                part_used="Fruit (Phala)",
            ),
            TKDLIngredient(
                name="Anacyclus pyrethrum",
                scientific_name="Anacyclus pyrethrum",
                traditional_name="Akarakarabha",
                source_category="plant",
                part_used="Root",
            ),
            TKDLIngredient(
                name="Citrullus colocynthis (fruit)",
                scientific_name="Citrullus colocynthis",
                traditional_name="Indravaruni",
                source_category="plant",
                part_used="Fruit (Phala)",
            ),
            TKDLIngredient(
                name="Citrullus colocynthis (root)",
                scientific_name="Citrullus colocynthis",
                traditional_name="Indravaruni",
                source_category="plant",
                part_used="Root",
            ),
        ],
    ),
    TKDLRecord(
        record_id="TKDL-AS-0007",
        formulation_name="Ashwagandha Churna",
        source_text="Sharangadhara Samhita",
        formulation_type="Churna (powder)",
        knowledge_known_since_years=600,
        therapeutic_use=["general debility", "stress support", "rasayana (rejuvenation)"],
        ingredients=[
            TKDLIngredient(
                name="Ashwagandha",
                scientific_name="Withania somnifera",
                traditional_name="Ashwagandha",
                source_category="plant",
                part_used="Root",
            ),
        ],
    ),
    TKDLRecord(
        record_id="TKDL-TR-0014",
        formulation_name="Triphala Churna",
        source_text="Sushruta Samhita",
        formulation_type="Churna (powder)",
        knowledge_known_since_years=2000,
        therapeutic_use=["digestion", "detoxification", "eye health"],
        ingredients=[
            TKDLIngredient(
                name="Terminalia chebula",
                scientific_name="Terminalia chebula",
                traditional_name="Haritaki",
                source_category="plant",
                part_used="Fruit",
            ),
            TKDLIngredient(
                name="Terminalia bellirica",
                scientific_name="Terminalia bellirica",
                traditional_name="Bibhitaki",
                source_category="plant",
                part_used="Fruit",
            ),
            TKDLIngredient(
                name="Emblica officinalis",
                scientific_name="Phyllanthus emblica",
                traditional_name="Amalaki",
                source_category="plant",
                part_used="Fruit",
            ),
        ],
    ),
    TKDLRecord(
        record_id="TKDL-CH-0031",
        formulation_name="Chyawanprash",
        source_text="Charaka Samhita",
        formulation_type="Avaleha (semi-solid confection)",
        knowledge_known_since_years=1500,
        therapeutic_use=["rasayana (rejuvenation)", "immunity support", "respiratory health"],
        ingredients=[
            TKDLIngredient(
                name="Emblica officinalis",
                scientific_name="Phyllanthus emblica",
                traditional_name="Amalaki",
                source_category="plant",
                part_used="Fruit",
            ),
            TKDLIngredient(
                name="Piper longum",
                scientific_name="Piper longum Linn.",
                traditional_name="Pippali",
                source_category="plant",
                part_used="Fruit",
            ),
            TKDLIngredient(
                name="Cinnamomum",
                scientific_name="Cinnamomum verum",
                traditional_name="Tvak",
                source_category="plant",
                part_used="Bark",
            ),
            TKDLIngredient(
                name="Elettaria cardamomum",
                scientific_name="Elettaria cardamomum",
                traditional_name="Ela",
                source_category="plant",
                part_used="Seed",
            ),
            TKDLIngredient(
                name="Honey",
                traditional_name="Madhu",
                source_category="animal",
            ),
            TKDLIngredient(
                name="Ghee",
                traditional_name="Ghrita",
                source_category="animal",
                processing="Clarified",
            ),
        ],
    ),
    TKDLRecord(
        record_id="TKDL-SR-0042",
        formulation_name="Sutshekhar Rasa",
        source_text="Bhaisajya Ratnavali",
        formulation_type="Rasa (mineral preparation)",
        knowledge_known_since_years=400,
        therapeutic_use=["acidity", "digestive disorders"],
        ingredients=[
            TKDLIngredient(
                name="Mica",
                traditional_name="Abhraka",
                source_category="mineral",
                processing="Incinerated (Bhasma)",
            ),
            TKDLIngredient(
                name="Mercury",
                traditional_name="Parada",
                source_category="mineral",
                processing="Purified (Shuddha)",
            ),
            TKDLIngredient(
                name="Sulphur",
                traditional_name="Gandhaka",
                source_category="mineral",
                processing="Purified (Shuddha)",
            ),
            TKDLIngredient(
                name="Piper nigrum",
                scientific_name="Piper nigrum",
                traditional_name="Maricha",
                source_category="plant",
                part_used="Fruit",
            ),
        ],
    ),
    TKDLRecord(
        record_id="TKDL-NP-0058",
        formulation_name="Nalpamaradi Thailam",
        source_text="Sahasrayogam",
        formulation_type="Thailam (medicated oil)",
        knowledge_known_since_years=700,
        therapeutic_use=["skin conditions", "topical / cosmetic application"],
        ingredients=[
            TKDLIngredient(
                name="Ficus benghalensis",
                scientific_name="Ficus benghalensis",
                traditional_name="Nyagrodha",
                source_category="plant",
                part_used="Bark",
            ),
            TKDLIngredient(
                name="Curcuma longa",
                scientific_name="Curcuma longa",
                traditional_name="Haridra",
                source_category="plant",
                part_used="Rhizome",
            ),
            TKDLIngredient(
                name="Sesame oil",
                scientific_name="Sesamum indicum",
                traditional_name="Tila Taila",
                source_category="plant",
                part_used="Seed (pressed)",
                processing="Cold-pressed oil",
            ),
            TKDLIngredient(
                name="Cow's milk",
                traditional_name="Godugdha",
                source_category="animal",
            ),
        ],
    ),
]

# --- Real TKDL sample records -------------------------------------------
# Extracted from actual saved TKDL portal pages (backend/data/tkdl_real_records.py).
# Still surfaced as mock=True (this remains a static offline dataset, not a live
# TKDL connection) but the underlying formulations/ingredients are authentic
# TKDL records, not synthetic examples — see that file's module docstring.
from backend.data.tkdl_real_records import TKDL_REAL_RECORDS  # noqa: E402

TKDL_MOCK_RECORDS = TKDL_MOCK_RECORDS + TKDL_REAL_RECORDS
