"""
Utility helper functions.
"""

import uuid
import re
from datetime import datetime
from typing import Optional, Dict, Any, List
import hashlib


def generate_session_id() -> str:
    """Generate a unique session ID."""
    return str(uuid.uuid4())


def generate_document_id() -> str:
    """Generate a unique document ID."""
    return str(uuid.uuid4())


def get_current_timestamp() -> datetime:
    """Get current UTC timestamp."""
    return datetime.utcnow()


def sanitize_filename(filename: str) -> str:
    """
    Sanitize filename to remove special characters.
    
    Args:
        filename: Original filename
        
    Returns:
        Sanitized filename
    """
    # Remove special characters except dots and underscores
    sanitized = re.sub(r'[^\w\s.-]', '', filename)
    # Replace spaces with underscores
    sanitized = sanitized.replace(' ', '_')
    # Remove multiple consecutive underscores
    sanitized = re.sub(r'_+', '_', sanitized)
    return sanitized


def get_file_extension(filename: str) -> str:
    """Get file extension from filename."""
    if '.' in filename:
        return filename.rsplit('.', 1)[-1].lower()
    return ''


def calculate_file_hash(content: bytes) -> str:
    """Calculate MD5 hash of file content."""
    return hashlib.md5(content).hexdigest()


def truncate_text(text: str, max_length: int = 500, suffix: str = "...") -> str:
    """
    Truncate text to maximum length.
    
    Args:
        text: Input text
        max_length: Maximum length
        suffix: Suffix to add if truncated
        
    Returns:
        Truncated text
    """
    if len(text) <= max_length:
        return text
    return text[:max_length - len(suffix)] + suffix


def clean_text(text: str) -> str:
    """
    Clean text by removing extra whitespace and special characters.
    
    Args:
        text: Input text
        
    Returns:
        Cleaned text
    """
    # Remove extra whitespace
    text = re.sub(r'\s+', ' ', text)
    # Remove leading/trailing whitespace
    text = text.strip()
    return text


def extract_keywords(text: str, min_length: int = 3) -> List[str]:
    """
    Extract keywords from text.
    
    Args:
        text: Input text
        min_length: Minimum keyword length
        
    Returns:
        List of keywords
    """
    # Remove special characters and convert to lowercase
    text = re.sub(r'[^\w\s]', '', text.lower())
    # Split into words
    words = text.split()
    # Filter by minimum length and remove common words
    stop_words = {'the', 'a', 'an', 'is', 'are', 'was', 'were', 'be', 'been',
                  'being', 'have', 'has', 'had', 'do', 'does', 'did', 'will',
                  'would', 'could', 'should', 'may', 'might', 'can', 'to', 'of',
                  'in', 'for', 'on', 'with', 'at', 'by', 'from', 'as', 'into',
                  'about', 'like', 'through', 'after', 'over', 'between', 'out',
                  'against', 'during', 'without', 'before', 'under', 'around',
                  'among', 'and', 'or', 'but', 'if', 'then', 'else', 'when',
                  'up', 'down', 'that', 'this', 'these', 'those', 'what', 'which',
                  'who', 'whom', 'whose', 'where', 'why', 'how', 'all', 'each',
                  'every', 'both', 'few', 'more', 'most', 'other', 'some', 'such',
                  'no', 'nor', 'not', 'only', 'own', 'same', 'so', 'than', 'too',
                  'very', 'just', 'also', 'now', 'here', 'there', 'my', 'your',
                  'his', 'her', 'its', 'our', 'their', 'me', 'you', 'him', 'us',
                  'them', 'i', 'we', 'he', 'she', 'it', 'they'}
    
    keywords = [word for word in words 
                if len(word) >= min_length and word not in stop_words]
    
    # Remove duplicates while preserving order
    seen = set()
    unique_keywords = []
    for word in keywords:
        if word not in seen:
            seen.add(word)
            unique_keywords.append(word)
    
    return unique_keywords


def format_response_time(milliseconds: float) -> str:
    """Format response time for display."""
    if milliseconds < 1000:
        return f"{milliseconds:.0f}ms"
    else:
        return f"{milliseconds/1000:.2f}s"


def calculate_confidence_score(
    faq_score: float = 0.0,
    rag_score: float = 0.0,
    llm_confidence: float = 0.5
) -> float:
    """
    Calculate overall confidence score from multiple sources.
    
    Args:
        faq_score: FAQ matching score (0-1)
        rag_score: RAG relevance score (0-1)
        llm_confidence: LLM confidence (0-1)
        
    Returns:
        Combined confidence score (0-1)
    """
    # Weight the scores
    weights = {
        'faq': 0.4,
        'rag': 0.4,
        'llm': 0.2
    }
    
    # Calculate weighted average
    total_score = (
        faq_score * weights['faq'] +
        rag_score * weights['rag'] +
        llm_confidence * weights['llm']
    )
    
    # Normalize to 0-1 range
    return min(max(total_score, 0.0), 1.0)


def mask_sensitive_data(text: str) -> str:
    """
    Mask sensitive data like phone numbers and emails.
    
    Args:
        text: Input text
        
    Returns:
        Text with masked sensitive data
    """
    # Mask email addresses
    text = re.sub(
        r'([a-zA-Z0-9_.+-]+)@([a-zA-Z0-9-]+\.[a-zA-Z0-9-.]+)',
        r'***@***.***',
        text
    )
    
    # Mask phone numbers (Indian format)
    text = re.sub(
        r'(\+91|0)?[\s-]?[6-9]\d{4}[\s-]?\d{5}',
        '***-***-****',
        text
    )
    
    return text


def paginate(
    items: List[Any],
    page: int = 1,
    per_page: int = 10
) -> Dict[str, Any]:
    """
    Paginate a list of items.
    
    Args:
        items: List of items
        page: Page number (1-indexed)
        per_page: Items per page
        
    Returns:
        Dictionary with paginated items and metadata
    """
    total = len(items)
    total_pages = (total + per_page - 1) // per_page
    
    start = (page - 1) * per_page
    end = start + per_page
    
    return {
        'items': items[start:end],
        'page': page,
        'per_page': per_page,
        'total': total,
        'total_pages': total_pages,
        'has_next': page < total_pages,
        'has_prev': page > 1
    }
