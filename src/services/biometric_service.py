from src.database import get_db_connection


def store_fingerprint_template(user_id, template_bytes):
    """
    Store fingerprint template for a user.
    """
    conn = get_db_connection()
    conn.execute(
        "UPDATE users SET fingerprint_template=? WHERE id=?",
        (template_bytes, user_id)
    )
    conn.commit()
    conn.close()


def match_fingerprint(template_bytes):
    """
    Match incoming fingerprint template against stored templates.
    Returns matched user_id or None.
    
    NOTE:
    Actual fingerprint matching is done by the MFS110 SDK.
    Here we simply compare templates using SDK-provided match function.
    """

    # --- PLACEHOLDER FOR SDK MATCH FUNCTION ---
    # The vendor SDK usually provides something like:
    # score = SDK.MatchTemplates(stored_template, incoming_template)

    conn = get_db_connection()
    users = conn.execute(
        "SELECT id, fingerprint_template FROM users"
    ).fetchall()
    conn.close()

    for user in users:
        stored_template = user["fingerprint_template"]

        # Placeholder comparison
        if stored_template == template_bytes:
            return user["id"]

        # In real integration:
        # if SDK.match(stored_template, template_bytes) >= threshold:
        #     return user["id"]

    return None
