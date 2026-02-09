"""
Application constants.
"""

# ===========================================
# Language Constants
# ===========================================

LANGUAGES = {
    "en": {
        "name": "English",
        "native_name": "English",
        "flag": "🇬🇧",
        "greeting": "Hello! How can I help you today?",
        "fallback": "I'm sorry, I couldn't understand that. Could you please rephrase?",
        "error": "Something went wrong. Please try again.",
        "human_handoff": "Let me connect you with a human agent for better assistance."
    },
    "hi": {
        "name": "Hindi",
        "native_name": "हिंदी",
        "flag": "🇮🇳",
        "greeting": "नमस्ते! आज मैं आपकी कैसे मदद कर सकता हूं?",
        "fallback": "मुझे खेद है, मैं यह समझ नहीं पाया। कृपया दोबारा कहें।",
        "error": "कुछ गलत हो गया। कृपया पुनः प्रयास करें।",
        "human_handoff": "बेहतर सहायता के लिए मैं आपको एक मानव एजेंट से जोड़ता हूं।"
    },
    "ta": {
        "name": "Tamil",
        "native_name": "தமிழ்",
        "flag": "🇮🇳",
        "greeting": "வணக்கம்! இன்று நான் உங்களுக்கு எப்படி உதவ முடியும்?",
        "fallback": "மன்னிக்கவும், என்னால் புரிந்துகொள்ள முடியவில்லை. தயவுசெய்து மீண்டும் கூறுங்கள்.",
        "error": "ஏதோ தவறு ஏற்பட்டது. மீண்டும் முயற்சிக்கவும்.",
        "human_handoff": "சிறந்த உதவிக்கு நான் உங்களை ஒரு நிபுணரிடம் இணைக்கிறேன்."
    },
    "te": {
        "name": "Telugu",
        "native_name": "తెలుగు",
        "flag": "🇮🇳",
        "greeting": "నమస్కారం! ఈరోజు నేను మీకు ఎలా సహాయం చేయగలను?",
        "fallback": "క్షమించండి, నేను అర్థం చేసుకోలేకపోయాను. దయచేసి మళ్ళీ చెప్పండి.",
        "error": "ఏదో తప్పు జరిగింది. దయచేసి మళ్ళీ ప్రయత్నించండి.",
        "human_handoff": "మెరుగైన సహాయం కోసం నేను మిమ్మల్ని ఒక నిపుణుడితో అనుసంధానం చేస్తాను."
    },
    "bn": {
        "name": "Bengali",
        "native_name": "বাংলা",
        "flag": "🇮🇳",
        "greeting": "নমস্কার! আজ আমি আপনাকে কীভাবে সাহায্য করতে পারি?",
        "fallback": "দুঃখিত, আমি বুঝতে পারলাম না। অনুগ্রহ করে আবার বলুন।",
        "error": "কিছু ভুল হয়েছে। অনুগ্রহ করে আবার চেষ্টা করুন।",
        "human_handoff": "আরও ভালো সাহায্যের জন্য আমি আপনাকে একজন বিশেষজ্ঞের সাথে সংযুক্ত করছি।"
    },
    "mr": {
        "name": "Marathi",
        "native_name": "मराठी",
        "flag": "🇮🇳",
        "greeting": "नमस्कार! आज मी तुम्हाला कशी मदत करू शकतो?",
        "fallback": "क्षमा करा, मला समजले नाही. कृपया पुन्हा सांगा.",
        "error": "काहीतरी चूक झाली. कृपया पुन्हा प्रयत्न करा.",
        "human_handoff": "अधिक चांगल्या मदतीसाठी मी तुम्हाला तज्ञाशी जोडतो."
    }
}


# ===========================================
# Intent Keywords
# ===========================================

