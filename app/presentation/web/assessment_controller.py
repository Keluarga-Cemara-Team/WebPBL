from flask import Blueprint, render_template, request, Response, redirect, url_for, flash, jsonify, current_app
from app.core.use_cases import SubmitAssessmentUseCase, ExportDatasetUseCase, GetAssessmentHistoryUseCase

assessment_bp = Blueprint("assessment", __name__)

def _get_use_cases():
    """Helper untuk mengambil instances use case yang sudah di-inject ke current_app"""
    repo = current_app.assessment_repository
    ml_svc = current_app.ml_service
    return (
        SubmitAssessmentUseCase(repo, ml_svc),
        ExportDatasetUseCase(repo),
        GetAssessmentHistoryUseCase(repo)
    )

@assessment_bp.route("/", methods=["GET"])
def form():
    """Menampilkan form input kuesioner data primer"""
    return render_template("assessment/form.html")

@assessment_bp.route("/submit", methods=["POST"])
def submit():
    """Memproses submission form data primer menggunakan Clean Architecture Use Case"""
    submit_uc, _, _ = _get_use_cases()

    raw_data = {
        "full_name": request.form.get("full_name"),
        "role": request.form.get("role"),
        "work_hours": request.form.get("work_hours"),
        "sleep_hours": request.form.get("sleep_hours"),
        "stress_level": request.form.get("stress_level"),
        "workload_feeling": request.form.get("workload_feeling"),
        "physical_fatigue": request.form.get("physical_fatigue"),
        "notes": request.form.get("notes")
    }

    try:
        saved_entity, ml_result = submit_uc.execute(raw_data)
        return render_template(
            "assessment/result.html",
            user=saved_entity.to_dict(),
            result=ml_result
        )
    except ValueError as e:
        flash(str(e), "danger")
        return redirect(url_for("assessment.form"))

@assessment_bp.route("/dataset", methods=["GET"])
def dataset_view():
    """Halaman tabel data primer yang terkumpul beserta metrik ringkas"""
    _, _, history_uc = _get_use_cases()
    data = history_uc.execute()
    return render_template(
        "assessment/dataset.html",
        records=data["assessments"],
        metrics=data["metrics"]
    )

@assessment_bp.route("/export/csv", methods=["GET"])
def export_csv():
    """Download data primer dalam format CSV (dapat langsung diserahkan ke tim MachineLearningPBL)"""
    _, export_uc, _ = _get_use_cases()
    csv_content = export_uc.execute()
    
    return Response(
        csv_content,
        mimetype="text/csv",
        headers={"Content-Disposition": "attachment;filename=primary_burnout_dataset.csv"}
    )

@assessment_bp.route("/api/predict", methods=["POST"])
def api_predict():
    """API endpoint JSON jika dipanggil dari aplikasi luar atau AJAX"""
    submit_uc, _, _ = _get_use_cases()
    payload = request.get_json(silent=True) or request.form.to_dict()

    try:
        saved_entity, ml_result = submit_uc.execute(payload)
        return jsonify({
            "status": "success",
            "data": saved_entity.to_dict(),
            "evaluation": ml_result
        }), 201
    except ValueError as e:
        return jsonify({"status": "error", "message": str(e)}), 400
