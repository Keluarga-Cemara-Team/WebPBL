from flask import Blueprint, render_template, request, Response, redirect, url_for, flash, jsonify, current_app
from app.core.use_cases import (
    SubmitAssessmentUseCase,
    UpdateAssessmentUseCase,
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
        ImportDatasetUseCase(repo, ml_svc),
        UpdateAssessmentUseCase(repo, ml_svc)
    )

@assessment_bp.route("/", methods=["GET"])
def form():
    """Menampilkan form input kuesioner data primer lengkap (40 kolom dataset)"""
    return render_template("assessment/form.html")

@assessment_bp.route("/submit", methods=["POST"])
def submit():
    """Memproses submission form data primer menggunakan Clean Architecture Use Case"""
    submit_uc, _, _, _, _ = _get_use_cases()

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
    """Halaman tabel data primer yang terkumpul beserta metrik ringkas dan pagination"""
    _, _, history_uc, _, _ = _get_use_cases()
    data = history_uc.execute()
    all_records = data["assessments"]

    try:
        per_page = int(request.args.get("per_page", 20))
    except (TypeError, ValueError):
        per_page = 20
    if per_page not in (10, 20, 50, 100):
        per_page = 20

    total_records = len(all_records)
    total_pages = max(1, (total_records + per_page - 1) // per_page)

    try:
        page = int(request.args.get("page", 1))
    except (TypeError, ValueError):
        page = 1
    page = max(1, min(page, total_pages))

    start_idx = (page - 1) * per_page
    end_idx = start_idx + per_page
    paginated_records = all_records[start_idx:end_idx]

    window_start = max(1, page - 2)
    window_end = min(total_pages, window_start + 4)
    window_start = max(1, window_end - 4)

    pagination = {
        "page": page,
        "per_page": per_page,
        "total_records": total_records,
        "total_pages": total_pages,
        "start_row": start_idx + 1 if total_records else 0,
        "end_row": min(end_idx, total_records),
        "page_numbers": list(range(window_start, window_end + 1)),
    }

    return render_template(
        "assessment/dataset.html",
        records=paginated_records,
        metrics=data["metrics"],
        pagination=pagination,
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

@assessment_bp.route("/edit/<assessment_id>", methods=["GET"])
def edit(assessment_id):
    """Menampilkan form edit untuk data responden berdasarkan ID"""
    repo = current_app.assessment_repository
    entity = repo.find_by_id(assessment_id)
    if not entity:
        flash(f"Data responden #{assessment_id} tidak ditemukan.", "danger")
        return redirect(url_for("assessment.dataset_view"))
    return render_template("assessment/edit.html", item=entity.to_dict())

@assessment_bp.route("/edit/<assessment_id>", methods=["POST"])
def update(assessment_id):
    """Memproses perubahan data responden dengan UpdateAssessmentUseCase"""
    _, _, _, _, update_uc = _get_use_cases()

    raw_data = request.form.to_dict()
    recalculate_ml = request.form.get("recalculate_ml") in ("1", "true", "on", "yes")

    try:
        updated_entity, _ = update_uc.execute(assessment_id, raw_data, recalculate_ml=recalculate_ml)
        flash(f"Data responden #{assessment_id} ({updated_entity.full_name}) berhasil diperbarui.", "success")
        return redirect(url_for("assessment.detail", assessment_id=assessment_id))
    except ValueError as e:
        flash(str(e), "danger")
        return redirect(url_for("assessment.edit", assessment_id=assessment_id))
    except Exception as e:
        flash(f"Terjadi kesalahan saat memperbarui data: {str(e)}", "danger")
        return redirect(url_for("assessment.edit", assessment_id=assessment_id))

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
    _, export_uc, _, _, _ = _get_use_cases()
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
    _, _, _, import_uc, _ = _get_use_cases()

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

@assessment_bp.route("/api/predict", methods=["POST", "OPTIONS"])
def api_predict():
    """API endpoint JSON jika dipanggil dari aplikasi luar atau AJAX"""
    if request.method == "OPTIONS":
        resp = Response()
        resp.headers["Access-Control-Allow-Origin"] = "*"
        resp.headers["Access-Control-Allow-Methods"] = "POST, OPTIONS"
        resp.headers["Access-Control-Allow-Headers"] = "Content-Type, Authorization, Accept"
        return resp

    submit_uc, _, _, _, _ = _get_use_cases()
    payload = request.get_json(silent=True) or request.form.to_dict()

    try:
        saved_entity, ml_result = submit_uc.execute(payload)
        resp = jsonify({
            "status": "success",
            "data": saved_entity.to_dict(),
            "evaluation": ml_result
        })
        resp.headers["Access-Control-Allow-Origin"] = "*"
        return resp, 201
    except ValueError as e:
        resp = jsonify({"status": "error", "message": str(e)})
        resp.headers["Access-Control-Allow-Origin"] = "*"
        return resp, 400
