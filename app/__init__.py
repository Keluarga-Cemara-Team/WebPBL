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
    """
    current_dir = Path(__file__).resolve().parent

    # Tentukan template_folder dan static_folder ke layer Presentation
    app = Flask(
        __name__,
        template_folder=str(current_dir / "presentation" / "templates"),
        static_folder=str(current_dir / "presentation" / "static")
    )
    
    config_obj = config_by_name.get(config_name, config_by_name["default"])
    app.config.from_object(config_obj)

    # 1. Inisialisasi Infrastruktur (DB & External Service)
    sqlite_client = SQLiteClient(app.config["DB_PATH"])
    assessment_repo = SQLiteAssessmentRepository(sqlite_client)
    ml_service = HttpMLPredictorService(app.config["ML_API_URL"])

    # 2. Dependency Injection: Pasang ke app context untuk diakses Controller
    app.assessment_repository = assessment_repo
    app.ml_service = ml_service

    # 3. Registrasi Presentation Layer Blueprints
    from app.presentation.web.main_controller import main_bp
    from app.presentation.web.assessment_controller import assessment_bp

    app.register_blueprint(main_bp)
    app.register_blueprint(assessment_bp, url_prefix="/assessment")

    return app
