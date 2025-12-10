import os
from typing import List, Dict
from pathlib import Path
import chromadb
from chromadb.config import Settings
from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain_community.embeddings import HuggingFaceEmbeddings
from app.core.config import settings


class KnowledgeBase:
    """Knowledge base using ChromaDB for vector search."""

    def __init__(self):
        self.client = chromadb.Client(
            Settings(
                persist_directory=settings.CHROMA_PERSIST_DIRECTORY,
                anonymized_telemetry=False,
            )
        )
        self.collection_name = "support_knowledge"
        self.embeddings = HuggingFaceEmbeddings(
            model_name=settings.EMBEDDING_MODEL,
            model_kwargs={"device": "cpu"},
        )

        # Get or create collection
        try:
            self.collection = self.client.get_collection(self.collection_name)
        except Exception:
            self.collection = self.client.create_collection(
                name=self.collection_name,
                metadata={"hnsw:space": "cosine"},
            )

    def load_documents(self, directory: str):
        """Load documents from directory into the knowledge base."""
        kb_path = Path(directory)
        if not kb_path.exists():
            print(f"Knowledge base directory {directory} does not exist")
            return

        text_splitter = RecursiveCharacterTextSplitter(
            chunk_size=500, chunk_overlap=50, length_function=len
        )

        documents = []
        metadatas = []
        ids = []

        for idx, file_path in enumerate(kb_path.glob("**/*.md")):
            with open(file_path, "r", encoding="utf-8") as f:
                content = f.read()

            chunks = text_splitter.split_text(content)

            for chunk_idx, chunk in enumerate(chunks):
                documents.append(chunk)
                metadatas.append(
                    {
                        "source": str(file_path.name),
                        "chunk": chunk_idx,
                        "full_path": str(file_path),
                    }
                )
                ids.append(f"{file_path.stem}_{idx}_{chunk_idx}")

        if documents:
            # Generate embeddings
            embeddings = self.embeddings.embed_documents(documents)

            # Add to collection
            self.collection.add(
                documents=documents, embeddings=embeddings, metadatas=metadatas, ids=ids
            )
            print(f"Loaded {len(documents)} chunks from {directory}")

    def search(self, query: str, n_results: int = 3) -> List[Dict[str, str]]:
        """Search knowledge base for relevant documents."""
        query_embedding = self.embeddings.embed_query(query)

        results = self.collection.query(
            query_embeddings=[query_embedding], n_results=n_results, include=["documents", "metadatas", "distances"]
        )

        articles = []
        if results["documents"] and len(results["documents"][0]) > 0:
            for doc, metadata, distance in zip(
                results["documents"][0], results["metadatas"][0], results["distances"][0]
            ):
                articles.append(
                    {
                        "content": doc,
                        "source": metadata.get("source", "Unknown"),
                        "relevance_score": 1 - distance,  # Convert distance to similarity
                    }
                )

        return articles

    def reset(self):
        """Clear the knowledge base."""
        try:
            self.client.delete_collection(self.collection_name)
            self.collection = self.client.create_collection(
                name=self.collection_name,
                metadata={"hnsw:space": "cosine"},
            )
            print("Knowledge base reset successfully")
        except Exception as e:
            print(f"Error resetting knowledge base: {e}")


# Global instance
kb = KnowledgeBase()
