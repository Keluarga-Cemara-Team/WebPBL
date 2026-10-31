from pathlib import Path
from flask import Flask
from app.config import config_by_name

# Import Infrastructure implementations
from app.infrastructure.db.sqlite_client import SQLiteClient
from app.infrastructure.repositories.sqlite_assessment_repo import SQLiteAssessmentRepository
from app.infrastructure.external.http_ml_service import HttpMLPredictorService

def create_app(config_name="development"):
    """
    Application Factory Pattern dengan Dependency Injection (Clean Architecture)
    Mendukung Cloud Firestore (Firebase) dengan fallback ke SQLite lokal.
    """
    current_dir = Path(__file__).resolve().parent

    app = Flask(
        __name__,
        template_folder=str(current_dir / "presentation" / "templates"),
        static_folder=str(current_dir / "presentation" / "static")
    )
    
    config_obj = config_by_name.get(config_name, config_by_name["default"])
    app.config.from_object(config_obj)

    # 1. Inisialisasi Database (Prioritas: Firebase Cloud Firestore -> Fallback: SQLite)
    firebase_cred = app.config.get("FIREBASE_CREDENTIALS_PATH")
    has_firebase = False

    if firebase_cred and (firebase_cred.exists() or list(firebase_cred.parent.glob("*firebase-adminsdk*.json"))):
        try:
            from app.infrastructure.db.firebase_client import FirebaseClient
            from app.infrastructure.repositories.firestore_assessment_repo import FirestoreAssessmentRepository
            from app.infrastructure.repositories.firestore_user_repo import FirestoreUserRepository

            firebase_client = FirebaseClient(firebase_cred)
            assessment_repo = FirestoreAssessmentRepository(firebase_client)
            user_repo = FirestoreUserRepository(firebase_client)

            app.db_engine_name = "Google Cloud Firestore (Firebase)"
            has_firebase = True
            print(">> [Database] Terhubung ke Google Cloud Firestore (Firebase)")
        except Exception as e:
            print(f">> [Database Warning] Gagal inisialisasi Firebase: {e}. Fallback ke SQLite.")

    if not has_firebase:
        sqlite_client = SQLiteClient(app.config["DB_PATH"])
        assessment_repo = SQLiteAssessmentRepository(sqlite_client)
        user_repo = None
        app.db_engine_name = "Local SQLite Engine"
        print(">> [Database] Terhubung ke SQLite Engine")

    # Inisialisasi Service ML
    ml_service = HttpMLPredictorService(app.config["ML_API_URL"])

    # 2. Dependency Injection: Pasang ke app context untuk diakses Controller
    app.assessment_repository = assessment_repo
    app.user_repository = user_repo
    app.ml_service = ml_service

    # 3. Registrasi Presentation Layer Blueprints
    from app.presentation.web.main_controller import main_bp
    from app.presentation.web.assessment_controller import assessment_bp
    from app.presentation.web.user_controller import user_bp

    app.register_blueprint(main_bp)
    app.register_blueprint(assessment_bp, url_prefix="/assessment")
    app.register_blueprint(user_bp, url_prefix="/users")
    
    return app
