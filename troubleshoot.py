#!/usr/bin/env python3
"""
AI Memory Bank Troubleshooting Script
Helps diagnose and fix common issues
"""

import subprocess
import time
import requests
import os

def run_command(command, capture_output=True):
    """Run shell command and return result"""
    try:
        if capture_output:
            result = subprocess.run(command, shell=True, capture_output=True, text=True, timeout=30)
            return result.returncode == 0, result.stdout, result.stderr
        else:
            result = subprocess.run(command, shell=True, timeout=30)
            return result.returncode == 0, "", ""
    except subprocess.TimeoutExpired:
        return False, "", "Command timed out"
    except Exception as e:
        return False, "", str(e)

def check_docker():
    """Check if Docker is installed and running"""
    print("🐳 Checking Docker...")
    
    # Check Docker installation
    success, stdout, stderr = run_command("docker --version")
    if not success:
        print("❌ Docker is not installed or not in PATH")
        print("💡 Install Docker Desktop from https://www.docker.com/products/docker-desktop/")
        return False
    
    print(f"✅ Docker installed: {stdout.strip()}")
    
    # Check Docker is running
    success, stdout, stderr = run_command("docker info")
    if not success:
        print("❌ Docker is not running")
        print("💡 Start Docker Desktop application")
        return False
    
    print("✅ Docker is running")
    
    # Check Docker Compose
    success, stdout, stderr = run_command("docker-compose --version")
    if not success:
        success, stdout, stderr = run_command("docker compose version")
        if not success:
            print("❌ Docker Compose not available")
            return False
    
    print(f"✅ Docker Compose available: {stdout.strip()}")
    return True

def check_services():
    """Check if all services are running"""
    print("\n🔍 Checking Services Status...")
    
    success, stdout, stderr = run_command("docker-compose ps")
    if not success:
        print("❌ Could not check service status")
        print(f"Error: {stderr}")
        return False
    
    print("📊 Service Status:")
    print(stdout)
    
    # Check if services are up
    if "Up" not in stdout:
        print("⚠️  Some services may not be running")
        return False
    
    return True

def check_endpoints():
    """Check if web endpoints are accessible"""
    print("\n🌐 Checking Web Endpoints...")
    
    endpoints = [
        ("Frontend", "http://localhost:3000", "text/html"),
        ("Backend API", "http://localhost:8000/health", "application/json"),
        ("API Docs", "http://localhost:8000/docs", "text/html"),
        ("Neo4j", "http://localhost:7474", "text/html"),
        ("Prometheus", "http://localhost:9090", "text/html")
    ]
    
    results = []
    for name, url, expected_type in endpoints:
        try:
            response = requests.get(url, timeout=10)
            if response.status_code == 200:
                print(f"✅ {name}: {url} - OK")
                results.append(True)
            else:
                print(f"❌ {name}: {url} - HTTP {response.status_code}")
                results.append(False)
        except requests.RequestException as e:
            print(f"❌ {name}: {url} - Not accessible")
            results.append(False)
    
    return all(results)

def check_logs():
    """Check service logs for errors"""
    print("\n📋 Checking Recent Logs...")
    
    services = ["backend", "frontend", "neo4j", "postgres", "redis"]
    
    for service in services:
        print(f"\n--- {service.upper()} LOGS ---")
        success, stdout, stderr = run_command(f"docker-compose logs --tail=5 {service}")
        if success and stdout:
            # Look for common error patterns
            if any(word in stdout.lower() for word in ["error", "failed", "exception", "critical"]):
                print(f"⚠️  {service} has recent errors:")
                print(stdout)
            else:
                print(f"✅ {service} logs look clean")
        else:
            print(f"❌ Could not get {service} logs")

def fix_common_issues():
    """Attempt to fix common issues"""
    print("\n🔧 Attempting Common Fixes...")
    
    # Stop and restart services
    print("1. Restarting all services...")
    run_command("docker-compose down", False)
    time.sleep(5)
    
    success, stdout, stderr = run_command("docker-compose up -d")
    if success:
        print("✅ Services restarted")
    else:
        print(f"❌ Failed to restart services: {stderr}")
        return False
    
    # Wait for services to start
    print("2. Waiting for services to initialize...")
    time.sleep(30)
    
    # Check if fix worked
    if check_endpoints():
        print("✅ Fix successful!")
        return True
    else:
        print("❌ Issues persist")
        return False

def show_quick_commands():
    """Show helpful commands"""
    print("\n💡 HELPFUL COMMANDS:")
    print("=" * 50)
    print("🔍 Check status:           docker-compose ps")
    print("📋 View logs:              docker-compose logs")
    print("🔄 Restart services:       docker-compose restart")
    print("🛑 Stop everything:        docker-compose down")
    print("🚀 Start everything:       docker-compose up -d")
    print("📊 Monitor logs:           docker-compose logs -f")
    print("🔧 Rebuild services:       docker-compose up -d --build")
    print("💾 View disk usage:        docker system df")
    print("🧹 Clean unused data:      docker system prune")

def main():
    print("🛠️  AI Memory Bank - Troubleshoot & Fix")
    print("=" * 60)
    
    # Check Docker
    if not check_docker():
        print("\n❌ Docker issues detected. Please fix Docker installation first.")
        return
    
    # Check if we're in the right directory
    if not os.path.exists("docker-compose.yml"):
        print("❌ docker-compose.yml not found")
        print("💡 Make sure you're in the ai-memory-bank directory")
        return
    
    # Check services
    services_ok = check_services()
    
    # Check endpoints
    endpoints_ok = check_endpoints()
    
    # Check logs if there are issues
    if not services_ok or not endpoints_ok:
        check_logs()
        
        # Ask if user wants to attempt fixes
        print("\n🤔 Would you like me to attempt automatic fixes?")
        response = input("Type 'yes' to proceed with fixes: ").lower().strip()
        
        if response in ['yes', 'y']:
            fix_common_issues()
        else:
            print("⚠️  Please check the issues above manually")
    else:
        print("\n🎉 All systems appear to be working correctly!")
        print("🌐 Access your AI Memory Bank at: http://localhost:3000")
    
    show_quick_commands()
    
    print("\n" + "=" * 60)
    print("🆘 Still having issues?")
    print("1. Check QUICKSTART_GUIDE.md for step-by-step instructions")
    print("2. Review logs: docker-compose logs")
    print("3. Try rebuilding: docker-compose up -d --build")

if __name__ == "__main__":
    main()