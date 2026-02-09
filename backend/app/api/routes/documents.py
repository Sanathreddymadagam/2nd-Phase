"""
Document API Routes - Endpoints for document upload and management.
"""

from fastapi import APIRouter, UploadFile, File, HTTPException, Form, Query
from typing import Optional, List
import logging
import os
from pathlib import Path
import aiofiles
from datetime import datetime

from app.config import settings
from app.models.schemas import DocumentUploadResponse, DocumentListResponse, DocumentInfo
from app.models.database import MongoDB, Collections
from app.core.rag import rag_service
from app.utils.helpers import generate_document_id, sanitize_filename, get_file_extension
from app.utils.validators import validate_file_upload

router = APIRouter()
logger = logging.getLogger(__name__)

# Ensure upload directory exists
UPLOAD_DIR = Path(settings.UPLOAD_DIR)
UPLOAD_DIR.mkdir(parents=True, exist_ok=True)


@router.post("/upload", response_model=DocumentUploadResponse)
async def upload_document(
    file: UploadFile = File(...),
    category: Optional[str] = Form(default=None)
):
    """
    Upload a document for RAG-based Q&A.
    
    Supported formats: PDF, TXT, DOCX
    Maximum size: 10MB
    
    The document will be:
    1. Saved to the server
    2. Processed and split into chunks
    3. Indexed in the vector database
    
    After upload, users can ask questions about the document content.
    """
    try:
        # Read file content for validation
        content = await file.read()
        file_size = len(content)
        
        # Validate file
        is_valid, error_msg = validate_file_upload(
            filename=file.filename,
            content_type=file.content_type,
            size=file_size,
            max_size=settings.MAX_FILE_SIZE,
            allowed_extensions=settings.ALLOWED_EXTENSIONS
        )
        
        if not is_valid:
            raise HTTPException(status_code=400, detail=error_msg)
        
        # Generate unique filename
        doc_id = generate_document_id()
        ext = get_file_extension(file.filename)
        safe_name = sanitize_filename(file.filename)
        stored_filename = f"{doc_id}_{safe_name}"
        file_path = UPLOAD_DIR / stored_filename
        
        # Save file
        async with aiofiles.open(file_path, 'wb') as f:
            await f.write(content)
        
        logger.info(f"Saved file: {stored_filename}")
        
        # Process document with RAG service
        rag_result = await rag_service.add_document(
            file_path=str(file_path),
            metadata={
                "document_id": doc_id,
                "original_name": file.filename,
                "category": category
            }
        )
        
        if not rag_result.get("success"):
            # Clean up file on failure
            os.remove(file_path)
            raise HTTPException(
                status_code=500,
                detail=f"Failed to process document: {rag_result.get('error')}"
            )
        
        # Save metadata to database
        doc_metadata = {
            "_id": doc_id,
            "filename": stored_filename,
            "original_name": file.filename,
            "file_path": str(file_path),
            "content_type": file.content_type,
            "size": file_size,
            "category": category,
            "uploaded_at": datetime.utcnow(),
            "processed": True,
            "chunk_count": rag_result.get("chunks_added", 0)
        }
        
        try:
            db = MongoDB.get_db()
            await db[Collections.DOCUMENTS].insert_one(doc_metadata)
        except Exception as e:
            logger.warning(f"Failed to save document metadata: {e}")
        
        return DocumentUploadResponse(
            success=True,
            document_id=doc_id,
            filename=stored_filename,
            original_name=file.filename,
            chunks_processed=rag_result.get("chunks_added", 0),
            message=f"Document uploaded and processed successfully. {rag_result.get('chunks_added', 0)} chunks indexed."
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Upload error: {e}", exc_info=True)
        raise HTTPException(
            status_code=500,
            detail=f"Failed to upload document: {str(e)}"
        )


@router.get("/list", response_model=DocumentListResponse)
async def list_documents(
    category: Optional[str] = Query(default=None),
    page: int = Query(default=1, ge=1),
    per_page: int = Query(default=20, ge=1, le=100)
):
    """
    List all uploaded documents.
    
    - **category**: Optional category filter
    - **page**: Page number
    - **per_page**: Items per page
    """
    try:
        db = MongoDB.get_db()
        
        # Build query
        query = {}
        if category:
            query["category"] = category
        
        # Get total count
        total = await db[Collections.DOCUMENTS].count_documents(query)
        
        # Get documents
        skip = (page - 1) * per_page
        cursor = db[Collections.DOCUMENTS].find(query).skip(skip).limit(per_page).sort("uploaded_at", -1)
        docs = await cursor.to_list(length=per_page)
        
        # Format response
        documents = [
            DocumentInfo(
                id=str(doc["_id"]),
                filename=doc["filename"],
                original_name=doc["original_name"],
                content_type=doc.get("content_type", "application/octet-stream"),
                size=doc["size"],
                uploaded_at=doc["uploaded_at"],
                processed=doc.get("processed", False),
                chunk_count=doc.get("chunk_count", 0),
                category=doc.get("category")
            )
            for doc in docs
        ]
        
        return DocumentListResponse(documents=documents, total=total)
        
    except Exception as e:
        logger.error(f"List documents error: {e}")
        return DocumentListResponse(documents=[], total=0)


@router.get("/{document_id}")
async def get_document(document_id: str):
    """
    Get document metadata by ID.
    """
    try:
        db = MongoDB.get_db()
        doc = await db[Collections.DOCUMENTS].find_one({"_id": document_id})
        
        if not doc:
            raise HTTPException(status_code=404, detail="Document not found")
        
        return DocumentInfo(
            id=str(doc["_id"]),
            filename=doc["filename"],
            original_name=doc["original_name"],
            content_type=doc.get("content_type", "application/octet-stream"),
            size=doc["size"],
            uploaded_at=doc["uploaded_at"],
            processed=doc.get("processed", False),
            chunk_count=doc.get("chunk_count", 0),
            category=doc.get("category")
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Get document error: {e}")
        raise HTTPException(status_code=500, detail="Failed to get document")


@router.delete("/{document_id}")
async def delete_document(document_id: str):
    """
    Delete a document.
    
    This will:
    1. Remove the file from disk
    2. Remove from vector database
    3. Remove metadata from MongoDB
    """
    try:
        db = MongoDB.get_db()
        
        # Get document metadata
        doc = await db[Collections.DOCUMENTS].find_one({"_id": document_id})
        
        if not doc:
            raise HTTPException(status_code=404, detail="Document not found")
        
        # Delete file from disk
        file_path = doc.get("file_path")
        if file_path and os.path.exists(file_path):
            os.remove(file_path)
            logger.info(f"Deleted file: {file_path}")
        
        # Delete from vector store
        filename = doc.get("filename")
        if filename:
            await rag_service.delete_document(filename)
        
        # Delete from database
        await db[Collections.DOCUMENTS].delete_one({"_id": document_id})
        
        return {
            "success": True,
            "message": "Document deleted successfully",
            "document_id": document_id
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Delete document error: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Failed to delete document: {str(e)}"
        )


@router.get("/search/query")
async def search_documents(
    q: str = Query(..., min_length=1, max_length=500),
    k: int = Query(default=5, ge=1, le=20)
):
    """
    Search documents using semantic search.
    
    - **q**: Search query
    - **k**: Number of results to return
    
    Returns relevant document chunks matching the query.
    """
    try:
        results = await rag_service.search_documents(query=q, k=k)
        
        return {
            "query": q,
            "results": results,
            "count": len(results)
        }
        
    except Exception as e:
        logger.error(f"Document search error: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Search failed: {str(e)}"
        )


@router.get("/stats/summary")
async def get_document_stats():
    """
    Get document statistics.
    """
    try:
        db = MongoDB.get_db()
        
        # Total documents
        total_docs = await db[Collections.DOCUMENTS].count_documents({})
        
        # Total chunks in vector store
        total_chunks = await rag_service.get_document_count()
        
        # Get all sources
        sources = await rag_service.get_all_sources()
        
        # Categories
        categories = await db[Collections.DOCUMENTS].distinct("category")
        
        # Total size
        pipeline = [
            {"$group": {"_id": None, "total_size": {"$sum": "$size"}}}
        ]
        size_result = await db[Collections.DOCUMENTS].aggregate(pipeline).to_list(1)
        total_size = size_result[0]["total_size"] if size_result else 0
        
        return {
            "total_documents": total_docs,
            "total_chunks": total_chunks,
            "indexed_sources": len(sources),
            "categories": categories,
            "total_size_bytes": total_size,
            "total_size_mb": round(total_size / (1024 * 1024), 2)
        }
        
    except Exception as e:
        logger.error(f"Stats error: {e}")
        return {
            "total_documents": 0,
            "total_chunks": 0,
            "error": str(e)
        }
