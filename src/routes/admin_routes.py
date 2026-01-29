import random
from datetime import datetime, timedelta, date

from flask import Blueprint, render_template, request, redirect, url_for, flash
from src.database import get_db_connection

admin_bp = Blueprint("admin_bp", __name__)


def _parse_time_to_minutes(raw_time: str) -> int:
    cleaned = (raw_time or "").strip()
    if not cleaned:
        raise ValueError("Time value cannot be empty")

    for fmt in ("%H:%M", "%I:%M%p", "%I:%M %p"):
        try:
            parsed = datetime.strptime(cleaned, fmt)
            return parsed.hour * 60 + parsed.minute
        except ValueError:
            continue

    raise ValueError(f"Invalid time format: {raw_time}")


def _minutes_to_time_str(total_minutes: int) -> str:
    hours = (total_minutes // 60) % 24
    minutes = total_minutes % 60
    return f"{hours:02d}:{minutes:02d}:00"


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
            "created_at": user["created_at"],
            "total_classes": total_classes,
        })

    conn.close()
    return render_template(
        "admin_dashboard.html",
        summary=summary,
        page="admin",
    )


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
        report_generated=date.today().isoformat(),
        page="admin"
    )


@admin_bp.route("/admin/generate-attendance", methods=["POST"])
def generate_attendance() -> str:
    try:
        user_id = int(request.form.get("user_id", ""))
    except ValueError:
        flash("Select a valid candidate before generating attendance.")
        return redirect(url_for("admin_bp.admin_dashboard"))

    start_date_raw = request.form.get("start_date", "")
    end_date_raw = request.form.get("end_date", "")
    start_time_raw = request.form.get("time_start", "")
    end_time_raw = request.form.get("time_end", "")
    total_classes_raw = request.form.get("total_classes", "")
    duration_raw = request.form.get("class_duration_hours", "")

    try:
        start_date = datetime.strptime(start_date_raw, "%Y-%m-%d").date()
        end_date = datetime.strptime(end_date_raw, "%Y-%m-%d").date()
    except ValueError:
        flash("Provide both start and end dates in YYYY-MM-DD format.")
        return redirect(url_for("admin_bp.admin_dashboard"))

    if start_date > end_date:
        flash("Start date must be before or same as end date.")
        return redirect(url_for("admin_bp.admin_dashboard"))

    try:
        total_classes = int(total_classes_raw)
    except ValueError:
        flash("Total classes must be a positive number.")
        return redirect(url_for("admin_bp.admin_dashboard"))

    if total_classes <= 0:
        flash("Total classes must be greater than zero.")
        return redirect(url_for("admin_bp.admin_dashboard"))

    try:
        duration_hours = float(duration_raw)
    except ValueError:
        flash("Class duration must be a number (in hours).")
        return redirect(url_for("admin_bp.admin_dashboard"))

    duration_minutes = int(round(duration_hours * 60))
    if duration_minutes <= 0:
        flash("Class duration must be greater than zero.")
        return redirect(url_for("admin_bp.admin_dashboard"))

    try:
        slot_start = _parse_time_to_minutes(start_time_raw)
        slot_end = _parse_time_to_minutes(end_time_raw)
    except ValueError as exc:
        flash(str(exc))
        return redirect(url_for("admin_bp.admin_dashboard"))

    if slot_start >= slot_end:
        flash("Start time must be earlier than end time.")
        return redirect(url_for("admin_bp.admin_dashboard"))

    if slot_start + duration_minutes > slot_end:
        flash("Class duration does not fit within the selected time window.")
        return redirect(url_for("admin_bp.admin_dashboard"))

    conn = get_db_connection()
    user = conn.execute("SELECT id FROM users WHERE id=?", (user_id,)).fetchone()
    if not user:
        conn.close()
        flash("Selected candidate does not exist.")
        return redirect(url_for("admin_bp.admin_dashboard"))

    days_range = []
    cursor_day = start_date
    while cursor_day <= end_date:
        days_range.append(cursor_day)
        cursor_day += timedelta(days=1)

    existing_rows = conn.execute(
        "SELECT date FROM attendance WHERE user_id=? AND date BETWEEN ? AND ?",
        (user_id, start_date.isoformat(), end_date.isoformat()),
    ).fetchall()
    taken_dates = {row["date"] for row in existing_rows}

    available_dates = [d for d in days_range if d.isoformat() not in taken_dates]
    if not available_dates:
        conn.close()
        flash("No free dates available in the selected window for this candidate.")
        return redirect(url_for("admin_bp.admin_dashboard"))

    classes_to_create = min(total_classes, len(available_dates))
    chosen_dates = random.sample(available_dates, classes_to_create)

    created = 0
    for class_date in chosen_dates:
        in_minutes = random.randint(slot_start, slot_end - duration_minutes)
        out_minutes = in_minutes + duration_minutes

        conn.execute(
            "INSERT INTO attendance (user_id, date, in_time, out_time) VALUES (?, ?, ?, ?)",
            (
                user_id,
                class_date.isoformat(),
                _minutes_to_time_str(in_minutes),
                _minutes_to_time_str(out_minutes),
            ),
        )
        created += 1

    conn.commit()
    conn.close()

    skipped = total_classes - created
    if skipped > 0:
        flash(
            f"Created {created} attendance records. {skipped} could not be scheduled because there were not enough free dates."
        )
    else:
        flash(f"Successfully created {created} attendance records.")

    return redirect(
        url_for("admin_bp.admin_user_detail", user_id=user_id, _anchor="backfill-tool")
    )
