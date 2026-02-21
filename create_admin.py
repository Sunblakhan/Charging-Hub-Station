import sys
from pathlib import Path

project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

from src.shared.auth.application.services.AuthService import AuthService
from src.shared.auth.infrastructure.repositories.UserRepository import SqliteUserRepository


def create_super_admin():
    """Create super admin user using DDD services."""

    user_repo = SqliteUserRepository()
    auth_service = AuthService(user_repo)

    try:
        result = auth_service.signup(
            email_str="admin@berlin.de",
            plain_password="123",
            role_str="admin"
        )
        print("✅ Super admin created successfully!")
        print(f"   Email: admin@berlin.de")
        print(f"   Password: 123")
        print("\n⚠️  IMPORTANT: Change the default password after first login!")

    except Exception as e:
        print(f"❌ Error: {str(e)}")
        sys.exit(1)


if __name__ == "__main__":
    create_super_admin()