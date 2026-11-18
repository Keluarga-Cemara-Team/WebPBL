import os
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent

class Config:
    """Konfigurasi dasar WebPBL Clean Architecture"""
    SECRET_KEY = os.getenv("SECRET_KEY", "antiburnout-clean-architecture-secret-2024")
    
    # URL Endpoint Machine Learning (berada di subrepo MachineLearningPBL)
    ML_API_URL = os.getenv("ML_API_URL", "http://127.0.0.1:8000/predict")
    
    # Penyimpanan Database Lokal (SQLite)
    DATA_DIR = BASE_DIR / "data"
    DB_PATH = DATA_DIR / "antiburnout.db"

    # Penyimpanan Pipeline Model Final & Metadata (Poin 5)
    FINAL_MODEL_DIR = DATA_DIR / "final_model"
    FINAL_MODEL_PIPELINE_PATH = FINAL_MODEL_DIR / "pipeline.joblib"
    FINAL_MODEL_METADATA_PATH = FINAL_MODEL_DIR / "metadata.json"

    # Firebase Cloud Firestore Credentials
    FIREBASE_CREDENTIALS_PATH = BASE_DIR / "serviceAccountKey.json"

class DevelopmentConfig(Config):
    DEBUG = True
    TESTING = False

class ProductionConfig(Config):
    DEBUG = False
    TESTING = False

config_by_name = {
    "development": DevelopmentConfig,
    "production": ProductionConfig,
    "default": DevelopmentConfig,
}
