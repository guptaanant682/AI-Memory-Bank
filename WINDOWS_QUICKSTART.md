# 🚀 AI Memory Bank - Windows Quick Start Guide

## 🎯 **INSTANT WORKING VERSION**

### **Step 1: Start the Simplified Backend**

**Open Command Prompt or PowerShell and run:**

```cmd
cd "C:\Users\pc\Downloads\major project\ai-memory-bank\backend"
python main_simple.py
```

**You should see:**
```
🚀 Starting AI Memory Bank - Simplified Backend
📍 API will be available at: http://localhost:8000
📚 API Documentation: http://localhost:8000/docs
```

### **Step 2: Test Your System**

**Open your web browser and go to:**
- **API Interface**: http://localhost:8000/docs
- **Health Check**: http://localhost:8000/health

### **Step 3: Upload and Query Documents**

**Using the API interface at http://localhost:8000/docs:**

1. **Upload a file**: Use the `/upload` endpoint
   - Click "Try it out"
   - Choose a `.txt` or `.md` file
   - Click "Execute"

2. **Query your content**: Use the `/query` endpoint
   - Click "Try it out"  
   - Enter a question about your document
   - Click "Execute"

3. **View documents**: Use the `/documents` endpoint

---

## 🔧 **FULL VERSION SETUP** (If you want all AI features)

### **Step 1: Install Dependencies**

```cmd
cd "C:\Users\pc\Downloads\major project\ai-memory-bank\backend"

# Install basic dependencies
pip install fastapi uvicorn python-multipart python-dotenv pydantic
pip install aiofiles requests sqlalchemy psycopg2-binary
pip install pypdf python-docx pillow numpy pandas

# Optional: Heavy AI models (takes time and space)
pip install torch transformers sentence-transformers spacy
python -m spacy download en_core_web_sm
```

### **Step 2: Start Full Backend**

```cmd
uvicorn main:app --reload --port 8000
```

---

## 🌐 **FRONTEND SETUP**

### **Option 1: Simple Test Page**

Create a basic HTML file to test your API:

```html
<!DOCTYPE html>
<html>
<head><title>AI Memory Bank Test</title></head>
<body>
    <h1>AI Memory Bank - Test Interface</h1>
    
    <div>
        <h2>Upload Document</h2>
        <input type="file" id="fileInput">
        <button onclick="uploadFile()">Upload</button>
    </div>
    
    <div>
        <h2>Ask Question</h2>
        <input type="text" id="queryInput" placeholder="Ask about your documents...">
        <button onclick="queryDocuments()">Ask</button>
        <div id="answer"></div>
    </div>

    <script>
        async function uploadFile() {
            const file = document.getElementById('fileInput').files[0];
            if (!file) return;
            
            const formData = new FormData();
            formData.append('file', file);
            
            const response = await fetch('http://localhost:8000/upload', {
                method: 'POST',
                body: formData
            });
            
            const result = await response.json();
            alert('Upload successful: ' + result.filename);
        }
        
        async function queryDocuments() {
            const query = document.getElementById('queryInput').value;
            if (!query) return;
            
            const formData = new FormData();
            formData.append('query', query);
            
            const response = await fetch('http://localhost:8000/query', {
                method: 'POST',
                body: formData
            });
            
            const result = await response.json();
            document.getElementById('answer').innerHTML = 
                '<h3>Answer:</h3><p>' + result.answer + '</p>';
        }
    </script>
</body>
</html>
```

Save this as `test.html` and open it in your browser.

### **Option 2: Full Next.js Frontend**

```cmd
cd "C:\Users\pc\Downloads\major project\ai-memory-bank\frontend"
npm install
npm run dev
```

Then access: http://localhost:3000

---

## ✅ **WHAT WORKS RIGHT NOW**

### **Simplified Version Features:**
- ✅ **File Upload**: Upload text and markdown files
- ✅ **Document Storage**: Files saved to disk
- ✅ **Basic Search**: Keyword-based document search
- ✅ **Simple Q&A**: Basic question answering
- ✅ **Document Management**: List, view, delete documents
- ✅ **API Documentation**: Full Swagger/OpenAPI docs

### **Database Services Running:**
- ✅ **PostgreSQL**: localhost:5432
- ✅ **Neo4j**: http://localhost:7474 (neo4j/password123)
- ✅ **Redis**: localhost:6379
- ✅ **Prometheus**: http://localhost:9090

---

## 🚀 **QUICK TEST WORKFLOW**

1. **Start backend**: `python main_simple.py`
2. **Go to**: http://localhost:8000/docs
3. **Upload** a text file with some content
4. **Query** it with questions about the content
5. **View results** in the API response

---

## 🔧 **TROUBLESHOOTING**

### **If you get module errors:**
```cmd
pip install <missing-module-name>
```

### **If port 8000 is busy:**
```cmd
python main_simple.py --port 8001
```

### **To check what's running:**
```cmd
netstat -an | findstr 8000
```

### **To stop the backend:**
Press `Ctrl+C` in the terminal

---

## 🌟 **NEXT STEPS**

1. **Test the simplified version** first
2. **Install full dependencies** if you want AI features
3. **Set up the frontend** for a better UI
4. **Explore the database services** that are already running

**Your AI Memory Bank is now functional and ready to use!** 🎉

The simplified version gives you a solid foundation to build upon, and you can gradually add more advanced AI features as needed.