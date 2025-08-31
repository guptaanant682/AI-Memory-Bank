# AI Memory Bank

A personal lifelong knowledge assistant powered by AI that automatically organizes, retrieves, and generates insights from your digital life.

## Features

- 🧠 **RAG-Powered Q&A**: Ask natural language questions about your documents
- 🤖 **AI Auto-Organization**: Automatic categorization and summarization
- 🎯 **Multimodal Search**: Search across text, audio, and images
- 🕸️ **Knowledge Graph**: Visualize relationships between concepts
- ⚡ **Semantic Search**: Context-aware retrieval beyond keyword matching

## Quick Start

### Prerequisites

- Python 3.9+
- Node.js 18+
- Docker (optional)

### Setup

1. **Clone and navigate**:
   ```bash
   cd ai-memory-bank
   ```

2. **Backend Setup**:
   ```bash
   cd backend
   python -m venv venv
   source venv/bin/activate  # Windows: venv\Scripts\activate
   pip install -r requirements.txt
   uvicorn main:app --reload
   ```

3. **Frontend Setup**:
   ```bash
   cd frontend
   npm install
   npm run dev
   ```

4. **Access the app**: http://localhost:3000

## Architecture

- **Frontend**: Next.js + TypeScript + TailwindCSS
- **Backend**: FastAPI + Python
- **Vector DB**: Supabase (PgVector)
- **AI Models**: Hugging Face (Mistral-7B, BLIP-2, Whisper)
- **Knowledge Graph**: Neo4j

## Development

See [PRD](../AI_Memory_Bank_PRD.md) for detailed specifications and implementation roadmap.# AI-Memory-Bank
