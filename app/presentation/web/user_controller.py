from flask import Blueprint, render_template, current_app

user_bp = Blueprint("user", __name__)


# Route untuk melihat daftar tabel user (Browse)
@user_bp.route("/", methods=["GET"])
def list_users():
    users = current_app.user_repository.find_all()
    return render_template("user/list.html", users=users)