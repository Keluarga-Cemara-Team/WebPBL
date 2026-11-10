import csv
import io
import re
from datetime import datetime
from typing import Dict, Any, List, Optional, Union
from app.core.entities.assessment import RespondentAssessment
from app.core.interfaces.repositories import IAssessmentRepository

def _clean_str(val: Any, default: str = "") -> str:
    if val is None:
        return default
    s = str(val).strip()
    return s if s and s.lower() not in ("nan", "null", "none") else default

def _clean_float(val: Any, default: float = 0.0) -> float:
    if val is None:
        return default
    s = str(val).strip()
    if not s or s.lower() in ("nan", "null", "none"):
        return default
    try:
        return float(s)
    except (ValueError, TypeError):
        return default

def _clean_int(val: Any, default: int = 0) -> int:
    if val is None:
        return default
    s = str(val).strip()
    if not s or s.lower() in ("nan", "null", "none"):
        return default
    try:
        return int(float(s))
    except (ValueError, TypeError):
        return default

def _normalize_key(key: str) -> str:
    """Mengubah header kolom seperti 'Person_ID' atau 'Work Hours Per Week' menjadi 'person_id' atau 'work_hours_per_week'"""
    if not key:
        return ""
    # Hapus BOM jika ada
    clean = key.replace("\ufeff", "").strip()
    clean = re.sub(r"[^a-zA-Z0-9_]", "_", clean).lower()
    clean = re.sub(r"_+", "_", clean).strip("_")
    return clean

