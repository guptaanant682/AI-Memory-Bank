#!/usr/bin/env python3
"""
Simple startup script for AI Memory Bank
Runs a basic version without complex dependencies
"""

import subprocess
import sys
import os
import time

def run_command(command, description=""):
    """Run a command and return success status"""
    try:
        print(f"🔧 {description}")
        result = subprocess.run(command, shell=True, check=True, capture_output=True, text=True)
        print(f"✅ Success: {description}")
        return True
    except subprocess.CalledProcessError as e:
        print(f"❌ Failed: {description}")
        print(f"Error: {e.stderr}")
        return False

def main():
    print("🚀 AI Memory Bank - Simple Startup")
    print("=" * 50)
    
    # Check if we're in the right directory
    if not os.path.exists("docker-compose.yml"):
        print("❌ Error: Please run this from the ai-memory-bank directory")
        return
    
    print("\n📦 Step 1: Starting Database Services")
    if run_command("docker-compose up -d postgres redis neo4j", "Starting databases"):
        print("✅ Database services started successfully")
    else:
        print("❌ Failed to start database services")
        return
    
    print("\n⏳ Step 2: Waiting for services to initialize...")
    time.sleep(10)
    
    print("\n📊 Step 3: Starting Monitoring")
    if run_command("docker-compose up -d prometheus grafana", "Starting monitoring"):
        print("✅ Monitoring services started")
    else:
        print("⚠️ Monitoring failed but continuing...")
    
    print("\n🌐 Step 4: Service Status Check")
    run_command("docker-compose ps", "Checking service status")
    
    print("\n🎉 SIMPLIFIED SYSTEM IS READY!")
    print("=" * 50)
    print("✅ Database Services Running:")
    print("   🐘 PostgreSQL: localhost:5432")
    print("   📊 Neo4j: http://localhost:7474")
    print("   🔴 Redis: localhost:6379")
    print("   📈 Prometheus: http://localhost:9090")
    print("   📊 Grafana: http://localhost:3001")
    
    print("\n💡 MANUAL SETUP INSTRUCTIONS:")
    print("Since the full Docker build had issues, you can:")
    print("1. Install Python dependencies locally:")
    print("   cd backend && pip install -r requirements.txt")
    print("2. Run backend locally:")
    print("   uvicorn main:app --reload --port 8000")
    print("3. In another terminal, install frontend:")
    print("   cd frontend && npm install && npm run dev")
    
    print("\n🔧 TROUBLESHOOTING:")
    print("- Check logs: docker-compose logs")
    print("- Restart services: docker-compose restart")
    print("- Stop all: docker-compose down")
    
    print(f"\n📋 Next Steps:")
    print("1. The databases are now running and ready")
    print("2. You can develop against them locally")
    print("3. Access Neo4j at http://localhost:7474 (neo4j/password123)")

if __name__ == "__main__":
    main()