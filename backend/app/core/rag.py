"""
RAG (Retrieval Augmented Generation) Service.

Handles document indexing and retrieval for answering questions
based on uploaded documents.
"""

from typing import Dict, List, Optional, Any
import logging
import os
from pathlib import Path

from app.config import settings
from app.utils.constants import RAG_CONFIG

logger = logging.getLogger(__name__)


class RAGService:
    """
    RAG service for document-based Q&A.
    
    Uses ChromaDB for vector storage and sentence-transformers for embeddings.
    """
    
    def __init__(self):
        self.persist_dir = settings.CHROMA_PERSIST_DIR
        self.embedding_model = settings.EMBEDDING_MODEL
        self.chunk_size = RAG_CONFIG["chunk_size"]
        self.chunk_overlap = RAG_CONFIG["chunk_overlap"]
        self.top_k = RAG_CONFIG["top_k"]
        self.min_relevance_score = RAG_CONFIG["min_relevance_score"]
        
        self._embeddings = None
        self._vectorstore = None
        self._text_splitter = None
        self._initialized = False
    
    async def initialize(self):
        """Initialize the RAG service components."""
        if self._initialized:
            return
        
        try:
            # Create persist directory if not exists
            Path(self.persist_dir).mkdir(parents=True, exist_ok=True)
            
            # Initialize embeddings
            from langchain.embeddings import HuggingFaceEmbeddings
            self._embeddings = HuggingFaceEmbeddings(
                model_name=self.embedding_model,
                model_kwargs={'device': 'cpu'},
                encode_kwargs={'normalize_embeddings': True}
            )
            
            # Initialize text splitter
            from langchain.text_splitter import RecursiveCharacterTextSplitter
            self._text_splitter = RecursiveCharacterTextSplitter(
                chunk_size=self.chunk_size,
                chunk_overlap=self.chunk_overlap,
                length_function=len,
                separators=["\n\n", "\n", " ", ""]
            )
            
            # Initialize or load vector store
            from langchain.vectorstores import Chroma
            self._vectorstore = Chroma(
                persist_directory=self.persist_dir,
                embedding_function=self._embeddings,
                collection_name="documents"
            )
            
            self._initialized = True
            logger.info("✅ RAG service initialized")
            
        except Exception as e:
            logger.error(f"❌ Failed to initialize RAG service: {e}")
            raise
    
    def _ensure_initialized(self):
        """Ensure service is initialized."""
        if not self._initialized:
            import asyncio
            asyncio.get_event_loop().run_until_complete(self.initialize())
    
    async def add_document(
        self,
        file_path: str,
        metadata: Dict[str, Any] = None
    ) -> Dict[str, Any]:
        """
        Process and add a document to the vector store.
        
        Args:
            file_path: Path to the document file
            metadata: Additional metadata for the document
            
        Returns:
            Dictionary with processing results
        """
        await self.initialize()
        
        if not os.path.exists(file_path):
            return {
                "success": False,
                "error": f"File not found: {file_path}",
                "chunks_added": 0
            }
        
        try:
            # Load document based on file type
            ext = file_path.rsplit('.', 1)[-1].lower()
            
            if ext == 'pdf':
                documents = await self._load_pdf(file_path)
            elif ext == 'txt':
                documents = await self._load_text(file_path)
            else:
                return {
                    "success": False,
                    "error": f"Unsupported file type: {ext}",
                    "chunks_added": 0
                }
            
            if not documents:
                return {
                    "success": False,
                    "error": "No content extracted from document",
                    "chunks_added": 0
                }
            
            # Split into chunks
            chunks = self._text_splitter.split_documents(documents)
            
            # Add metadata to chunks
            filename = os.path.basename(file_path)
            for chunk in chunks:
                chunk.metadata["source"] = filename
                chunk.metadata["file_path"] = file_path
                if metadata:
                    chunk.metadata.update(metadata)
            
            # Add to vector store
            self._vectorstore.add_documents(chunks)
            
            # Persist
            self._vectorstore.persist()
            
            logger.info(f"Added document: {filename} ({len(chunks)} chunks)")
            
            return {
                "success": True,
                "filename": filename,
                "chunks_added": len(chunks),
                "message": f"Successfully processed {len(chunks)} chunks"
            }
            
        except Exception as e:
            logger.error(f"Error adding document: {e}")
            return {
                "success": False,
                "error": str(e),
                "chunks_added": 0
            }
    
    async def _load_pdf(self, file_path: str) -> List:
        """Load PDF document."""
        try:
            from langchain.document_loaders import PyPDFLoader
            loader = PyPDFLoader(file_path)
            return loader.load()
        except Exception as e:
            logger.error(f"Error loading PDF: {e}")
            
            # Fallback to pdfplumber
            try:
                import pdfplumber
                from langchain.schema import Document
                
                documents = []
                with pdfplumber.open(file_path) as pdf:
                    for i, page in enumerate(pdf.pages):
                        text = page.extract_text() or ""
                        if text.strip():
                            documents.append(Document(
                                page_content=text,
                                metadata={"page": i + 1}
                            ))
                return documents
            except Exception as e2:
                logger.error(f"Fallback PDF loading failed: {e2}")
                return []
    
    async def _load_text(self, file_path: str) -> List:
        """Load text document."""
        try:
            from langchain.document_loaders import TextLoader
            loader = TextLoader(file_path, encoding='utf-8')
            return loader.load()
        except Exception as e:
            logger.error(f"Error loading text file: {e}")
            return []
    
    async def search_documents(
        self,
        query: str,
        k: int = None,
        filter_metadata: Dict = None
    ) -> List[Dict[str, Any]]:
        """
        Search for relevant documents.
        
        Args:
            query: Search query
            k: Number of results to return
            filter_metadata: Optional metadata filter
            
        Returns:
            List of relevant document chunks with scores
        """
        await self.initialize()
        
        if k is None:
            k = self.top_k
        
        try:
            # Perform similarity search with scores
            results = self._vectorstore.similarity_search_with_score(
                query,
                k=k
            )
            
            formatted_results = []
            for doc, score in results:
                # Convert distance to similarity (ChromaDB returns L2 distance)
                # Lower distance = higher similarity
                similarity = 1 / (1 + score)
                
                if similarity >= self.min_relevance_score:
                    formatted_results.append({
                        "content": doc.page_content,
                        "metadata": doc.metadata,
                        "relevance_score": similarity,
                        "source": doc.metadata.get("source", "unknown")
                    })
            
            return formatted_results
            
        except Exception as e:
            logger.error(f"Search error: {e}")
            return []
    
    async def generate_answer(
        self,
        query: str,
        llm_service
    ) -> Dict[str, Any]:
        """
        Generate an answer using RAG.
        
        Args:
            query: User's question
            llm_service: LLM service for generation
            
        Returns:
            Dictionary with answer and sources
        """
        # Search for relevant documents
        relevant_docs = await self.search_documents(query, k=3)
        
        if not relevant_docs:
            return {
                "answer": None,
                "sources": [],
                "confidence": 0.0,
                "context_found": False
            }
        
        # Build context from retrieved documents
        context_parts = []
        sources = []
        
        for i, doc in enumerate(relevant_docs):
            context_parts.append(f"[Document {i+1}]: {doc['content']}")
            source = doc.get("source", "unknown")
            if source not in sources:
                sources.append(source)
        
        context = "\n\n".join(context_parts)
        
        # Generate answer using LLM
        result = await llm_service.generate_with_context(
            query=query,
            context=context
        )
        
        if not result.get("success"):
            return {
                "answer": None,
                "sources": sources,
                "confidence": 0.0,
                "context_found": True,
                "error": result.get("error")
            }
        
        # Calculate confidence
        avg_relevance = sum(d["relevance_score"] for d in relevant_docs) / len(relevant_docs)
        
        return {
            "answer": result.get("response"),
            "sources": sources,
            "confidence": avg_relevance,
            "context_found": True,
            "relevant_chunks": len(relevant_docs)
        }
    
    async def delete_document(self, filename: str) -> bool:
        """
        Delete a document from the vector store.
        
        Args:
            filename: Name of the file to delete
            
        Returns:
            True if successful
        """
        await self.initialize()
        
        try:
            # Get documents with matching source
            # Note: ChromaDB doesn't have built-in delete by metadata
            # This is a workaround
            collection = self._vectorstore._collection
            
            # Get IDs of documents from this source
            results = collection.get(
                where={"source": filename}
            )
            
            if results and results['ids']:
                collection.delete(ids=results['ids'])
                self._vectorstore.persist()
                logger.info(f"Deleted document: {filename}")
                return True
            
            return False
            
        except Exception as e:
            logger.error(f"Error deleting document: {e}")
            return False
    
    async def get_document_count(self) -> int:
        """Get total number of document chunks in the store."""
        await self.initialize()
        
        try:
            collection = self._vectorstore._collection
            return collection.count()
        except Exception:
            return 0
    
    async def get_all_sources(self) -> List[str]:
        """Get list of all indexed document sources."""
        await self.initialize()
        
        try:
            collection = self._vectorstore._collection
            results = collection.get()
            
            sources = set()
            for metadata in results.get('metadatas', []):
                if metadata and 'source' in metadata:
                    sources.add(metadata['source'])
            
            return list(sources)
        except Exception as e:
            logger.error(f"Error getting sources: {e}")
            return []
    
    async def clear_all(self):
        """Clear all documents from the vector store."""
        await self.initialize()
        
        try:
            # Delete the collection
            self._vectorstore.delete_collection()
            
            # Reinitialize
            from langchain.vectorstores import Chroma
            self._vectorstore = Chroma(
                persist_directory=self.persist_dir,
                embedding_function=self._embeddings,
                collection_name="documents"
            )
            
            logger.info("Cleared all documents from vector store")
            
        except Exception as e:
            logger.error(f"Error clearing vector store: {e}")
            raise


# ===========================================
# Singleton Instance
# ===========================================

rag_service = RAGService()
