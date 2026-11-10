from urllib.parse import urlparse
from flask import Blueprint, render_template, request, redirect, url_for, session, flash, current_app
from app.core.use_cases import LoginAdminUseCase

auth_bp = Blueprint("auth", __name__)

def is_safe_redirect(target: str) -> bool:
    """Memastikan URL tujuan redirect aman (tidak mengarah ke domain phising/eksternal)"""
    if not target:
        return False
    ref_url = urlparse(request.host_url)
    test_url = urlparse(target)
    return test_url.scheme in ("", "http", "https") and (not test_url.netloc or test_url.netloc == ref_url.netloc)

@auth_bp.route("/login", methods=["GET", "POST"])
def login():
    """
    Halaman dan Pemrosesan Login Administrator (phpMyAdmin Classic Portal).
    Sebelum masuk ke dashboard, pengguna wajib diautentikasi terlebih dahulu.
    """
    # Jika sudah dalam keadaan login, langsung arahkan ke Dashboard Utama
    if session.get("logged_in"):
        return redirect(url_for("main.index"))

    next_url = request.args.get("next") or request.form.get("next", "")

    if request.method == "POST":
        identifier = request.form.get("identifier", "").strip()
        password = request.form.get("password", "").strip()

        user_repo = current_app.user_repository
        login_uc = LoginAdminUseCase(user_repo)

        user, err_msg = login_uc.execute(identifier, password)

        if user:
            # Set sesi login Flask
            session.clear()
            session["logged_in"] = True
            session["user_id"] = user.id
            session["username"] = user.username
            session["user_name"] = user.full_name
            session["user_email"] = user.email
            session["user_role"] = user.role

            flash(f"Autentikasi berhasil. Selamat datang, {user.full_name}!", "success")

            # Redirect ke halaman tujuan sebelum login, atau ke Dashboard jika tidak ada
            if next_url and is_safe_redirect(next_url) and not next_url.startswith("/login"):
                return redirect(next_url)
            return redirect(url_for("main.index"))
        else:
            flash(err_msg, "danger")
            return render_template(
                "auth/login.html",
                identifier=identifier,
                next=next_url,
                db_engine=getattr(current_app, "db_engine_name", "Local SQLite Engine")
            ), 401

    return render_template(
        "auth/login.html",
        next=next_url,
        db_engine=getattr(current_app, "db_engine_name", "Local SQLite Engine")
    )

@auth_bp.route("/logout", methods=["GET", "POST"])
def logout():
    """Mengakhiri sesi login administrator dan kembali ke layar login"""
    session.clear()
    flash("Anda telah berhasil keluar dari sesi Administrator AntiBurnout.", "success")
    return redirect(url_for("auth.login"))
