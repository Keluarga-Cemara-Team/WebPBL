from flask import Blueprint, render_template, jsonify, current_app, request
from app.core.use_cases import ImportDatasetUseCase

main_bp = Blueprint("main", __name__)

@main_bp.route("/")
def index():
    """Halaman Utama / Landing Page"""
    db_engine = getattr(current_app, "db_engine_name", "Google Cloud Firestore")
    return render_template("main/index.html", db_engine=db_engine)

@main_bp.route("/dataset-management/")
def dataset_management():
    """Menampilkan halaman frontend Dataset Management."""
    return render_template("dataset_management/index.html")

@main_bp.route("/dataset-management/upload", methods=["POST"])
def upload_dataset():
    """Endpoint untuk menerima file CSV dan menyimpannya ke database"""
    if "file" not in request.files:
        return jsonify({"status": "error", "message": "Tidak ada file yang dikirim."}), 400

    file = request.files["file"]
    if not file or file.filename == "":
        return jsonify({"status": "error", "message": "File belum dipilih."}), 400

    if not file.filename.lower().endswith(".csv"):
        return jsonify({"status": "error", "message": "Format file harus berformat .csv."}), 400

    try:
        repo = current_app.assessment_repository
        import_uc = ImportDatasetUseCase(repo)
        result = import_uc.execute(file.stream, filename=file.filename)

        return jsonify({
            "status": "success",
            "message": f"Berhasil mengimpor {result['imported_count']} baris data ke database ({getattr(current_app, 'db_engine_name', 'Database')}).",
            "data": result
        }), 200
    except ValueError as ve:
        return jsonify({"status": "error", "message": str(ve)}), 400
    except Exception as e:
        return jsonify({"status": "error", "message": f"Terjadi kesalahan saat memproses file: {str(e)}"}), 500

@main_bp.route("/dataset-management/train", methods=["POST"])
def compare_dataset_models():
    """Train and compare classifiers for the dataset currently open in the admin page."""
    payload = request.get_json(silent=True)
    if not isinstance(payload, dict):
        return jsonify({"status": "error", "message": "Payload dataset harus berupa JSON object."}), 400

    try:
        from app.core.use_cases.compare_dataset_models import CompareDatasetModelsUseCase

        result = CompareDatasetModelsUseCase().execute(payload)
        return jsonify({"status": "success", "data": result}), 200
    except ValueError as error:
        return jsonify({"status": "error", "message": str(error)}), 400
    except Exception:
        current_app.logger.exception("Gagal melatih dan membandingkan model klasifikasi.")
        return jsonify({
            "status": "error",
            "message": "Terjadi kesalahan saat melatih model. Periksa log server untuk detail.",
        }), 500

@main_bp.route("/healthz")
def health_check():
    """Endpoint Pemantauan Kesehatan Sistem (Standar Industri Uptime Monitor)"""
    return jsonify({
        "status": "healthy",
        "service": "AntiBurnout-WebPBL",
        "database": getattr(current_app, "db_engine_name", "Google Cloud Firestore"),
        "ml_target": current_app.config.get("ML_API_URL")
    }), 200
