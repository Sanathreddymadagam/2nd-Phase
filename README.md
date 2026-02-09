# Language Agnostic Chatbot

A multilingual conversational AI chatbot for campus/college queries supporting 5+ languages with document Q&A capabilities.

## 🎯 Features

- **Multilingual Support**: Hindi, English, Tamil, Telugu, Bengali, Marathi
- **Document Q&A**: Upload PDFs and ask questions (RAG-based)
- **Context Awareness**: Maintains conversation context
- **FAQ Matching**: Quick answers from predefined FAQs
- **24/7 Availability**: Always available to answer queries
- **Conversation Logging**: All interactions logged for improvement

## 🛠️ Tech Stack

### Backend
- Python 3.10+ with FastAPI
- Ollama (LLM - llama3.2:3b)
- ChromaDB (Vector Database)
- MongoDB (Database)
- LangChain (RAG Pipeline)

### Frontend
- React 18+ with Vite
- Tailwind CSS
- Axios

### Deployment
- Backend: Render
- Frontend: Vercel
- Database: MongoDB Atlas

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
