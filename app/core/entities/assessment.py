from dataclasses import dataclass, field
from datetime import datetime
from typing import Optional

@dataclass
class RespondentAssessment:
    """
    Domain Entity: Representasi data primer responden dan evaluasi burnout.
    Bersifat murni (Pure Python), tidak terikat framework atau database.
    """
    full_name: str
    role: str
    work_hours: float
    sleep_hours: float
    stress_level: int
    workload_feeling: int
    physical_fatigue: int
    notes: Optional[str] = ""
    id: Optional[int] = None
    burnout_score: Optional[float] = None
    burnout_level: Optional[str] = None
    recommendation: Optional[str] = None
    created_at: datetime = field(default_factory=datetime.now)

    def validate(self) -> None:
        """Memastikan aturan bisnis (domain invariants) terpenuhi"""
        if not self.full_name or len(self.full_name.strip()) < 2:
            raise ValueError("Nama/ID responden minimal 2 karakter.")
        
        if not (1.0 <= self.work_hours <= 24.0):
            raise ValueError("Jam kerja harus berada di antara 1 - 24 jam/hari.")
            
        if not (0.0 <= self.sleep_hours <= 24.0):
            raise ValueError("Jam tidur harus berada di antara 0 - 24 jam/hari.")
            
        if not (1 <= self.stress_level <= 5):
            raise ValueError("Skala stres harus bernilai 1 sampai 5.")
            
        if not (1 <= self.workload_feeling <= 5):
            raise ValueError("Skala beban kerja harus bernilai 1 sampai 5.")
            
        if not (1 <= self.physical_fatigue <= 5):
            raise ValueError("Skala kelelahan fisik harus bernilai 1 sampai 5.")

    def to_dict(self) -> dict:
        """Mengubah entity ke dictionary format data primer"""
        return {
            "id": self.id,
            "full_name": self.full_name,
            "role": self.role,
            "work_hours": self.work_hours,
            "sleep_hours": self.sleep_hours,
            "stress_level": self.stress_level,
            "workload_feeling": self.workload_feeling,
            "physical_fatigue": self.physical_fatigue,
            "notes": self.notes or "",
            "burnout_score": self.burnout_score,
            "burnout_level": self.burnout_level,
            "recommendation": self.recommendation,
            "created_at": self.created_at.strftime("%Y-%m-%d %H:%M:%S") if isinstance(self.created_at, datetime) else str(self.created_at)
        }
