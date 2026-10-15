
import os
import hashlib
from pathlib import Path

from dotenv import load_dotenv
from langchain_core.documents import Document
from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_huggingface import HuggingFaceEmbeddings
from langchain_pinecone import PineconeVectorStore
from langchain_community.document_loaders import TextLoader

from log.logger import (
    log_info,
    log_success,
    log_error,
    log_warning,
    log_header,
)

load_dotenv()

# Configuration

BASE_DIR = Path(__file__).resolve().parent
DATA_DIR = BASE_DIR / "data_sources"

PINECONE_INDEX_NAME = os.getenv("PINECONE_INDEX_NAME")

EMBEDDING_MODEL = "sentence-transformers/all-MiniLM-L6-v2"

CHUNK_SIZE = 1000
CHUNK_OVERLAP = 150


# 1. Loading documents


def load_documents() -> list[Document]:
    """Load all Markdown files recursively from data_sources/."""

    log_header("Loading Markdown Documents")

    if not DATA_DIR.exists():
        log_error(f"Data directory not found: {DATA_DIR}")
        raise FileNotFoundError(f"Missing directory: {DATA_DIR}")

    md_files = sorted(DATA_DIR.rglob("*.md"))

    if not md_files:
        log_warning(f"No Markdown files found in {DATA_DIR}")
        return []

    documents = []

    for file_path in md_files:
        try:
            loader = TextLoader(
                str(file_path),
                encoding="utf-8",
            )

            loaded_docs = loader.load()

            # Preserve the relative path as source metadata.
            relative_path = file_path.relative_to(DATA_DIR).as_posix()

            for document in loaded_docs:
                document.metadata["source"] = relative_path
                documents.append(document)

            log_success(f"Loaded: {relative_path}")

        except Exception as exc:
            log_error(f"Failed to load {file_path}: {exc}")

    log_info(f"Markdown files discovered: {len(md_files)}")
    log_success(f"Documents loaded: {len(documents)}")

    return documents


# 2. Spliting Documents into Chunks

def chunk_documents(
    documents: list[Document],
) -> list[Document]:
    """Split documents into overlapping chunks."""

    log_header("Chunking Documents")

    if not documents:
        log_warning("No documents available for chunking.")
        return []

    text_splitter = RecursiveCharacterTextSplitter(
        chunk_size=CHUNK_SIZE,
        chunk_overlap=CHUNK_OVERLAP,
        add_start_index=True,
        separators=[
            "\n## ",
            "\n### ",
            "\n#### ",
            "\n\n",
            "\n",
            " ",
            "",
        ],
    )

    chunks = text_splitter.split_documents(documents)

    # Remove empty chunks 
    valid_chunks = [
        chunk
        for chunk in chunks
        if chunk.page_content.strip()
    ]

    log_info(f"Chunk size: {CHUNK_SIZE} characters")
    log_info(f"Chunk overlap: {CHUNK_OVERLAP} characters")
    log_success(f"Total chunks created: {len(valid_chunks)}")

    return valid_chunks


# 3. Initialize Embedding Model

def get_embeddings() -> HuggingFaceEmbeddings:
    """Initialize the local Hugging Face embedding model."""

    log_header("Initializing Embedding Model")

    embeddings = HuggingFaceEmbeddings(
        model_name=EMBEDDING_MODEL,
        model_kwargs={"device": "cpu"},
        encode_kwargs={"normalize_embeddings": True},
    )

    log_success(f"Embedding model loaded: {EMBEDDING_MODEL}")

    return embeddings


# 4. Add Chunks to Pinecone


def add_to_vector_db(
    chunks: list[Document],
) -> PineconeVectorStore | None:
    """Embed chunks and upsert them into Pinecone."""

    log_header("Adding Documents to Pinecone")

    if not chunks:
        log_warning("No chunks available to index.")
        return None

    if not PINECONE_INDEX_NAME:
        log_error("PINECONE_INDEX_NAME is missing from .env")
        raise ValueError("PINECONE_INDEX_NAME is required.")

    if not os.getenv("PINECONE_API_KEY"):
        log_error("PINECONE_API_KEY is missing from .env")
        raise ValueError("PINECONE_API_KEY is required.")

    embeddings = get_embeddings()

    vector_store = PineconeVectorStore(
        index_name=PINECONE_INDEX_NAME,
        embedding=embeddings,
    )


    ids = []

    for chunk in chunks:
        source = chunk.metadata.get("source", "unknown")
        start_index = chunk.metadata.get("start_index", 0)

        unique_content = (
            f"{source}:{start_index}:{chunk.page_content}"
        )

        chunk_id = hashlib.sha256(
            unique_content.encode("utf-8")
        ).hexdigest()

        ids.append(chunk_id)

    # PineconeVectorStore uses the embedding model to generate
    # vectors and upserts them into the configured index.
    vector_store.add_documents(
        documents=chunks,
        ids=ids,
    )

    log_success(
        f"Successfully indexed {len(chunks)} chunks "
        f"in Pinecone index '{PINECONE_INDEX_NAME}'."
    )

    return vector_store


# 5. Runing Complete Ingestion Pipeline


def ingest_data() -> PineconeVectorStore | None:
    """Execute loading, chunking, embedding, and indexing."""

    log_header("RAG Data Ingestion Pipeline")

    try:
        documents = load_documents()

        if not documents:
            log_warning("Ingestion stopped: no documents loaded.")
            return None

        chunks = chunk_documents(documents)

        if not chunks:
            log_warning("Ingestion stopped: no valid chunks.")
            return None

        vector_store = add_to_vector_db(chunks)

        log_header("Data Ingestion Completed")
        log_success(f"Documents loaded: {len(documents)}")
        log_success(f"Chunks indexed: {len(chunks)}")

        return vector_store

    except Exception as exc:
        log_error(f"Data ingestion failed: {exc}")
        raise


if __name__ == "__main__":
    ingest_data()
