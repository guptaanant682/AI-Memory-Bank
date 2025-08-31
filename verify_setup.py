#!/usr/bin/env python3
"""
Simple setup verification without external dependencies
"""

import os
import re

def check_env_file():
    """Check if .env file has all required credentials"""
    env_path = ".env"
    
    if not os.path.exists(env_path):
        return False, "❌ .env file not found"
    
    try:
        with open(env_path, 'r') as f:
            content = f.read()
        
        checks = {
            "Supabase URL": r'SUPABASE_URL=https://\w+\.supabase\.co',
            "Supabase Key": r'SUPABASE_KEY=eyJ[\w\-\.]+',
            "Hugging Face Token": r'HUGGINGFACE_API_TOKEN=hf_\w+',
            "Slack Bot Token": r'SLACK_BOT_TOKEN=xoxb-[\d\-\w]+',
            "Slack Channel ID": r'SLACK_CHANNEL_ID=C\w+'
        }
        
        results = {}
        for name, pattern in checks.items():
            if re.search(pattern, content):
                results[name] = "✅ Configured"
            else:
                results[name] = "❌ Missing or invalid"
        
        return True, results
        
    except Exception as e:
        return False, f"❌ Error reading .env: {str(e)}"

def check_project_structure():
    """Check if all key project files exist"""
    key_files = [
        "backend/main.py",
        "backend/services/document_processor.py",
        "backend/services/ai_learning_agent.py",
        "frontend/package.json",
        "frontend/src/app/page.tsx",
        "docker-compose.yml",
        "README.md"
    ]
    
    results = {}
    for file_path in key_files:
        if os.path.exists(file_path):
            results[file_path] = "✅ Present"
        else:
            results[file_path] = "❌ Missing"
    
    return results

def main():
    print("🧪 AI Memory Bank - Setup Verification")
    print("=" * 60)
    print()
    
    # Check environment configuration
    print("📋 Environment Configuration Check")
    print("-" * 40)
    env_ok, env_results = check_env_file()
    
    if env_ok:
        for item, status in env_results.items():
            print(f"{status} {item}")
        
        all_configured = all("✅" in status for status in env_results.values())
    else:
        print(env_results)
        all_configured = False
    
    print()
    
    # Check project structure
    print("📋 Project Structure Check")
    print("-" * 40)
    structure_results = check_project_structure()
    
    for file_path, status in structure_results.items():
        print(f"{status} {file_path}")
    
    all_files_present = all("✅" in status for status in structure_results.values())
    
    print()
    
    # Summary
    print("📋 SETUP VERIFICATION SUMMARY")
    print("=" * 60)
    
    if all_configured and all_files_present:
        print("🎉 SYSTEM FULLY CONFIGURED AND READY!")
        print()
        print("🚀 To launch your AI Memory Bank:")
        print("1. Install Docker and Docker Compose")
        print("2. Run: docker-compose up -d")
        print("3. Wait for services to start (2-3 minutes)")
        print("4. Access: http://localhost:3000")
        print()
        print("✨ FEATURES READY TO USE:")
        print("   📄 Upload documents (PDF, DOC, TXT, MD)")
        print("   🎵 Process audio files (MP3, WAV, M4A)")
        print("   🖼️  Analyze images (JPG, PNG, GIF)")
        print("   🔍 Ask questions about your content")
        print("   🕸️  Explore knowledge relationships")
        print("   🧠 Get AI learning insights")
        print("   👥 Collaborate with others")
        print("   📊 View analytics and trends")
        print("   ⚡ Real-time Slack integration")
        print()
    else:
        print("⚠️  Setup Issues Found:")
        if not all_configured:
            print("   🔧 Some API credentials need configuration")
        if not all_files_present:
            print("   📁 Some project files are missing")
        print()
        print("💡 Check the issues above and re-run this script")
    
    print("🔧 Need help? Check README.md or SETUP.md")

if __name__ == "__main__":
    main()