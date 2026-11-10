from typing import Tuple, Optional
from app.core.entities.user import User
from app.core.interfaces.repositories import IUserRepository

class LoginAdminUseCase:
    """
    Use Case Autentikasi Masuk Administrator (Clean Architecture).
    Mengecek kredensial akun terhadap repository, memverifikasi kecocokan
    password hash, dan memvalidasi hak akses role administrator.
    """

    def __init__(self, user_repo: IUserRepository):
        self.user_repo = user_repo

    def execute(self, identifier: str, password: str) -> Tuple[Optional[User], Optional[str]]:
        if not identifier or not identifier.strip():
            return None, "Username atau email harus diisi."
        
        if not password or not password.strip():
            return None, "Kata sandi harus diisi."

        user = self.user_repo.find_by_identifier(identifier.strip())
        if not user:
            return None, "Akun administrator tidak ditemukan. Periksa kembali username atau email Anda."

        if not user.check_password(password):
            return None, "Kata sandi yang Anda masukkan salah."

        if user.role != "admin":
            return None, "Akses ditolak: Akun ini tidak memiliki hak akses administrator."

        return user, None