INTENT_KEYWORDS = {
    "greeting": [
        "hello", "hi", "hey", "namaste", "good morning", "good afternoon",
        "good evening", "howdy", "greetings", "नमस्ते", "नमस्कार"
    ],
    "fee_query": [
        "fee", "fees", "payment", "amount", "cost", "tuition", "charges",
        "price", "pay", "money", "शुल्क", "फीस", "पैसे"
    ],
    "admission": [
        "admission", "apply", "application", "eligibility", "seat", "enroll",
        "enrollment", "join", "entry", "प्रवेश", "दाखिला"
    ],
    "scholarship": [
        "scholarship", "financial aid", "grant", "stipend", "merit",
        "concession", "discount", "waiver", "छात्रवृत्ति", "स्कॉलरशिप"
    ],
    "timetable": [
        "timetable", "schedule", "class timing", "lecture", "period",
        "timing", "when", "time", "समय", "समय सारणी"
    ],
    "exam": [
        "exam", "examination", "test", "marks", "result", "grade",
        "score", "passing", "fail", "परीक्षा", "रिजल्ट"
    ],
    "document": [
        "document", "certificate", "transcript", "bonafide", "letter",
        "attestation", "verification", "दस्तावेज़", "प्रमाणपत्र"
    ],
    "contact": [
        "contact", "phone", "email", "address", "office", "location",
        "where", "reach", "संपर्क", "पता"
    ],
    "hostel": [
        "hostel", "accommodation", "room", "mess", "stay", "living",
        "dormitory", "हॉस्टल", "छात्रावास"
    ],
    "library": [
        "library", "book", "borrow", "return", "reading", "पुस्तकालय", "किताब"
    ],
    "goodbye": [
        "bye", "goodbye", "see you", "thank you", "thanks", "धन्यवाद",
        "अलविदा", "good bye"
    ]
}


# ===========================================
# System Prompts
# ===========================================

SYSTEM_PROMPTS = {
    "default": """You are a helpful campus assistant chatbot for a college/university. 
Your job is to answer student queries about admissions, fees, scholarships, timetables, 
exams, documents, and other campus-related topics.

Guidelines:
1. Be friendly, concise, and helpful
2. If you're not sure about something, say so clearly
3. Provide accurate information based on the context given
4. If the question is outside your knowledge, suggest contacting the relevant office
5. Keep responses under 200 words unless more detail is needed
6. Use bullet points for lists when appropriate""",

    "faq_response": """Based on the FAQ information provided, give a clear and helpful answer.
If the FAQ doesn't fully answer the question, supplement with general helpful information.""",

    "rag_response": """Answer the question based ONLY on the provided context from documents.
If the context doesn't contain the answer, clearly state that you don't have that information
and suggest where the user might find it.

Context:
{context}

Question: {question}

Provide a helpful, accurate answer based on the context above.""",

    "conversation_context": """Previous conversation:
{history}

Current question: {question}

Consider the conversation history when answering. If this is a follow-up question,
use context from previous messages."""
}


# ===========================================
# Response Templates
# ===========================================

RESPONSE_TEMPLATES = {
    "no_answer": "I don't have specific information about that. Please contact the {office} office for accurate details.",
    "general_help": "I can help you with information about:\n• Admissions\n• Fees & Payments\n• Scholarships\n• Timetables\n• Exams & Results\n• Documents\n• Contact Information\n\nWhat would you like to know?",
    "suggest_contact": "For detailed information, please contact:\n• Email: {email}\n• Phone: {phone}\n• Office: {office}",
}


# ===========================================
# Error Messages
# ===========================================

ERROR_MESSAGES = {
    "llm_unavailable": "The AI service is temporarily unavailable. Please try again later.",
    "translation_failed": "Translation service is currently unavailable.",
    "database_error": "Unable to process your request. Please try again.",
    "rate_limit": "Too many requests. Please wait a moment and try again.",
    "file_too_large": "The file is too large. Maximum size is 10MB.",
    "invalid_file_type": "Invalid file type. Please upload PDF, TXT, or DOCX files.",
    "session_expired": "Your session has expired. Starting a new conversation.",
}


# ===========================================
# Confidence Thresholds
# ===========================================

CONFIDENCE_THRESHOLDS = {
    "high": 0.8,      # High confidence, use response directly
    "medium": 0.5,    # Medium confidence, use with disclaimer
    "low": 0.3,       # Low confidence, suggest human help
    "fallback": 0.2   # Very low, trigger fallback
}


# ===========================================
# RAG Configuration
# ===========================================

RAG_CONFIG = {
    "chunk_size": 500,
    "chunk_overlap": 50,
    "top_k": 3,
    "min_relevance_score": 0.3
}


# ===========================================
# Suggested Questions by Category
# ===========================================

SUGGESTED_QUESTIONS = {
    "admission": [
        "What are the eligibility criteria?",
        "What documents are required?",
        "What is the application deadline?"
    ],
    "fees": [
        "What is the semester fee?",
        "What payment methods are accepted?",
        "Is there any late fee penalty?"
    ],
    "scholarship": [
        "Who is eligible for scholarship?",
        "How to apply for scholarship?",
        "What is the scholarship amount?"
    ],
    "exam": [
        "When are the exams scheduled?",
        "What is the passing criteria?",
        "How can I check my results?"
    ],
    "general": [
        "What are the admission requirements?",
        "What is the fee structure?",
        "Are there any scholarships available?"
    ]
}
