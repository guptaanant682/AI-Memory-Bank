#!/usr/bin/env python3
"""
Quick test script to verify Supabase connection
Run this to make sure your credentials are working
"""

import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

def test_supabase_connection():
    """Test Supabase connection and PgVector extension"""
    try:
        from supabase import create_client
        
        # Get credentials from .env
        supabase_url = os.getenv("SUPABASE_URL")
        supabase_key = os.getenv("SUPABASE_KEY")
        
        print(f"🔗 Testing Supabase connection...")
        print(f"📍 URL: {supabase_url}")
        print(f"🔑 Key: {supabase_key[:20]}...")
        
        # Create Supabase client
        supabase = create_client(supabase_url, supabase_key)
        
        # Test connection with a simple query
        result = supabase.from_("information_schema.tables").select("table_name").limit(1).execute()
        
        print("✅ Supabase connection successful!")
        print(f"📊 Database is accessible")
        
        # Test PgVector extension
        try:
            # This will work if PgVector is installed
            result = supabase.rpc("vector_extension_test", {}).execute()
            print("✅ PgVector extension is available!")
        except:
            print("⚠️  PgVector might need to be enabled (that's ok for now)")
        
        return True
        
    except ImportError:
        print("❌ supabase-py not installed. Run: pip install supabase")
        return False
    except Exception as e:
        print(f"❌ Connection failed: {str(e)}")
        print("\n🔧 Troubleshooting:")
        print("1. Check your Supabase URL and key in .env file")
        print("2. Make sure your Supabase project is active")
        print("3. Verify the service_role key (not anon key)")
        return False

if __name__ == "__main__":
    print("🧪 AI Memory Bank - Supabase Connection Test")
    print("=" * 50)
    
    success = test_supabase_connection()
    
    if success:
        print("\n🎉 Ready to start the AI Memory Bank!")
        print("Run: docker-compose up -d")
    else:
        print("\n🔧 Please fix the connection issues first")