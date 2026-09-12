"""
VEC-01 — Vector store setup.

Choice: Chroma, per build spec section 7's explicit "pick Chroma if anyone
wants a simple local dev loop... don't debate this for more than 10 minutes."
Local persistent client, no external service to stand up — good fit for a
hackathon timeline.

Also contains build_where_clause(), which is the actual wiring between
ROUTE-01's output and retrieval: it consumes RoutingResult.regime_filters
directly (the AUTHORITATIVE field ROUTE-01 documents) and produces a Chroma
`where` filter. This is the first place the classify -> route -> retrieve
chain becomes real instead of three modules that only make sense on paper.
"""

from pathlib import Path
from typing import Optional

import chromadb
from chromadb.api.models.Collection import Collection

from backend.logic.routing import RoutingResult
from backend.rag.chunking import Chunk

DEFAULT_COLLECTION_NAME = "legal_corpus"


def get_client(persist_directory: str = "./chroma_data") -> chromadb.ClientAPI:
    """Local persistent client — data survives between runs, no server to manage."""
    return chromadb.PersistentClient(path=persist_directory)


def get_or_create_collection(client: chromadb.ClientAPI, name: str = DEFAULT_COLLECTION_NAME) -> Collection:
    # No custom embedding function passed -> Chroma uses its bundled default
    # embedding model. Per spec section 7 ("pick one and don't swap mid-build"):
    # this IS that pick. If the team later wants a different embedding model,
    # change it here only, and re-run ingestion (embeddings aren't portable
    # across different embedding functions).
    return client.get_or_create_collection(name=name)


def _chunk_to_chroma_metadata(chunk: Chunk) -> dict:
    """Chroma metadata values must be str/int/float/bool — no lists. Tags get
    joined into a comma-separated string; split back out with a plain .split(',')
    on read if you ever need the list form again."""
    return {
        "doc_id": chunk.doc_id or "",
        "jurisdiction": chunk.jurisdiction or "",
        "legal_regime": chunk.legal_regime or "",
        "document_type": chunk.document_type or "",
        "section_or_article": chunk.section_or_article or "",
        "product_class_tags_csv": ",".join(chunk.product_class_tags),
        "metadata_source": chunk.metadata_source,
        "status_note": chunk.status_note or "",
        # RAG-03 needs this to build citable RetrievedChunkRef objects — without
        # it, every retrieved chunk would come back with source_url=None and
        # nothing downstream (CITE, the UI) could link back to the actual law.
        "source_url": chunk.source_url or "",
        # Without this, routes/query.py's citation caching always falls back
        # to doc_id ("IN-3") instead of a real name ("Biological Diversity
        # Act 2002") -- a real, user-visible citation quality bug found by
        # inspecting what was actually stored vs. what Chunk/RetrievedChunkRef
        # both already expect to have.
        "document_name": chunk.document_name or "",
    }


def add_chunks(collection: Collection, chunks: list[Chunk]) -> int:
    """Upsert chunks into the collection. Returns count actually inserted
    (chunks with no text are skipped — Chroma rejects empty documents)."""
    usable = [c for c in chunks if c.text.strip()]
    if not usable:
        return 0
    collection.upsert(
        ids=[c.chunk_id for c in usable],
        documents=[c.text for c in usable],
        metadatas=[_chunk_to_chroma_metadata(c) for c in usable],
    )
    return len(usable)


def build_where_clause(routing: RoutingResult) -> Optional[dict]:
    """
    Converts ROUTE-01's RoutingResult into a Chroma `where` filter.

    Always ANDs in jurisdiction. Within that, each matched regime_filter
    becomes an OR branch; a regime_filter with document_types set further
    ANDs a document_type restriction onto just that branch (this is what
    makes Classical/Generic correctly exclude Patents Rules while Proprietary
    includes it, per the ROUTE-01 v2 fix — see routing.py's module docstring).

    Returns None if there's nothing to filter on (caller should fall back to
    unfiltered jurisdiction-only retrieval per build spec section 5).
    """
    if not routing.regime_filters:
        return {"jurisdiction": routing.jurisdiction} if routing.jurisdiction else None

    regime_clauses = []
    for f in routing.regime_filters:
        if f.document_types:
            regime_clauses.append({
                "$and": [
                    {"legal_regime": f.legal_regime},
                    {"document_type": {"$in": f.document_types}},
                ]
            })
        else:
            regime_clauses.append({"legal_regime": f.legal_regime})

    regime_clause = regime_clauses[0] if len(regime_clauses) == 1 else {"$or": regime_clauses}

    return {"$and": [{"jurisdiction": routing.jurisdiction}, regime_clause]}


def query(collection: Collection, query_text: str, where: Optional[dict] = None, top_k: int = 5) -> dict:
    kwargs = {"query_texts": [query_text], "n_results": top_k}
    if where:
        kwargs["where"] = where
    return collection.query(**kwargs)


def ingest_directory(corpus_root: Path, persist_directory: str = "./chroma_data",
                      collection_name: str = DEFAULT_COLLECTION_NAME) -> int:
    """Convenience wrapper: chunk a directory tree and load it straight into Chroma.
    Returns the number of chunks actually inserted."""
    from backend.rag.chunking import load_chunks_from_directory

    chunks = load_chunks_from_directory(corpus_root)
    client = get_client(persist_directory)
    collection = get_or_create_collection(client, collection_name)
    return add_chunks(collection, chunks)