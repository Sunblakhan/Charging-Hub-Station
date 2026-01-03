from dataclasses import dataclass

@dataclass
class User:
    email: str
    password_hash: str
    role: str  # 'user', 'operator', 'admin'
    is_approved: bool = False