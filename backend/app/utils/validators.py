"""
Input validation utilities.
"""

import re
from typing import Optional, Tuple, List
from app.utils.constants import LANGUAGES


def validate_message(message: str) -> Tuple[bool, Optional[str]]:
    """
    Validate user message.
    
    Args:
        message: User message
        
    Returns:
        Tuple of (is_valid, error_message)
    """
    if not message:
        return False, "Message cannot be empty"
    
    if len(message) < 1:
        return False, "Message is too short"
    
    if len(message) > 2000:
        return False, "Message exceeds maximum length of 2000 characters"
    
    # Check for potentially harmful content (basic check)
    harmful_patterns = [
        r'<script.*?>.*?</script>',  # Script tags
        r'javascript:',               # JavaScript protocol
        r'on\w+\s*=',                 # Event handlers
    ]
    
    for pattern in harmful_patterns:
        if re.search(pattern, message, re.IGNORECASE):
            return False, "Message contains invalid content"
    
    return True, None


def validate_language(language: str) -> Tuple[bool, Optional[str]]:
    """
    Validate language code.
    
    Args:
        language: Language code
        
    Returns:
        Tuple of (is_valid, error_message)
    """
    if not language:
        return False, "Language code is required"
    
    if language not in LANGUAGES:
        valid_codes = ", ".join(LANGUAGES.keys())
        return False, f"Invalid language code. Valid codes: {valid_codes}"
    
    return True, None


def validate_session_id(session_id: str) -> Tuple[bool, Optional[str]]:
    """
    Validate session ID format.
    
    Args:
        session_id: Session ID
        
    Returns:
        Tuple of (is_valid, error_message)
    """
    if not session_id:
        return True, None  # Session ID is optional
    
    # UUID format check
    uuid_pattern = r'^[a-f0-9]{8}-[a-f0-9]{4}-[a-f0-9]{4}-[a-f0-9]{4}-[a-f0-9]{12}$'
    if not re.match(uuid_pattern, session_id, re.IGNORECASE):
        return False, "Invalid session ID format"
    
    return True, None


def validate_file_upload(
    filename: str,
    content_type: str,
    size: int,
    max_size: int = 10 * 1024 * 1024,
    allowed_extensions: List[str] = None
) -> Tuple[bool, Optional[str]]:
    """
    Validate file upload.
    
    Args:
        filename: Original filename
        content_type: MIME type
        size: File size in bytes
        max_size: Maximum allowed size
        allowed_extensions: List of allowed extensions
        
    Returns:
        Tuple of (is_valid, error_message)
    """
    if allowed_extensions is None:
        allowed_extensions = ['pdf', 'txt', 'docx']
    
    if not filename:
        return False, "Filename is required"
    
    # Check file extension
    ext = filename.rsplit('.', 1)[-1].lower() if '.' in filename else ''
    if ext not in allowed_extensions:
        return False, f"Invalid file type. Allowed: {', '.join(allowed_extensions)}"
    
    # Check file size
    if size > max_size:
        max_mb = max_size / (1024 * 1024)
        return False, f"File too large. Maximum size: {max_mb:.0f}MB"
    
    if size == 0:
        return False, "File is empty"
    
    # Check content type
    valid_content_types = {
        'pdf': 'application/pdf',
        'txt': 'text/plain',
        'docx': 'application/vnd.openxmlformats-officedocument.wordprocessingml.document'
    }
    
    expected_type = valid_content_types.get(ext)
    if expected_type and content_type != expected_type:
        # Allow some flexibility for text files
        if ext == 'txt' and 'text' in content_type:
            pass
        else:
            return False, "File content type does not match extension"
    
    return True, None


def validate_faq_input(
    question: str,
    answer: str,
    category: str,
    language: str
) -> Tuple[bool, Optional[str]]:
    """
    Validate FAQ input.
    
    Args:
        question: FAQ question
        answer: FAQ answer
        category: FAQ category
        language: Language code
        
    Returns:
        Tuple of (is_valid, error_message)
    """
    if not question or len(question) < 5:
        return False, "Question must be at least 5 characters"
    
    if len(question) > 500:
        return False, "Question exceeds maximum length of 500 characters"
    
    if not answer or len(answer) < 10:
        return False, "Answer must be at least 10 characters"
    
    if len(answer) > 2000:
        return False, "Answer exceeds maximum length of 2000 characters"
    
    if not category or len(category) < 2:
        return False, "Category is required"
    
    is_valid_lang, lang_error = validate_language(language)
    if not is_valid_lang:
        return False, lang_error
    
    return True, None


def validate_rating(rating: int) -> Tuple[bool, Optional[str]]:
    """
    Validate feedback rating.
    
    Args:
        rating: Rating value
        
    Returns:
        Tuple of (is_valid, error_message)
    """
    if not isinstance(rating, int):
        return False, "Rating must be an integer"
    
    if rating < 1 or rating > 5:
        return False, "Rating must be between 1 and 5"
    
    return True, None


def sanitize_input(text: str) -> str:
    """
    Sanitize user input to prevent injection attacks.
    
    Args:
        text: User input
        
    Returns:
        Sanitized text
    """
    if not text:
        return ""
    
    # Remove control characters
    text = re.sub(r'[\x00-\x08\x0b\x0c\x0e-\x1f\x7f]', '', text)
    
    # Escape HTML entities
    text = text.replace('&', '&amp;')
    text = text.replace('<', '&lt;')
    text = text.replace('>', '&gt;')
    text = text.replace('"', '&quot;')
    text = text.replace("'", '&#x27;')
    
    return text.strip()
