"""
Database Seeder: Create Super Admin User

According to DDD, database seeding scripts belong in infrastructure/seeders/
or as standalone utility scripts in a scripts/ folder.

This script creates the super admin user for initial system setup.
"""

import sys
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

from src.shared.auth.application.services.UserService import UserService


def create_super_admin():
    """Create super admin user using DDD services."""
    
    user_service = UserService()
    
    try:
        # Check if admin already exists
        existing_admin = user_service.get_user_by_email("admin@berlin.de")
        if existing_admin:
            print("✅ Super admin already exists!")
            print(f"   Email: {existing_admin['email']}")
            print(f"   Role: {existing_admin['role']}")
            return
        
        # Create super admin
        result = user_service.create_admin(
            email="admin@berlin.de",
            password="123"
        )
        
        if result["success"]:
            print("✅ Super admin created successfully!")
            print(f"   Email: admin@berlin.de")
            print(f"   Password: 123")
            print(f"   Role: super_admin")
            print("\n⚠️  IMPORTANT: Change the default password after first login!")
        else:
            print(f"❌ Failed to create admin: {result.get('message', 'Unknown error')}")
            
    except Exception as e:
        print(f"❌ Error: {str(e)}")
        sys.exit(1)


if __name__ == "__main__":
    create_super_admin()