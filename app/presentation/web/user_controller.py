from flask import Blueprint, render_template, request, redirect, url_for, current_app

user_bp = Blueprint("user", __name__)

# Route untuk melihat daftar tabel user (Browse)
@user_bp.route("/", methods=["GET"])
def list_users():
    users = current_app.user_repository.find_all()
    return render_template("user/list.html", users=users)

# Route untuk form input user baru (Insert)
@user_bp.route("/create", methods=["GET", "POST"])
def create_user():
    if request.method == "POST":
        # Ambil data dari form -> simpan ke database
        pass
    return render_template("user/form.html")