class ImportDatasetUseCase:
    """
    Use Case: Memproses dan menyimpan dataset CSV ke database.
    Mendukung skema burnout_dataset1.csv (40 kolom) maupun CSV umum.
    """

    def __init__(self, repository: IAssessmentRepository):
        self.repository = repository

    def execute(self, file_source: Any, filename: Optional[str] = None) -> Dict[str, Any]:
        """
        Mengeksekusi pembacaan CSV dan memasukkannya ke database secara batch.
        file_source: bisa berupa file stream (Flask FileStorage.stream), string, bytes, atau io.TextIOBase.
        """
        # 1. Konversi file_source ke TextIO reader
        if isinstance(file_source, bytes):
            text_stream = io.StringIO(file_source.decode("utf-8-sig", errors="replace"))
        elif isinstance(file_source, str):
            text_stream = io.StringIO(file_source)
        elif hasattr(file_source, "read"):
            content = file_source.read()
            if isinstance(content, bytes):
                text_stream = io.StringIO(content.decode("utf-8-sig", errors="replace"))
            else:
                text_stream = io.StringIO(str(content))
        else:
            raise ValueError("Sumber file tidak valid untuk dibaca.")

        reader = csv.reader(text_stream)
        try:
            raw_headers = next(reader)
        except StopIteration:
            raise ValueError("File CSV kosong atau tidak memiliki baris data.")

        # Buat mapping header asli ke header ternormalisasi
        header_map = [_normalize_key(h) for h in raw_headers]
        if not any(header_map):
            raise ValueError("Header kolom CSV tidak terdeteksi.")

        assessments: List[RespondentAssessment] = []
        row_index = 0

        for row in reader:
            if not row or not any(cell.strip() for cell in row):
                continue  # Lewati baris kosong
            row_index += 1

            # Buat dict mapping baris
            row_dict = {}
            for col_idx, val in enumerate(row):
                if col_idx < len(header_map):
                    row_dict[header_map[col_idx]] = val.strip()

            entity = self._map_row_to_entity(row_dict, row_index)
            assessments.append(entity)

        if not assessments:
            raise ValueError("Tidak ada baris data valid yang ditemukan di dalam file CSV.")

        # 2. Simpan ke database menggunakan batch insert
        saved_count = self.repository.bulk_save(assessments)

        return {
            "filename": filename or "dataset.csv",
            "total_rows": len(assessments),
            "imported_count": saved_count,
            "columns_detected": raw_headers
        }

    def _map_row_to_entity(self, d: Dict[str, str], row_num: int) -> RespondentAssessment:
        """Helper untuk memetakan dictionary baris CSV ke RespondentAssessment entity"""
        pid = _clean_str(d.get("person_id") or d.get("id") or d.get("respondent_id") or f"CSV-{row_num:04d}")
        full_name = _clean_str(d.get("full_name") or d.get("nama") or d.get("name") or f"Responden {pid}")

        age = _clean_float(d.get("age") or d.get("umur") or d.get("usia"), 28.0)
        gender = _clean_str(d.get("gender") or d.get("jenis_kelamin"), "Male")
        country = _clean_str(d.get("country") or d.get("negara"), "Indonesia")
        occupation = _clean_str(d.get("occupation") or d.get("pekerjaan") or d.get("role") or d.get("jabatan"), "Software Engineer")
        education_level = _clean_str(d.get("education_level") or d.get("pendidikan"), "Bachelor")
        employment_status = _clean_str(d.get("employment_status") or d.get("status_pekerjaan"), "Employed")
        monthly_income_usd = _clean_float(d.get("monthly_income_usd") or d.get("income") or d.get("gaji"), 1500.0)
        remote_work = _clean_str(d.get("remote_work") or d.get("tipe_kerja"), "Hybrid")

        work_hours = _clean_float(d.get("work_hours_per_week") or d.get("work_hours") or d.get("jam_kerja"), 40.0)
        job_satisfaction = _clean_float(d.get("job_satisfaction") or d.get("kepuasan_kerja"), 6.0)
        work_life_balance = _clean_float(d.get("work_life_balance") or d.get("keseimbangan_hidup"), 5.0)
        productivity_score = _clean_float(d.get("productivity_score") or d.get("produktivitas"), 65.0)
        absenteeism_days = _clean_int(d.get("absenteeism_days") or d.get("absen_hari"), 2)

        sleep_hours = _clean_float(d.get("sleep_hours") or d.get("jam_tidur"), 7.0)
        sleep_quality = _clean_str(d.get("sleep_quality") or d.get("kualitas_tidur"), "Average")
        physical_activity_hours = _clean_float(d.get("physical_activity_hours") or d.get("aktivitas_fisik"), 4.0)
        exercise_frequency = _clean_str(d.get("exercise_frequency") or d.get("frekuensi_olahraga"), "Weekly")
        meditation_minutes = _clean_float(d.get("meditation_minutes") or d.get("meditasi"), 10.0)
        screen_time_hours = _clean_float(d.get("screen_time_hours") or d.get("waktu_layar"), 8.0)
        social_media_hours = _clean_float(d.get("social_media_hours") or d.get("medsos"), 2.5)
        gaming_hours = _clean_float(d.get("gaming_hours") or d.get("game"), 1.0)
        coffee_cups_per_day = _clean_int(d.get("coffee_cups_per_day") or d.get("kopi"), 2)
        alcohol_consumption = _clean_str(d.get("alcohol_consumption") or d.get("alkohol"), "No")
        smoking = _clean_str(d.get("smoking") or d.get("merokok"), "No")
        healthy_diet = _clean_str(d.get("healthy_diet") or d.get("diet_sehat"), "Yes")

        stress_level = _clean_str(d.get("stress_level") or d.get("tingkat_stres"), "Moderate")
        chronic_stress = _clean_str(d.get("chronic_stress") or d.get("stres_kronis"), "No")
        anxiety_score = _clean_float(d.get("anxiety_score") or d.get("skor_cemas"), 35.0)
        depression_score = _clean_float(d.get("depression_score") or d.get("skor_depresi"), 30.0)
        mood_score = _clean_float(d.get("mood_score") or d.get("skor_suasana_hati"), 60.0)
        emotional_stability = _clean_float(d.get("emotional_stability") or d.get("stabilitas_emosi"), 60.0)
        family_history = _clean_str(d.get("family_history_mental_illness") or d.get("riwayat_keluarga"), "No")
        therapy = _clean_str(d.get("therapy_attendance") or d.get("terapi"), "No")
        support_system = _clean_str(d.get("support_system") or d.get("dukungan_sosial"), "Good")
        life_satisfaction = _clean_float(d.get("life_satisfaction") or d.get("kepuasan_hidup"), 6.0)
        notes = _clean_str(d.get("notes") or d.get("catatan"), "")

        raw_score = d.get("burnout_score") or d.get("skor_burnout")
        burnout_score = _clean_float(raw_score, None) if raw_score is not None and str(raw_score).strip() else None

        raw_risk = _clean_str(d.get("burnout_risk") or d.get("burnout_level") or d.get("risiko_burnout"), "")
        if not raw_risk and burnout_score is not None:
            if burnout_score >= 70:
                raw_risk = "High"
            elif burnout_score >= 40:
                raw_risk = "Moderate"
            else:
                raw_risk = "Low"
        elif not raw_risk:
            raw_risk = "Moderate"

        mental_health = _clean_str(d.get("mental_health_status") or d.get("status_kesehatan_mental"), "")
        if not mental_health:
            if raw_risk.lower() in ("high", "tinggi", "critical"):
                mental_health = "Critical"
            elif raw_risk.lower() in ("low", "rendah", "healthy"):
                mental_health = "Healthy"
            else:
                mental_health = "Needs Attention"

        recommendation = _clean_str(
            d.get("ai_wellness_recommendation") or d.get("recommendation") or d.get("rekomendasi"),
            "Maintain Healthy Routine"
        )

        return RespondentAssessment(
            person_id=pid,
            full_name=full_name,
            age=age,
            gender=gender,
            country=country,
            occupation=occupation,
            education_level=education_level,
            employment_status=employment_status,
            monthly_income_usd=monthly_income_usd,
            remote_work=remote_work,
            work_hours_per_week=work_hours,
            job_satisfaction=job_satisfaction,
            work_life_balance=work_life_balance,
            productivity_score=productivity_score,
            absenteeism_days=absenteeism_days,
            sleep_hours=sleep_hours,
            sleep_quality=sleep_quality,
            physical_activity_hours=physical_activity_hours,
            exercise_frequency=exercise_frequency,
            meditation_minutes=meditation_minutes,
            screen_time_hours=screen_time_hours,
            social_media_hours=social_media_hours,
            gaming_hours=gaming_hours,
            coffee_cups_per_day=coffee_cups_per_day,
            alcohol_consumption=alcohol_consumption,
            smoking=smoking,
            healthy_diet=healthy_diet,
            stress_level=stress_level,
            chronic_stress=chronic_stress,
            anxiety_score=anxiety_score,
            depression_score=depression_score,
            mood_score=mood_score,
            emotional_stability=emotional_stability,
            family_history_mental_illness=family_history,
            therapy_attendance=therapy,
            support_system=support_system,
            life_satisfaction=life_satisfaction,
            notes=notes,
            burnout_score=burnout_score,
            burnout_risk=raw_risk,
            mental_health_status=mental_health,
            ai_wellness_recommendation=recommendation,
            created_at=datetime.now()
        )

