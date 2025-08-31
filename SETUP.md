# AI Memory Bank - Setup Guide

This guide will help you set up and run the AI Memory Bank project on your local machine.

## Prerequisites

### Required Software
- **Python 3.9+** - [Download here](https://www.python.org/downloads/)
- **Node.js 18+** - [Download here](https://nodejs.org/)
- **Git** - [Download here](https://git-scm.com/)
- **FFmpeg** - [Download here](https://ffmpeg.org/) (for audio processing)
- **Tesseract OCR** - [Download here](https://github.com/tesseract-ocr/tesseract) (for image text extraction)

### Required API Keys & Services

#### Essential (for basic functionality):
1. **Supabase Account** (Free tier available)
   - Go to [Supabase](https://supabase.com)
   - Create a new project
   - Get your Project URL and anon key from Settings > API

2. **Hugging Face Token** (Free)
   - Go to [Hugging Face](https://huggingface.co/settings/tokens)
   - Create a new token with read permissions

#### Optional (for enhanced features):
3. **OpenAI API Key** (Paid, for better LLM performance)
   - Go to [OpenAI Platform](https://platform.openai.com/api-keys)

4. **Neo4j AuraDB** (Free tier available, for knowledge graphs)
   - Go to [Neo4j Aura](https://neo4j.com/cloud/aura/)

## Quick Setup (Automated)

1. **Run the setup script**:
   ```bash
   cd ai-memory-bank
   python scripts/setup.py
   ```

2. **Configure environment variables** in `backend/.env`:
   ```env
   SUPABASE_URL=https://your-project.supabase.co
   SUPABASE_ANON_KEY=your-anon-key
   HUGGING_FACE_TOKEN=your-hf-token
   ```

3. **Set up Supabase database**:
   - Copy the contents of `backend/database/supabase_schema.sql`
   - Go to your Supabase project > SQL Editor
   - Paste and run the SQL script

4. **Start the application**:
   ```bash
   # Terminal 1 - Backend
   cd backend
   source venv/bin/activate  # Linux/Mac
   # OR: venv\Scripts\activate  # Windows
   uvicorn main:app --reload
   
   # Terminal 2 - Frontend
   cd frontend
   npm run dev
   ```

5. **Open your browser** to `http://localhost:3000`

## Manual Setup (Step by Step)

### 1. Backend Setup

```bash
cd ai-memory-bank/backend

# Create virtual environment
python -m venv venv

# Activate virtual environment
source venv/bin/activate  # Linux/Mac
# OR: venv\Scripts\activate  # Windows

# Install dependencies
pip install --upgrade pip
pip install -r requirements.txt

# Download spaCy model
python -m spacy download en_core_web_sm

# Create directories
mkdir uploads local_storage
```

### 2. Frontend Setup

```bash
cd ai-memory-bank/frontend

# Install dependencies
npm install
```

### 3. Environment Configuration

Create `backend/.env` file:
```env
# Database
DATABASE_URL=postgresql://user:password@localhost:5432/ai_memory_bank

# Supabase
SUPABASE_URL=https://your-project.supabase.co
SUPABASE_ANON_KEY=your-anon-key
SUPABASE_SERVICE_ROLE_KEY=your-service-role-key

# Hugging Face
HUGGING_FACE_TOKEN=your-hf-token

# Neo4j (optional)
NEO4J_URI=bolt://localhost:7687
NEO4J_USER=neo4j
NEO4J_PASSWORD=password123

# App Settings
UPLOAD_DIR=uploads
MAX_FILE_SIZE_MB=50
```

### 4. Supabase Database Setup

1. Go to your Supabase project
2. Navigate to SQL Editor
3. Copy and paste the contents of `backend/database/supabase_schema.sql`
4. Run the script to create tables and functions

### 5. Start Development Servers

**Backend** (Terminal 1):
```bash
cd backend
source venv/bin/activate  # Linux/Mac
uvicorn main:app --reload --host 0.0.0.0 --port 8000
```

**Frontend** (Terminal 2):
```bash
cd frontend
npm run dev
```

## Testing the Setup

1. Open `http://localhost:3000` in your browser
2. Upload different file types:
   - **Text**: PDF, DOC, TXT, MD files
   - **Images**: JPG, PNG, GIF files
   - **Audio**: MP3, WAV, M4A files
3. Ask questions about the uploaded content
4. Verify you get AI-generated responses from multimodal content

## Common Issues & Solutions

### Python Issues
- **"Python not found"**: Make sure Python 3.9+ is installed and in your PATH
- **"pip not found"**: Try `python -m pip` instead of `pip`
- **Virtual environment issues**: Delete `venv` folder and recreate it

### Node.js Issues
- **"npm not found"**: Install Node.js from the official website
- **Package installation fails**: Try `npm install --legacy-peer-deps`
- **Port 3000 in use**: Kill the process or use a different port

### AI Model Issues
- **"Model not found"**: Check your Hugging Face token is valid
- **Slow performance**: Models will download on first use (may take time)
- **Out of memory**: Use smaller models or increase system RAM
- **Whisper download fails**: Ensure stable internet connection for model download
- **BLIP model errors**: First run requires downloading large vision models (~2GB)

### Database Issues
- **Supabase connection fails**: Check your URL and API keys
- **Vector extension error**: Make sure the pgvector extension is enabled
- **Permission denied**: Check your Row Level Security policies

### API Issues
- **CORS errors**: Make sure frontend URL is in CORS allowed origins
- **File upload fails**: Check file size limits and supported formats
- **Slow responses**: First-time model loading can take several minutes
- **Audio processing fails**: Check FFmpeg installation
- **Image text extraction fails**: Install Tesseract OCR

## Development Tips

### Model Performance
- **CPU vs GPU**: Models will use GPU if available (much faster)
- **Model caching**: Models are cached after first load
- **Batch processing**: Upload multiple documents at once for efficiency

### Database Performance
- **Vector search**: Use appropriate similarity thresholds (0.5-0.8)
- **Indexing**: Ensure vector indexes are created for large datasets
- **Chunking**: Adjust chunk size (500 words) based on your content

### Local Development
- **Without Supabase**: The system will fall back to local JSON storage
- **Offline mode**: Most AI models can run offline after initial download
- **Docker**: Use `docker-compose up` for containerized development

## Production Deployment

For production deployment, see:
- Frontend: Deploy to [Vercel](https://vercel.com) or [Netlify](https://netlify.com)
- Backend: Deploy to [Railway](https://railway.app) or [Render](https://render.com)
- Database: Use [Supabase](https://supabase.com) hosted database

## Getting Help

- **Issues**: Check the [PRD document](AI_Memory_Bank_PRD.md) for detailed specifications
- **API Documentation**: Visit `http://localhost:8000/docs` when backend is running
- **Logs**: Check console output for detailed error messages

## Next Steps

After successful setup:
1. **Phase 2**: Add multimodal support (audio, images)
2. **Phase 3**: Implement knowledge graph visualization  
3. **Phase 4**: Add collaborative features
4. **Phase 5**: Deploy to production

Happy coding! 🚀