from dataclasses import dataclass
from typing import Optional

@dataclass
class User:
    full_name: str
    email: str
    role: str = "employee"
    division: str = "IT"
    id: Optional[str] = None

    def validate(self):
        if not self.email or "@" not in self.email:
            raise ValueError("Format email tidak valid.")