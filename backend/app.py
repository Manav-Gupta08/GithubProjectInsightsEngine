import os
from flask import Flask
from flask_cors import CORS
from dotenv import load_dotenv

load_dotenv()

def create_app() -> Flask:
    app = Flask(
        __name__,
        static_folder="../frontend/dist",
        static_url_path="",
    )

    # In production CORS_ORIGINS = your Render frontend URL
    # In dev it's http://localhost:5173
    allowed_origins = os.getenv(
        "CORS_ORIGINS",
        "http://localhost:5173"
    ).split(",")

    CORS(app, resources={r"/api/*": {"origins": allowed_origins}})

    from api.repos import repos_bp
    from api.batch import batch_bp
    app.register_blueprint(repos_bp, url_prefix="/api")
    app.register_blueprint(batch_bp, url_prefix="/api")

    @app.route("/", defaults={"path": ""})
    @app.route("/<path:path>")
    def serve_spa(path):
        from flask import send_from_directory
        dist = os.path.join(app.root_path, "../frontend/dist")
        if path and os.path.exists(os.path.join(dist, path)):
            return send_from_directory(dist, path)
        return send_from_directory(dist, "index.html")

    return app

if __name__ == "__main__":
    application = create_app()
    port = int(os.getenv("PORT", 5000))
    debug = os.getenv("FLASK_DEBUG", "1") == "1"
    application.run(host="0.0.0.0", port=port, debug=debug)