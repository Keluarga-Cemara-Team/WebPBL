from dataclasses import dataclass
from typing import Optional, Union, Dict, Any
from werkzeug.security import generate_password_hash, check_password_hash

@dataclass
class User:
    """
    Domain Entity User / Administrator (Clean Architecture)
    """
    full_name: str
    email: str
    username: str = ""
    password_hash: str = ""
    role: str = "admin"
    division: str = "Pusat Riset PBL"
    id: Optional[Union[str, int]] = None
    created_at: Optional[str] = None

    def validate(self) -> None:
        if not self.email or "@" not in self.email:
            raise ValueError("Format email tidak valid.")
        if not self.username or not self.username.strip():
            raise ValueError("Username tidak boleh kosong.")
        if not self.full_name or not self.full_name.strip():
            raise ValueError("Nama lengkap tidak boleh kosong.")

    def set_password(self, raw_password: str) -> None:
        if not raw_password or len(raw_password) < 4:
            raise ValueError("Password minimal 4 karakter.")
        self.password_hash = generate_password_hash(raw_password)

    def check_password(self, candidate_password: str) -> bool:
        if not self.password_hash or not candidate_password:
            return False
        return check_password_hash(self.password_hash, candidate_password)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "id": self.id,
            "username": self.username,
            "email": self.email,
            "full_name": self.full_name,
            "role": self.role,
            "division": self.division,
            "created_at": self.created_at
        }
