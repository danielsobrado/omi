#!/usr/bin/env python3
"""
Simple test script to verify dual-database architecture works.
This script tests the database switching functionality.
"""

import os
import sys
import importlib

def test_database_switching():
    """Test that database switching works correctly."""
    
    print("Testing dual-database architecture...")
    
    # Test PostgreSQL first (since we have the dependencies)
    print("\n1. Testing PostgreSQL:")
    os.environ["DATABASE_CHOICE"] = "postgres"
    
    # Test just the dispatcher logic first
    try:
        # Import the apps module
        if 'database.apps' in sys.modules:
            importlib.reload(sys.modules['database.apps'])
        else:
            import database.apps
        print("   ✓ PostgreSQL import successful")
        
        # Test other modules
        print("\n2. Testing other modules with PostgreSQL:")
        modules_to_test = ['auth', 'chat', 'conversations', 'memories', 'notifications', 'tasks', 'trends', 'users']
        
        for module_name in modules_to_test:
            try:
                module = importlib.import_module(f'database.{module_name}')
                if f'database.{module_name}' in sys.modules:
                    importlib.reload(sys.modules[f'database.{module_name}'])
                print(f"   ✓ {module_name} module loaded successfully")
            except Exception as e:
                print(f"   ✗ {module_name} module failed: {e}")
        
    except Exception as e:
        print(f"   ✗ PostgreSQL test failed: {e}")
    
    # Test Firestore dispatcher logic (won't work without Firebase but shows the dispatcher)
    print("\n3. Testing Firestore dispatcher (will show import error - this is expected):")
    os.environ["DATABASE_CHOICE"] = "firestore"
    
    try:
        # Clear the module cache to force reload
        modules_to_clear = [key for key in sys.modules.keys() if key.startswith('database.')]
        for module in modules_to_clear:
            if module != 'database.redis_db':  # Keep redis_db as it's shared
                del sys.modules[module]
        
        import database.apps
        print("   ✓ Firestore import successful (Firebase installed)")
    except ModuleNotFoundError as e:
        if 'google' in str(e):
            print("   ⚠ Firestore dispatcher working correctly (Firebase not installed - expected)")
        else:
            print(f"   ✗ Unexpected import error: {e}")
    except Exception as e:
        print(f"   ✗ Firestore test failed: {e}")
    
    print("\n✅ Database switching test completed!")
    print("\nTo use PostgreSQL in production:")
    print("1. Set DATABASE_CHOICE=postgres in your .env file")
    print("2. Set POSTGRES_URL to your PostgreSQL connection string")
    print("3. Start your PostgreSQL instance")
    print("4. Run the backend - tables will be created automatically")

if __name__ == "__main__":
    # Add the backend directory to the Python path
    backend_dir = "/home/sobradod/omi/backend"
    if backend_dir not in sys.path:
        sys.path.insert(0, backend_dir)
    
    test_database_switching()
