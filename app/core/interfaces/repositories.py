from abc import ABC, abstractmethod
from typing import List, Optional
from app.core.entities.assessment import RespondentAssessment

class IAssessmentRepository(ABC):
    """
    Port Interface untuk Data Access Layer.
    Domain dan Use Cases tidak peduli apakah penyimpanan menggunakan
    SQLite, PostgreSQL, MySQL, atau In-Memory.
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
    def find_by_id(self, assessment_id: int) -> Optional[RespondentAssessment]:
        """Mencari data responden berdasarkan ID"""
        pass
