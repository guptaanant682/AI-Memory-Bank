#!/usr/bin/env python3
"""
Install backend dependencies for AI Memory Bank
"""

import subprocess
import sys
import os

def run_pip_install(packages, description=""):
    """Install packages using pip"""
    try:
        print(f"📦 Installing {description}...")
        cmd = [sys.executable, "-m", "pip", "install"] + packages
        result = subprocess.run(cmd, capture_output=True, text=True, check=True)
        print(f"✅ Successfully installed {description}")
        return True
    except subprocess.CalledProcessError as e:
        print(f"❌ Failed to install {description}")
        print(f"Error: {e.stderr}")
        return False

def main():
    print("🚀 AI Memory Bank - Backend Dependencies Installer")
    print("=" * 60)
    
    # Change to backend directory
    backend_dir = "backend"
    if os.path.exists(backend_dir):
        os.chdir(backend_dir)
        print(f"📁 Changed to {os.getcwd()}")
    
    # Core dependencies (install in groups to avoid conflicts)
    core_deps = [
        "fastapi==0.104.1",
        "uvicorn[standard]==0.24.0",
        "python-multipart==0.0.6",
        "python-dotenv==1.0.0",
        "pydantic==2.5.0",
        "aiofiles==23.2.1",
        "requests==2.31.0"
    ]
    
    # Database dependencies
    db_deps = [
        "sqlalchemy==2.0.23",
        "psycopg2-binary==2.9.9",
        "neo4j==5.14.1",
        "supabase==2.3.4"
    ]
    
    # Document processing
    doc_deps = [
        "pypdf==3.17.1",
        "python-docx==1.1.0",
        "pillow==10.1.0"
    ]
    
    # Basic ML (without heavy dependencies initially)
    ml_basic = [
        "numpy==1.24.3",
        "pandas==2.0.3",
        "scikit-learn==1.3.2"
    ]
    
    # Install in phases
    phases = [
        (core_deps, "Core FastAPI dependencies"),
        (db_deps, "Database drivers"),
        (doc_deps, "Document processing"),
        (ml_basic, "Basic ML libraries")
    ]
    
    all_success = True
    for deps, desc in phases:
        if not run_pip_install(deps, desc):
            all_success = False
            print(f"⚠️ Continuing with remaining dependencies...")
    
    # Heavy ML dependencies (optional)
    print("\n🤖 Optional: Heavy AI/ML Dependencies")
    print("These may take a while to install and require significant disk space")
    response = input("Install AI models? (y/n): ").lower().strip()
    
    if response == 'y':
        heavy_ml = [
            "torch==2.1.1",
            "transformers==4.35.2",
            "sentence-transformers==2.2.2",
            "spacy==3.7.2"
        ]
        
        run_pip_install(heavy_ml, "AI/ML models (this may take several minutes)")
        
        # Download spaCy model
        print("📥 Downloading spaCy English model...")
        try:
            subprocess.run([sys.executable, "-m", "spacy", "download", "en_core_web_sm"], 
                         check=True, capture_output=True)
            print("✅ spaCy model downloaded")
        except subprocess.CalledProcessError:
            print("⚠️ Could not download spaCy model (can be done later)")
    
    print("\n🎉 INSTALLATION SUMMARY")
    print("=" * 60)
    
    if all_success:
        print("✅ All core dependencies installed successfully!")
        print("\n🚀 Ready to start the backend:")
        print("   uvicorn main:app --reload --port 8000")
        print("\n🌐 After starting, access:")
        print("   API: http://localhost:8000")
        print("   Docs: http://localhost:8000/docs")
    else:
        print("⚠️ Some dependencies had issues, but you can try starting anyway")
        print("💡 You can install missing packages individually with:")
        print("   pip install <package-name>")
    
    print(f"\n📋 Current directory: {os.getcwd()}")
    print("🔧 If you encounter import errors, install the specific missing package")

if __name__ == "__main__":
    main()