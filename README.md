# LANGUAGE AGNOSTIC CHATBOT
================================================

## PROJECT OVERVIEW
----------------
This is a multilingual chatbot system designed to handle user queries in multiple Indian languages. 
The chatbot can understand questions in different languages, process them, and provide relevant responses 
based on a knowledge base of Frequently Asked Questions (FAQs) and document data.

## LANGUAGES SUPPORTED
-------------------
- English (en)
- Hindi (hi)
- Bengali (bn)
- Marathi (mr)
- Tamil (ta)
- Telugu (te)

## ARCHITECTURE
------------
The project follows a modern full-stack architecture with clear separation of concerns:

1. BACKEND (FastAPI - Python)
   - RESTful API server handling all business logic
   - Modular structure with organized code components
   - API routes for different functionalities

2. FRONTEND (React + Vite)
   - Interactive user interface for chat interaction
   - Language selection capability
   - Real-time message display
   - Responsive design using Tailwind CSS

## BACKEND STRUCTURE (20% Implementation)
---------------------------------------

1. API Routes (backend/app/api/routes/)
   - health.py: System health check endpoint
   - chat.py: Main chat message handling
   - faqs.py: FAQ management endpoints
   - documents.py: Document upload and management
   - admin.py: Administrative functions

2. Core Components (backend/app/core/)
   - chatbot.py: Main chatbot logic and orchestration
   - intent.py: User intent classification
   - context.py: Conversation context management
   - translation.py: Language translation services
   - rag.py: Retrieval Augmented Generation for document search

3. Services (backend/app/services/)
   - faq_service.py: FAQ retrieval and matching
   - llm_service.py: Large Language Model integration

4. Models (backend/app/models/)
   - schemas.py: Data validation schemas
   - database.py: Database connection and setup

5. Utilities (backend/app/utils/)
   - constants.py: Application constants
   - helpers.py: Helper functions
   - validators.py: Input validation

## FRONTEND STRUCTURE (20% Implementation)
----------------------------------------

1. Components (frontend/src/components/)
   - ChatWindow.jsx: Main chat interface container
   - MessageList.jsx: Display conversation messages
   - InputBox.jsx: User input handling
   - LanguageSelector.jsx: Language switching interface
   - Header.jsx: Application header

2. Pages (frontend/src/pages/)
   - ChatPage.jsx: Main chat interface page
   - AdminPage.jsx: Administrative interface

3. Contexts (frontend/src/contexts/)
   - ChatContext.jsx: Global chat state management
   - LanguageContext.jsx: Language preference management

4. Services (frontend/src/services/)
   - api.js: API communication layer
   - chatService.js: Chat-specific API calls

## KEY FEATURES IMPLEMENTED
-------------------------

1. Multi-Language Support
   - Users can select their preferred language
   - Interface elements adapt to selected language
   - FAQ database organized by language

2. FAQ System
   - Pre-loaded frequently asked questions in 6 languages
   - Quick response mechanism for common queries
   - JSON-based FAQ storage for easy management

3. RESTful API
   - Clean API design following REST principles
   - Proper HTTP methods and status codes
   - JSON request/response format

4. Modern Frontend
   - Component-based React architecture
   - State management using Context API
   - Responsive design for all devices

5. Health Monitoring
   - API health check endpoint
   - System status monitoring

## DATA ORGANIZATION
-----------------
The FAQ data is organized in JSON files by language:
- faqs_en.json: English FAQs
- faqs_hi.json: Hindi FAQs
- faqs_bn.json: Bengali FAQs
- faqs_mr.json: Marathi FAQs
- faqs_ta.json: Tamil FAQs
- faqs_te.json: Telugu FAQs

Each FAQ entry contains:
- Question in the specific language
- Answer in the specific language
- Category for organization
- Keywords for better matching

## TECHNOLOGY STACK
-----------------

Backend:
- FastAPI: Modern Python web framework
- Pydantic: Data validation
- Python 3.10+

Frontend:
- React 18: UI library
- Vite: Build tool and dev server
- Tailwind CSS: Utility-first CSS framework
- Axios: HTTP client

## CURRENT PROJECT STATUS (20%)
-----------------------------

COMPLETED:
1. Basic project structure setup
2. Backend API framework with FastAPI
3. Frontend React application with Vite
4. Component architecture for chat interface
5. Language selection mechanism
6. FAQ data structure in multiple languages
7. API routing structure
8. Basic chatbot core logic
9. Health check endpoint
10. Development environment configuration

PLANNED FOR FULL IMPLEMENTATION:
1. Complete LLM integration for intelligent responses
2. Vector database for efficient document search
3. Advanced translation using AI models
4. Context-aware conversation handling
5. Document upload and processing
6. Admin dashboard functionality
7. User authentication and authorization
8. Conversation history persistence
9. Analytics and monitoring
10. Production deployment setup

## HOW IT WORKS (Current Implementation)
--------------------------------------

1. User selects their preferred language from the interface
2. User types a question in their chosen language
3. Frontend sends the message to the backend API
4. Backend processes the request:
   - Identifies user intent
   - Searches FAQ database for matching question
   - Prepares response in the same language
5. Response is sent back to frontend
6. Frontend displays the response in the chat window

## API ENDPOINTS (Implemented)
----------------------------

GET /api/health
- Check if the API server is running
- Returns status and timestamp

POST /api/chat/message
- Send a chat message
- Accepts: message text, language code
- Returns: bot response

GET /api/faqs
- Retrieve FAQs for a specific language
- Query parameter: language code
- Returns: list of FAQs

POST /api/documents/upload
- Upload documents for knowledge base
- Accepts: file upload
- Returns: upload status

## DEVELOPMENT SETUP
-----------------

Backend:
1. Navigate to backend directory
2. Install dependencies: pip install -r requirements.txt
3. Run server: uvicorn app.main:app --reload
4. Server runs on http://localhost:8000

Frontend:
1. Navigate to frontend directory
2. Install dependencies: npm install
3. Run development server: npm run dev
4. Application runs on http://localhost:5173

## PROJECT GOALS
-------------
The ultimate goal is to create an accessible chatbot that can help users get information 
in their native language, breaking down language barriers in accessing information and services.

This 20% implementation establishes the foundation for the complete system, demonstrating:
- Technical feasibility
- Scalable architecture
- User interface design
- Multi-language capability


## 📁 Project Structure

```
language-agnostic-chatbot/
├── backend/          # FastAPI backend
├── frontend/         # React frontend
├── Information/      # Project documentation
└── README.md
```

## 🚀 Quick Start

### Backend Setup
```bash
cd backend
python -m venv venv
venv\Scripts\activate  # Windows
pip install -r requirements.txt
uvicorn app.main:app --reload
```

### Frontend Setup
```bash
cd frontend
npm install
npm run dev
```

## 📄 License

MIT License

## 👥 Team

Smart India Hackathon Project
