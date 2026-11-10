from pathlib import Path
from flask import Flask, request, redirect, url_for, session, flash
from app.config import config_by_name

# Import Infrastructure implementations
from app.infrastructure.db.sqlite_client import SQLiteClient
from app.infrastructure.repositories.sqlite_assessment_repo import SQLiteAssessmentRepository
from app.infrastructure.repositories.sqlite_user_repo import SQLiteUserRepository
from app.infrastructure.external.http_ml_service import HttpMLPredictorService

def create_app(config_name="development"):
    """
    Application Factory Pattern dengan Dependency Injection (Clean Architecture)
    Mendukung Cloud Firestore (Firebase) dengan fallback ke SQLite lokal.
    Menerapkan perlindungan sesi Autentikasi Administrator sebelum akses halaman portal.
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

            # Pastikan akun admin default tersedia di Firestore
            try:
                if not user_repo.find_by_identifier("admin"):
                    from werkzeug.security import generate_password_hash
                    from app.core.entities.user import User
                    user_repo.save(User(
                        username="admin",
                        email="admin@antiburnout.com",
                        password_hash=generate_password_hash("admin123"),
                        full_name="Administrator PBL",
                        role="admin",
                        division="Pusat Riset PBL"
                    ))
                    print(">> [Database] Akun administrator default berhasil di-seed ke Cloud Firestore")
            except Exception as e:
                print(f">> [Database Notice] Pemeriksaan seed admin Firestore: {e}")

            app.db_engine_name = "Google Cloud Firestore (Firebase)"
            has_firebase = True
            print(">> [Database] Terhubung ke Google Cloud Firestore (Firebase)")
        except Exception as e:
            print(f">> [Database Warning] Gagal inisialisasi Firebase: {e}. Fallback ke SQLite.")

    if not has_firebase:
        sqlite_client = SQLiteClient(app.config["DB_PATH"])
        assessment_repo = SQLiteAssessmentRepository(sqlite_client)
        user_repo = SQLiteUserRepository(sqlite_client)
        app.sqlite_client = sqlite_client
        app.db_engine_name = "Local SQLite Engine"
        
        # Pengecekan status tabel database dan akun administrator
        db_status = sqlite_client.inspect_database()
        print(f">> [Database Checked] Engine: SQLite ({db_status['db_path']})")
        print(f">> [Database Checked] Tabel aktif: {db_status['tables']}")
        if db_status.get("default_admin"):
            admin_info = db_status["default_admin"]
            print(f">> [Database Checked] Akun Admin siap: {admin_info['username']} ({admin_info['email']})")

    # Inisialisasi Service ML
    ml_service = HttpMLPredictorService(app.config["ML_API_URL"])

    # 2. Dependency Injection: Pasang ke app context untuk diakses Controller
    app.assessment_repository = assessment_repo
    app.user_repository = user_repo
    app.ml_service = ml_service

    # 3. Registrasi Presentation Layer Blueprints
    from app.presentation.web.auth_controller import auth_bp
    from app.presentation.web.main_controller import main_bp
    from app.presentation.web.assessment_controller import assessment_bp
    from app.presentation.web.user_controller import user_bp

    app.register_blueprint(auth_bp)
    app.register_blueprint(main_bp)
    app.register_blueprint(assessment_bp, url_prefix="/assessment")
    app.register_blueprint(user_bp, url_prefix="/users")

    # 4. Filter Autentikasi Global: Wajib Login Sebelum Masuk Portal Admin
    @app.before_request
    def enforce_admin_authentication():
        """
        Memastikan pengguna telah login sebagai admin sebelum dapat mengakses
        seluruh fitur dashboard, data entry, dataset management, dan tabel assessments.
        """
        endpoint = request.endpoint or ""
        path = request.path or ""

        # Bebaskan akses ke aset statis (CSS, JS, Fonts, Images)
        if path.startswith("/static"):
            return None

        # Bebaskan endpoint login & logout
        if endpoint.startswith("auth.") or path.startswith("/login") or path.startswith("/logout"):
            return None

        # Bebaskan uptime health check untuk monitoring external
        if endpoint == "main.health_check" or path == "/healthz":
            return None

        # Periksa apakah sesi login administrator aktif
        if not session.get("logged_in"):
            # Jika akses via browser, arahkan ke login dengan parameter next URL
            flash("Silakan masuk (login) terlebih dahulu untuk mengakses Admin Portal.", "warning")
            return redirect(url_for("auth.login", next=request.full_path if request.query_string else request.path))

        return None

    # 5. Injeksi Data Sesi Admin ke Seluruh Template Jinja2
    @app.context_processor
    def inject_auth_context():
        return {
            "current_user": {
                "id": session.get("user_id"),
                "username": session.get("username", "admin"),
                "full_name": session.get("user_name", "Administrator PBL"),
                "email": session.get("user_email", "admin@antiburnout.com"),
                "role": session.get("user_role", "admin"),
                "is_authenticated": bool(session.get("logged_in"))
            }
        }

    return app
