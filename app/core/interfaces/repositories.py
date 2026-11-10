from abc import ABC, abstractmethod
from typing import List, Optional, Any
from app.core.entities.assessment import RespondentAssessment
from app.core.entities.user import User

class IAssessmentRepository(ABC):
    """
    Port Interface untuk Data Access Layer Data Primer Asesmen.
    Domain dan Use Cases tidak peduli apakah penyimpanan menggunakan
    SQLite, PostgreSQL, MySQL, Firestore, atau In-Memory.
    """

    @abstractmethod
    def save(self, assessment: RespondentAssessment) -> RespondentAssessment:
        """Menyimpan record data primer responden ke storage"""
        pass

    @abstractmethod
    def find_all(self) -> List[RespondentAssessment]:
        """Mengambil seluruh data primer responden"""
        pass

    @abstractmethod
    def find_by_id(self, assessment_id: Any) -> Optional[RespondentAssessment]:
        """Mencari data responden berdasarkan ID"""
        pass

    @abstractmethod
    def delete(self, assessment_id: Any) -> bool:
        """Menghapus data responden berdasarkan ID"""
        pass


class IUserRepository(ABC):
    """
    Port Interface untuk Manajemen Akun Pengguna / Administrator.
    """

    @abstractmethod
    def save(self, user: User) -> User:
        """Menyimpan atau memperbarui data akun"""
        pass

    @abstractmethod
    def find_by_id(self, user_id: Any) -> Optional[User]:
        """Mencari user berdasarkan ID"""
        pass

    @abstractmethod
    def find_by_identifier(self, identifier: str) -> Optional[User]:
        """Mencari user berdasarkan username ATAU email"""
        pass

    @abstractmethod
    def find_all(self) -> List[User]:
        """Mengambil seluruh user terdaftar"""
        pass

    @abstractmethod
    def count(self) -> int:
        """Menghitung total user yang tersimpan"""
        pass
