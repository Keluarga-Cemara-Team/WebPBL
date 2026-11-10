from flask import Blueprint, render_template, request, Response, redirect, url_for, flash, jsonify, current_app
from app.core.use_cases import (
    SubmitAssessmentUseCase,
    ExportDatasetUseCase,
    GetAssessmentHistoryUseCase,
    ImportDatasetUseCase
)

assessment_bp = Blueprint("assessment", __name__)

def _get_use_cases():
    """Helper untuk mengambil instances use case yang sudah di-inject ke current_app"""
    repo = current_app.assessment_repository
    ml_svc = current_app.ml_service
    return (
        SubmitAssessmentUseCase(repo, ml_svc),
        ExportDatasetUseCase(repo),
        GetAssessmentHistoryUseCase(repo),
        ImportDatasetUseCase(repo, ml_svc)
    )

@assessment_bp.route("/", methods=["GET"])
def form():
    """Menampilkan form input kuesioner data primer lengkap (40 kolom dataset)"""
    return render_template("assessment/form.html")

@assessment_bp.route("/submit", methods=["POST"])
def submit():
    """Memproses submission form data primer menggunakan Clean Architecture Use Case"""
    submit_uc, _, _, _ = _get_use_cases()

    # Ambil seluruh atribut dari input form
    raw_data = request.form.to_dict()

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
    _, _, history_uc, _ = _get_use_cases()
    data = history_uc.execute()
    return render_template(
        "assessment/dataset.html",
        records=data["assessments"],
        metrics=data["metrics"]
    )

@assessment_bp.route("/detail/<assessment_id>", methods=["GET"])
def detail(assessment_id):
    """Menampilkan rincian lengkap 40 atribut responden beserta evaluasi burnout"""
    repo = current_app.assessment_repository
    entity = repo.find_by_id(assessment_id)
    if not entity:
        flash(f"Data responden #{assessment_id} tidak ditemukan.", "danger")
        return redirect(url_for("assessment.dataset_view"))
    return render_template("assessment/detail.html", item=entity.to_dict())

@assessment_bp.route("/delete/<assessment_id>", methods=["POST"])
def delete_item(assessment_id):
    """Menghapus satu baris data responden berdasarkan ID"""
    repo = current_app.assessment_repository
    success = repo.delete(assessment_id)
    if success:
        flash(f"Data responden #{assessment_id} berhasil dihapus dari database.", "success")
    else:
        flash(f"Gagal menghapus data responden #{assessment_id}.", "danger")
    return redirect(url_for("assessment.dataset_view"))

@assessment_bp.route("/delete-batch", methods=["POST"])
def delete_batch():
    """Menghapus beberapa baris data sekaligus (Bulk Delete)"""
    repo = current_app.assessment_repository
    selected_ids = request.form.getlist("selected_id[]")
    if not selected_ids:
        flash("Tidak ada baris data yang dipilih untuk dihapus.", "warning")
        return redirect(url_for("assessment.dataset_view"))

    deleted_count = 0
    for aid in selected_ids:
        if repo.delete(aid):
            deleted_count += 1

    flash(f"Berhasil menghapus {deleted_count} baris data responden terpilih.", "success")
    return redirect(url_for("assessment.dataset_view"))

@assessment_bp.route("/export/csv", methods=["GET"])
def export_csv():
    """Download data primer dalam format CSV (persis format mental_health_burnout_prediction_dataset.csv)"""
    _, export_uc, _, _ = _get_use_cases()
    csv_content = export_uc.execute()

    return Response(
        csv_content,
        mimetype="text/csv",
        headers={"Content-Disposition": "attachment;filename=mental_health_burnout_primary_dataset.csv"}
    )

@assessment_bp.route("/import", methods=["GET"])
def import_view():
    """Halaman Import Dataset dari file Excel (.xlsx / .xls) atau CSV (Tampilan Klasik phpMyAdmin)"""
    return render_template("assessment/import.html")

@assessment_bp.route("/import", methods=["POST"])
def import_process():
    """Memproses file Excel / CSV yang diunggah untuk disimpan ke database"""
    _, _, _, import_uc = _get_use_cases()

    uploaded_file = request.files.get("dataset_file")
    if not uploaded_file or not uploaded_file.filename:
        flash("Silakan pilih file Excel (.xlsx, .xls) atau CSV terlebih dahulu.", "warning")
        return redirect(url_for("assessment.import_view"))

    mode = request.form.get("mode", "append")
    auto_predict = request.form.get("auto_predict", "1") == "1"

    try:
        file_bytes = uploaded_file.read()
        filename = uploaded_file.filename

        result = import_uc.execute(
            file_content=file_bytes,
            filename=filename,
            mode=mode,
            auto_predict=auto_predict
        )

        msg = (
            f"Import Berhasil! Sebanyak {result['imported_count']} baris data responden "
            f"dari file '{filename}' berhasil dimasukkan ke database "
            f"(Mode: {'Tambah / Append' if mode == 'append' else 'Ganti / Replace'})."
        )
        flash(msg, "success")

        if result["skipped_count"] > 0:
            flash(
                f"{result['skipped_count']} baris data dilewati karena format tidak sesuai: "
                + "; ".join(result["errors"][:5]),
                "warning"
            )

        return redirect(url_for("assessment.dataset_view"))

    except ValueError as ve:
        flash(f"Gagal memproses file: {str(ve)}", "danger")
        return redirect(url_for("assessment.import_view"))
    except Exception as e:
        flash(f"Terjadi kesalahan saat import dataset: {str(e)}", "danger")
        return redirect(url_for("assessment.import_view"))

@assessment_bp.route("/import/template", methods=["GET"])
def download_template():
    """Download template file Excel (.xlsx) resmi dengan 40 kolom dan panduan pengisian"""
    excel_bytes = ImportDatasetUseCase.generate_excel_template()
    return Response(
        excel_bytes,
        mimetype="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        headers={"Content-Disposition": "attachment;filename=antiburnout_dataset_template.xlsx"}
    )

@assessment_bp.route("/api/predict", methods=["POST"])
def api_predict():
    """API endpoint JSON jika dipanggil dari aplikasi luar atau AJAX"""
    submit_uc, _, _, _ = _get_use_cases()
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
