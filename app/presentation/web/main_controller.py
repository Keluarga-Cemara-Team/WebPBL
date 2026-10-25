from flask import Blueprint, render_template, jsonify, current_app

main_bp = Blueprint("main", __name__)

@main_bp.route("/")
def index():
    """Halaman Utama / Landing Page"""
    return render_template("main/index.html")

@main_bp.route("/dataset-management/")
def dataset_management():
    """Menampilkan halaman frontend Dataset Management."""
    return render_template("dataset_management/index.html")

@main_bp.route("/healthz")
def health_check():
    """Endpoint Pemantauan Kesehatan Sistem (Standar Industri Uptime Monitor)"""
    return jsonify({
        "status": "healthy",
        "service": "AntiBurnout-WebPBL",
        "ml_target": current_app.config.get("ML_API_URL")
    }), 200
