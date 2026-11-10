import io
import re
import math
import logging
from typing import Dict, Any, List, Optional
import pandas as pd
from app.core.entities.assessment import RespondentAssessment
from app.core.interfaces.repositories import IAssessmentRepository
from app.core.interfaces.ml_service import IMLPredictorService

logger = logging.getLogger(__name__)

class ImportDatasetUseCase:
    """
    Use Case: Mengimpor dataset kuesioner dari file Excel (.xlsx, .xls) atau CSV
    ke dalam repository (SQLite / Cloud Firestore).
    Mendukung mapping kolom otomatis, validasi tipe data, inferensi ML jika target kosong,
    serta opsi mode Append atau Replace.
    """

    # Kamus mapping nama kolom file Excel ke atribut RespondentAssessment
    COLUMN_NORMALIZATION_MAP = {
        "personid": "person_id",
        "id": "person_id",
        "idresponden": "person_id",
        "fullname": "full_name",
        "name": "full_name",
        "nama": "full_name",
        "namalengkap": "full_name",
        "age": "age",
        "usia": "age",
        "umur": "age",
        "gender": "gender",
        "jeniskelamin": "gender",
        "jk": "gender",
        "sex": "gender",
        "country": "country",
        "negara": "country",
        "domisili": "country",
        "occupation": "occupation",
        "pekerjaan": "occupation",
        "profesi": "occupation",
        "role": "occupation",
        "jabatan": "occupation",
        "educationlevel": "education_level",
        "education": "education_level",
        "pendidikan": "education_level",
        "employmentstatus": "employment_status",
        "employment": "employment_status",
        "statuskerja": "employment_status",
        "monthlyincomeusd": "monthly_income_usd",
        "income": "monthly_income_usd",
        "pendapatan": "monthly_income_usd",
        "gaji": "monthly_income_usd",
        "workhoursperweek": "work_hours_per_week",
        "workhours": "work_hours_per_week",
        "jamkerja": "work_hours_per_week",
        "jamkerjamingguan": "work_hours_per_week",
        "remotework": "remote_work",
        "remote": "remote_work",
        "kerjaremote": "remote_work",
        "wfh": "remote_work",
        "jobsatisfaction": "job_satisfaction",
        "kepuasankerja": "job_satisfaction",
        "worklifebalance": "work_life_balance",
        "wlb": "work_life_balance",
        "sleephours": "sleep_hours",
        "jamtidur": "sleep_hours",
        "tidur": "sleep_hours",
        "sleepquality": "sleep_quality",
        "kualitastidur": "sleep_quality",
        "stresslevel": "stress_level",
        "tingkatstres": "stress_level",
        "stres": "stress_level",
        "anxietyscore": "anxiety_score",
        "anxiety": "anxiety_score",
        "kecemasan": "anxiety_score",
        "depressionscore": "depression_score",
        "depression": "depression_score",
        "depresi": "depression_score",
        "moodscore": "mood_score",
        "mood": "mood_score",
        "emotionalstability": "emotional_stability",
        "stabilitsemosi": "emotional_stability",
        "physicalactivityhours": "physical_activity_hours",
        "aktivitasfisik": "physical_activity_hours",
        "exercisefrequency": "exercise_frequency",
        "olahraga": "exercise_frequency",
        "meditationminutes": "meditation_minutes",
        "meditasi": "meditation_minutes",
        "screentimehours": "screen_time_hours",
        "screentime": "screen_time_hours",
        "socialmediahours": "social_media_hours",
        "socialmedia": "social_media_hours",
        "medsos": "social_media_hours",
        "gaminghours": "gaming_hours",
        "gaming": "gaming_hours",
        "game": "gaming_hours",
        "coffeecupsperday": "coffee_cups_per_day",
        "coffee": "coffee_cups_per_day",
        "kopi": "coffee_cups_per_day",
        "alcoholconsumption": "alcohol_consumption",
        "alcohol": "alcohol_consumption",
        "alkohol": "alcohol_consumption",
        "smoking": "smoking",
        "merokok": "smoking",
        "rokok": "smoking",
        "healthydiet": "healthy_diet",
        "diet": "healthy_diet",
        "polamakan": "healthy_diet",
        "chronicstress": "chronic_stress",
        "streskronis": "chronic_stress",
        "familyhistorymentalillness": "family_history_mental_illness",
        "riwayatkeluarga": "family_history_mental_illness",
        "therapyattendance": "therapy_attendance",
        "terapi": "therapy_attendance",
        "supportsystem": "support_system",
        "dukungansosial": "support_system",
        "lifesatisfaction": "life_satisfaction",
        "kepuasanhidup": "life_satisfaction",
        "productivityscore": "productivity_score",
        "produktivitas": "productivity_score",
        "absenteeismdays": "absenteeism_days",
        "absen": "absenteeism_days",
        "haritidukerja": "absenteeism_days",
        "burnoutscore": "burnout_score",
        "skorburnout": "burnout_score",
        "burnoutrisk": "burnout_risk",
        "burnoutlevel": "burnout_risk",
        "risikoburnout": "burnout_risk",
        "mentalhealthstatus": "mental_health_status",
        "statuskesehatanmental": "mental_health_status",
        "aiwellnessrecommendation": "ai_wellness_recommendation",
        "recommendation": "ai_wellness_recommendation",
        "rekomendasi": "ai_wellness_recommendation",
        "notes": "notes",
        "catatan": "notes"
    }

    def __init__(self, repository: IAssessmentRepository, ml_service: IMLPredictorService):
        self.repository = repository
        self.ml_service = ml_service

    @staticmethod
    def _normalize_key(key: str) -> str:
        """Menghapus spasi, underscore, simbol, dan lowercase key"""
        return re.sub(r"[^a-zA-Z0-9]", "", str(key).strip().lower())

    @staticmethod
    def _clean_val(val: Any) -> Any:
        """Membersihkan nilai NaN/None dari Pandas"""
        if val is None:
            return None
        if isinstance(val, float) and (math.isnan(val) or math.isinf(val)):
            return None
        if isinstance(val, str):
            s = val.strip()
            return s if s != "" else None
        return val

    def execute(self, file_content: bytes, filename: str, mode: str = "append", auto_predict: bool = True, max_rows: int = 1000) -> Dict[str, Any]:
        """
        Memproses file Excel (.xlsx / .xls) atau CSV.
        Args:
            file_content: bytes dari file yang diunggah
            filename: nama file asli
            mode: 'append' (tambahkan) atau 'replace' (hapus data lama dahulu)
            auto_predict: True jika nilai burnout kosong maka dihitung oleh model ML
            max_rows: batas maksimum baris yang diimpor per eksekusi
        """
        ext = filename.lower().split(".")[-1]
        if ext not in ["xlsx", "xls", "csv"]:
            raise ValueError(f"Ekstensi file .{ext} tidak didukung. Harap unggah file Excel (.xlsx, .xls) atau .csv")

        # 1. Baca DataFrame dari Bytes menggunakan Pandas
        buffer = io.BytesIO(file_content)
        try:
            if ext in ["xlsx", "xls"]:
                df = pd.read_excel(buffer, engine="openpyxl" if ext == "xlsx" else None)
            else:
                # Coba utf-8, fallback ke latin1
                try:
                    df = pd.read_csv(buffer, encoding="utf-8")
                except UnicodeDecodeError:
                    buffer.seek(0)
                    df = pd.read_csv(buffer, encoding="latin1")
        except Exception as e:
            raise ValueError(f"Gagal membaca file {filename}: {str(e)}")

        if df.empty:
            raise ValueError("File Excel/CSV tidak memiliki baris data (kosong).")

        # 2. Pemetaan Kolom File ke Entity Field
        col_map = {}
        for original_col in df.columns:
            norm = self._normalize_key(original_col)
            if norm in self.COLUMN_NORMALIZATION_MAP:
                col_map[original_col] = self.COLUMN_NORMALIZATION_MAP[norm]

        logger.info(f"Importing {len(df)} rows from {filename}. Mapped columns: {col_map}")

        # 3. Handle Mode Replace jika dipilih
        if mode == "replace":
            try:
                existing_records = self.repository.find_all()
                for rec in existing_records:
                    if rec.id:
                        self.repository.delete(rec.id)
            except Exception as e:
                logger.warning(f"Gagal mengosongkan data lama dalam mode replace: {e}")

        # 4. Iterasi Baris Data
        imported_count = 0
        skipped_count = 0
        errors: List[str] = []

        total_to_process = min(len(df), max_rows)

        for idx in range(total_to_process):
            row = df.iloc[idx]
            row_dict = {}

            # Ambil nilai berdasarkan kolom terpetakan
            for orig_col, field_name in col_map.items():
                row_dict[field_name] = self._clean_val(row.get(orig_col))

            # Helper konversi angka aman
            def _num(key, default, cast_fn=float):
                v = row_dict.get(key)
                if v is None:
                    return default
                try:
                    return cast_fn(v)
                except (ValueError, TypeError):
                    return default

            def _str(key, default):
                v = row_dict.get(key)
                return str(v).strip() if v is not None else default

            person_id = _str("person_id", f"PID-IMP-{(idx+1):04d}")
            full_name = _str("full_name", f"Responden #{person_id}")

            try:
                assessment = RespondentAssessment(
                    person_id=person_id,
                    full_name=full_name,
                    age=_num("age", 28.0),
                    gender=_str("gender", "Male"),
                    country=_str("country", "Indonesia"),
                    occupation=_str("occupation", "Software Engineer"),
                    education_level=_str("education_level", "Bachelor"),
                    employment_status=_str("employment_status", "Employed"),
                    monthly_income_usd=_num("monthly_income_usd", 1500.0),
                    remote_work=_str("remote_work", "Hybrid"),
                    work_hours_per_week=_num("work_hours_per_week", 40.0),
                    job_satisfaction=_num("job_satisfaction", 6.0),
                    work_life_balance=_num("work_life_balance", 5.0),
                    productivity_score=_num("productivity_score", 65.0),
                    absenteeism_days=_num("absenteeism_days", 2, cast_fn=int),
                    sleep_hours=_num("sleep_hours", 7.0),
                    sleep_quality=_str("sleep_quality", "Average"),
                    physical_activity_hours=_num("physical_activity_hours", 4.0),
                    exercise_frequency=_str("exercise_frequency", "Weekly"),
                    meditation_minutes=_num("meditation_minutes", 10.0),
                    screen_time_hours=_num("screen_time_hours", 8.0),
                    social_media_hours=_num("social_media_hours", 2.5),
                    gaming_hours=_num("gaming_hours", 1.0),
                    coffee_cups_per_day=_num("coffee_cups_per_day", 2, cast_fn=int),
                    alcohol_consumption=_str("alcohol_consumption", "No"),
                    smoking=_str("smoking", "No"),
                    healthy_diet=_str("healthy_diet", "Yes"),
                    stress_level=_str("stress_level", "Moderate"),
                    chronic_stress=_str("chronic_stress", "No"),
                    anxiety_score=_num("anxiety_score", 35.0),
                    depression_score=_num("depression_score", 30.0),
                    mood_score=_num("mood_score", 60.0),
                    emotional_stability=_num("emotional_stability", 60.0),
                    family_history_mental_illness=_str("family_history_mental_illness", "No"),
                    therapy_attendance=_str("therapy_attendance", "No"),
                    support_system=_str("support_system", "Good"),
                    life_satisfaction=_num("life_satisfaction", 6.0),
                    notes=_str("notes", f"Diimpor dari {filename}")
                )

                # Cek target burnout (apakah sudah ada di Excel atau perlu dihitung ML)
                existing_score = row_dict.get("burnout_score")
                existing_risk = row_dict.get("burnout_risk")

                if existing_score is not None and existing_risk is not None:
                    assessment.burnout_score = float(existing_score)
                    assessment.burnout_risk = str(existing_risk)
                    assessment.mental_health_status = _str("mental_health_status", "Needs Attention")
                    assessment.ai_wellness_recommendation = _str("ai_wellness_recommendation", "Maintain Healthy Routine")
                elif auto_predict:
                    # Jalankan inferensi Machine Learning
                    ml_eval = self.ml_service.predict_burnout(assessment.to_dict())
                    assessment.burnout_score = float(ml_eval.get("burnout_score", 0.0))
                    assessment.burnout_risk = str(ml_eval.get("burnout_risk") or ml_eval.get("burnout_level", "Moderate"))
                    assessment.mental_health_status = str(ml_eval.get("mental_health_status") or "Needs Attention")
                    assessment.ai_wellness_recommendation = str(ml_eval.get("ai_wellness_recommendation") or ml_eval.get("recommendation", "Take Regular Breaks"))

                # Simpan ke repository database
                self.repository.save(assessment)
                imported_count += 1

            except Exception as e:
                skipped_count += 1
                errors.append(f"Baris {idx + 2}: {str(e)}")

        return {
            "total_rows_file": len(df),
            "processed_rows": total_to_process,
            "imported_count": imported_count,
            "skipped_count": skipped_count,
            "mode": mode,
            "filename": filename,
            "mapped_columns_count": len(col_map),
            "errors": errors[:15]
        }

    @classmethod
    def generate_excel_template(cls) -> bytes:
        """
        Menghasilkan file Excel (.xlsx) template resmi dengan 40 kolom
        dan 2 baris data contoh untuk panduan pengisian kuesioner.
        """
        headers = [
            "Person_ID", "Full_Name", "Age", "Gender", "Country", "Occupation",
            "Education_Level", "Employment_Status", "Monthly_Income_USD", "Work_Hours_Per_Week",
            "Remote_Work", "Job_Satisfaction", "Work_Life_Balance", "Sleep_Hours",
            "Sleep_Quality", "Stress_Level", "Anxiety_Score", "Depression_Score",
            "Mood_Score", "Emotional_Stability", "Physical_Activity_Hours", "Exercise_Frequency",
            "Meditation_Minutes", "Screen_Time_Hours", "Social_Media_Hours", "Gaming_Hours",
            "Coffee_Cups_Per_Day", "Alcohol_Consumption", "Smoking", "Healthy_Diet",
            "Chronic_Stress", "Family_History_Mental_Illness", "Therapy_Attendance",
            "Support_System", "Life_Satisfaction", "Productivity_Score", "Absenteeism_Days",
            "Burnout_Score", "Burnout_Risk", "Mental_Health_Status"
        ]

        sample_rows = [
            [
                "PID-1001", "Ahmad Fauzi", 29.0, "Male", "Indonesia", "Software Engineer",
                "Bachelor", "Employed", 1800.0, 48.0, "Hybrid", 6.0, 5.0, 6.5,
                "Average", "Moderate", 45.0, 35.0, 60.0, 65.0, 3.5, "Weekly",
                15.0, 8.5, 2.0, 1.0, 2, "No", "No", "Yes",
                "No", "No", "No", "Good", 6.0, 70.0, 1,
                58.0, "Moderate", "Needs Attention"
            ],
            [
                "PID-1002", "Siti Nurhaliza", 25.0, "Female", "Indonesia", "Data Analyst",
                "Bachelor", "Employed", 1400.0, 40.0, "Yes", 8.0, 8.0, 7.5,
                "Good", "Low", 20.0, 15.0, 85.0, 80.0, 5.0, "Daily",
                20.0, 6.0, 1.5, 0.5, 1, "No", "No", "Yes",
                "No", "No", "No", "Good", 8.0, 85.0, 0,
                24.0, "Low", "Healthy"
            ]
        ]

        df = pd.DataFrame(sample_rows, columns=headers)

        output = io.BytesIO()
        with pd.ExcelWriter(output, engine="openpyxl") as writer:
            df.to_excel(writer, sheet_name="Data Responden", index=False)
            
            # Tambahkan sheet keterangan petunjuk pengisian
            guide_data = {
                "Nama Kolom": ["Person_ID", "Full_Name", "Age", "Gender", "Occupation", "Work_Hours_Per_Week", "Sleep_Hours", "Stress_Level", "Burnout_Score & Risk"],
                "Format / Tipe": ["Teks unik (misal: PID-001)", "Nama responden", "Angka (15 - 100)", "Male / Female / Other", "Profesi / Pekerjaan", "Jam kerja per minggu (0 - 120)", "Jam tidur per hari (0 - 24)", "Low / Moderate / High", "Boleh dikosongkan (akan dihitung otomatis oleh AI/ML AntiBurnout)"]
            }
            pd.DataFrame(guide_data).to_excel(writer, sheet_name="Panduan Pengisian", index=False)

        return output.getvalue()

