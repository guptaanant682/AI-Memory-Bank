#!/usr/bin/env python3
"""
AI Memory Bank Setup Script

This script helps set up the AI Memory Bank project by:
1. Installing Python dependencies
2. Setting up environment variables
3. Downloading required AI models
4. Creating necessary directories
"""

import os
import subprocess
import sys
from pathlib import Path

def run_command(command, description=""):
    """Run a shell command and handle errors"""
    print(f"📦 {description or command}")
    try:
        result = subprocess.run(command, shell=True, check=True, capture_output=True, text=True)
        if result.stdout:
            print(result.stdout)
        return True
    except subprocess.CalledProcessError as e:
        print(f"❌ Error: {e}")
        if e.stderr:
            print(e.stderr)
        return False

def check_python_version():
    """Check if Python version is compatible"""
    version = sys.version_info
    if version.major < 3 or (version.major == 3 and version.minor < 9):
        print("❌ Python 3.9 or higher is required")
        return False
    print(f"✅ Python {version.major}.{version.minor}.{version.micro} detected")
    return True

def setup_backend():
    """Set up the backend environment"""
    print("\n🚀 Setting up Backend...")
    
    backend_dir = Path(__file__).parent.parent / "backend"
    os.chdir(backend_dir)
    
    # Create virtual environment
    if not Path("venv").exists():
        if not run_command("python -m venv venv", "Creating virtual environment"):
            return False
    
    # Activate virtual environment and install dependencies
    if os.name == 'nt':  # Windows
        activate_cmd = r"venv\Scripts\activate && "
    else:  # Unix/macOS
        activate_cmd = "source venv/bin/activate && "
    
    if not run_command(f"{activate_cmd}pip install --upgrade pip", "Upgrading pip"):
        return False
    
    if not run_command(f"{activate_cmd}pip install -r requirements.txt", "Installing Python dependencies"):
        return False
    
    # Download spaCy model
    if not run_command(f"{activate_cmd}python -m spacy download en_core_web_sm", "Downloading spaCy English model"):
        print("⚠️ Warning: spaCy model download failed. Entity extraction may not work.")
    
    # Create necessary directories
    os.makedirs("uploads", exist_ok=True)
    os.makedirs("local_storage", exist_ok=True)
    
    print("✅ Backend setup completed!")
    return True

def setup_frontend():
    """Set up the frontend environment"""
    print("\n🎨 Setting up Frontend...")
    
    frontend_dir = Path(__file__).parent.parent / "frontend"
    os.chdir(frontend_dir)
    
    # Check if Node.js is installed
    try:
        subprocess.run(["node", "--version"], check=True, capture_output=True)
        subprocess.run(["npm", "--version"], check=True, capture_output=True)
        print("✅ Node.js and npm detected")
    except (subprocess.CalledProcessError, FileNotFoundError):
        print("❌ Node.js and npm are required. Please install them first.")
        return False
    
    # Install dependencies
    if not run_command("npm install", "Installing Node.js dependencies"):
        return False
    
    print("✅ Frontend setup completed!")
    return True

def setup_environment():
    """Set up environment variables"""
    print("\n⚙️ Setting up environment...")
    
    env_file = Path(__file__).parent.parent / "backend" / ".env"
    env_example = Path(__file__).parent.parent / "backend" / ".env.example"
    
    if not env_file.exists() and env_example.exists():
        # Copy .env.example to .env
        with open(env_example, 'r') as src, open(env_file, 'w') as dst:
            dst.write(src.read())
        print(f"✅ Created {env_file} from template")
        print("📝 Please edit .env file with your actual API keys and database URLs")
    elif env_file.exists():
        print("✅ .env file already exists")
    else:
        print("⚠️ Warning: No .env.example file found")
    
    return True

def show_next_steps():
    """Show what to do next"""
    print("\n🎉 Setup completed! Here's what to do next:")
    print("\n1. Configure your environment variables:")
    print("   - Edit backend/.env with your API keys")
    print("   - Get Supabase credentials: https://supabase.com")
    print("   - Get Hugging Face token: https://huggingface.co/settings/tokens")
    print("\n2. Start the development servers:")
    print("   Backend:")
    print("     cd backend")
    print("     source venv/bin/activate  # Linux/Mac")
    print("     venv\\Scripts\\activate     # Windows")
    print("     uvicorn main:app --reload")
    print("\n   Frontend:")
    print("     cd frontend")
    print("     npm run dev")
    print("\n3. Open http://localhost:3000 in your browser")
    print("\n📚 For detailed instructions, see the PRD document and README files.")

def main():
    """Main setup function"""
    print("🧠 AI Memory Bank Setup")
    print("=" * 50)
    
    # Check Python version
    if not check_python_version():
        return False
    
    # Setup components
    success = all([
        setup_environment(),
        setup_backend(),
        setup_frontend()
    ])
    
    if success:
        show_next_steps()
        return True
    else:
        print("\n❌ Setup failed. Please check the errors above.")
        return False

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)