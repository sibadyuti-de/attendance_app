from flask import Flask, url_for
from src.config import Config
from src.database import init_db
import os

def create_app():
    app = Flask(
        __name__,
        static_folder=Config.STATIC_FOLDER,
        static_url_path="/static",
    )
    app.config.from_object(Config)

    # Ensure upload folder exists
    os.makedirs(app.config["UPLOAD_FOLDER"], exist_ok=True)

    # Initialize database
    init_db()

    # Blueprints will be registered here later
    from src.routes.user_routes import user_bp
    from src.routes.attendance_routes import attendance_bp
    from src.routes.admin_routes import admin_bp
    
    app.register_blueprint(user_bp)
    app.register_blueprint(attendance_bp)
    app.register_blueprint(admin_bp)

    @app.context_processor
    def utility_processor():
        def image_url(path):
            if not path:
                return ""

            normalized = str(path).replace("\\", "/")

            if normalized.startswith("http://") or normalized.startswith("https://"):
                return normalized

            for marker in ("/static/", "static/"):
                if marker in normalized:
                    normalized = normalized.split(marker, 1)[1]
                    break

            return url_for("static", filename=normalized)

        return dict(image_url=image_url)



    return app
