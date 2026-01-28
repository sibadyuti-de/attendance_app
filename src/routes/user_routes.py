from flask import Blueprint, render_template, request, redirect, url_for, flash, abort
from src.database import get_db_connection
from src.services.image_service import resize_and_compress
from src.config import Config
import os

user_bp = Blueprint("user_bp", __name__)

def _absolute_image_path(stored_path: str | None) -> str | None:
    if not stored_path:
        return None

    normalized = str(stored_path).replace("\\", "/")

    if normalized.startswith("http://") or normalized.startswith("https://"):
        return None

    if os.path.isabs(normalized):
        return normalized

    normalized = normalized.lstrip("/")
    if normalized.startswith("static/"):
        normalized = normalized.split("static/", 1)[1]

    return os.path.join(Config.STATIC_FOLDER, normalized)


def _cleanup_image(path: str | None) -> None:
    absolute_path = _absolute_image_path(path)
    if absolute_path and os.path.exists(absolute_path):
        try:
            os.remove(absolute_path)
        except OSError:
            pass


@user_bp.route("/")
def list_users():
    conn = get_db_connection()
    users = conn.execute("SELECT * FROM users").fetchall()
    conn.close()
    return render_template("users.html", users=users, page="users")


@user_bp.route("/users")
def legacy_users_route():
    return redirect(url_for("user_bp.list_users"))


@user_bp.route("/users/add", methods=["GET", "POST"])
def add_user():
    if request.method == "POST":
        name = request.form["name"]
        phone = request.form["phone"]
        image_file = request.files["image"]

        saved_image_path = resize_and_compress(image_file)

        conn = get_db_connection()
        conn.execute(
            "INSERT INTO users (name, phone, image_path) VALUES (?, ?, ?)",
            (name, phone, saved_image_path)
        )
        conn.commit()
        conn.close()

        flash("User added successfully!")
        return redirect(url_for("user_bp.list_users"))

    return render_template("add_user.html", page="add-user")


@user_bp.route("/users/<int:user_id>/edit", methods=["GET", "POST"])
def edit_user(user_id):
    conn = get_db_connection()
    user = conn.execute("SELECT * FROM users WHERE id=?", (user_id,)).fetchone()

    if not user:
        conn.close()
        abort(404)

    if request.method == "POST":
        name = request.form["name"]
        phone = request.form["phone"]
        image_file = request.files.get("image")

        image_path = user["image_path"]
        if image_file and image_file.filename:
            new_path = resize_and_compress(image_file)
            _cleanup_image(image_path)
            image_path = new_path

        conn.execute(
            "UPDATE users SET name=?, phone=?, image_path=? WHERE id=?",
            (name, phone, image_path, user_id)
        )
        conn.commit()
        conn.close()

        flash("Candidate updated successfully!")
        return redirect(url_for("user_bp.list_users"))

    conn.close()
    return render_template("edit_user.html", user=user, page="users")


@user_bp.route("/users/<int:user_id>/delete", methods=["POST"])
def delete_user(user_id):
    conn = get_db_connection()
    user = conn.execute("SELECT * FROM users WHERE id=?", (user_id,)).fetchone()

    if not user:
        conn.close()
        abort(404)

    conn.execute("DELETE FROM attendance WHERE user_id=?", (user_id,))
    conn.execute("DELETE FROM users WHERE id=?", (user_id,))
    conn.commit()
    conn.close()

    _cleanup_image(user["image_path"])

    flash("Candidate deleted.")
    return redirect(url_for("user_bp.list_users"))
