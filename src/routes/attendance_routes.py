from flask import Blueprint, render_template, request, jsonify
from datetime import date, datetime
from src.database import get_db_connection

attendance_bp = Blueprint("attendance_bp", __name__)


@attendance_bp.route("/attendance")
def attendance_page():
    today = date.today().isoformat()
    conn = get_db_connection()
    users = conn.execute(
        """
        SELECT u.id,
               u.name,
               u.phone,
               u.image_path,
               todays.in_time   AS today_in,
               todays.out_time  AS today_out,
               COALESCE(totals.total_classes, 0) AS total_classes
        FROM users u
        LEFT JOIN (
            SELECT user_id, in_time, out_time
            FROM attendance
            WHERE date = ?
        ) AS todays ON todays.user_id = u.id
        LEFT JOIN (
            SELECT user_id, COUNT(*) AS total_classes
            FROM attendance
            WHERE in_time IS NOT NULL
            GROUP BY user_id
        ) AS totals ON totals.user_id = u.id
        ORDER BY u.name COLLATE NOCASE
        """,
        (today,),
    ).fetchall()
    conn.close()

    total_students = len(users)
    active_sessions = sum(1 for user in users if user["today_in"] and not user["today_out"])
    completed_sessions = sum(1 for user in users if user["today_out"])

    return render_template(
        "attendance.html",
        users=users,
        today=today,
        page="attendance",
        total_students=total_students,
        active_sessions=active_sessions,
        completed_sessions=completed_sessions,
    )


@attendance_bp.route("/attendance/mark", methods=["POST"])
def mark_attendance():
    user_id = request.form["user_id"]
    action = request.form["action"]  # in / out

    today = date.today().isoformat()
    now_time = datetime.now().strftime("%H:%M:%S")

    conn = get_db_connection()
    record = conn.execute(
        "SELECT * FROM attendance WHERE user_id=? AND date=?",
        (user_id, today)
    ).fetchone()

    if not record:
        if action == "in":
            conn.execute(
                "INSERT INTO attendance (user_id, date, in_time) VALUES (?, ?, ?)",
                (user_id, today, now_time)
            )
        else:
            conn.execute(
                "INSERT INTO attendance (user_id, date, out_time) VALUES (?, ?, ?)",
                (user_id, today, now_time)
            )
    else:
        if action == "in" and record["in_time"] is None:
            conn.execute(
                "UPDATE attendance SET in_time=? WHERE id=?",
                (now_time, record["id"])
            )
        elif action == "out" and record["out_time"] is None:
            conn.execute(
                "UPDATE attendance SET out_time=? WHERE id=?",
                (now_time, record["id"])
            )
        else:
            conn.close()
            return jsonify({"status": "error", "message": "Already marked"})

    conn.commit()

    updated_record = conn.execute(
        "SELECT in_time, out_time FROM attendance WHERE user_id=? AND date=?",
        (user_id, today),
    ).fetchone()

    total_classes = conn.execute(
        "SELECT COUNT(*) FROM attendance WHERE user_id=? AND in_time IS NOT NULL",
        (user_id,),
    ).fetchone()[0]

    conn.close()

    action_message = "Start time captured" if action == "in" else "End time captured"

    return jsonify(
        {
            "status": "success",
            "message": action_message,
            "record": {
                "in_time": updated_record["in_time"] if updated_record else None,
                "out_time": updated_record["out_time"] if updated_record else None,
            },
            "total_classes": total_classes,
        }
    )
