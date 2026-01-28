from flask import Blueprint, render_template
from src.database import get_db_connection

admin_bp = Blueprint("admin_bp", __name__)


@admin_bp.route("/admin")
def admin_dashboard():
    conn = get_db_connection()

    users = conn.execute("SELECT * FROM users").fetchall()

    summary = []
    for user in users:
        total_classes = conn.execute(
            "SELECT COUNT(*) FROM attendance WHERE user_id=? AND in_time IS NOT NULL",
            (user["id"],)
        ).fetchone()[0]

        summary.append({
            "id": user["id"],
            "name": user["name"],
            "phone": user["phone"],
            "image": user["image_path"],
            "total_classes": total_classes
        })

    conn.close()
    return render_template("admin_dashboard.html", summary=summary, page="admin")


@admin_bp.route("/admin/user/<int:user_id>")
def admin_user_detail(user_id):
    conn = get_db_connection()

    user = conn.execute("SELECT * FROM users WHERE id=?", (user_id,)).fetchone()
    attendance = conn.execute(
        "SELECT * FROM attendance WHERE user_id=? ORDER BY date DESC",
        (user_id,)
    ).fetchall()

    conn.close()

    total_classes = sum(1 for row in attendance if row["in_time"])

    return render_template(
        "admin_user_detail.html",
        user=user,
        attendance=attendance,
        total_classes=total_classes,
        page="admin"
    )
