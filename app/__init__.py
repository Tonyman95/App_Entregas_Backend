from flask import Flask, jsonify
from flask_cors import CORS
from flask_jwt_extended import JWTManager
from sqlalchemy import select, func
from database import SessionLocal
from config import Config

def create_app():
    app = Flask(__name__)
    app.config.from_object(Config)

    CORS(app)
    jwt = JWTManager(app)

    # Import and register blueprints
    from api.auth import create_auth_blueprint, require_perm
    auth_bp = create_auth_blueprint(jwt)
    app.register_blueprint(auth_bp)

    from api.beneficios import create_beneficios_blueprint
    beneficios_bp = create_beneficios_blueprint(require_perm)
    app.register_blueprint(beneficios_bp)

    from api.periodos import create_periodos_blueprint
    periodos_bp = create_periodos_blueprint(require_perm)
    app.register_blueprint(periodos_bp)

    from api.trabajadores import create_trabajadores_blueprint
    trabajadores_bp = create_trabajadores_blueprint(require_perm)
    app.register_blueprint(trabajadores_bp)

    from api.sucursales import create_sucursales_blueprint
    sucursales_bp = create_sucursales_blueprint(require_perm)
    app.register_blueprint(sucursales_bp)

    from api.usuarios import create_usuarios_blueprint
    usuarios_bp = create_usuarios_blueprint(require_perm)
    app.register_blueprint(usuarios_bp)

    from api.entregas import create_entregas_blueprint
    entregas_bp = create_entregas_blueprint(require_perm)
    app.register_blueprint(entregas_bp)
    
    from api.reportes import create_reportes_blueprint
    reportes_bp = create_reportes_blueprint(require_perm)
    app.register_blueprint(reportes_bp)


    @app.teardown_appcontext
    def shutdown_session(exception=None):
        SessionLocal.remove()

    @app.get('/')
    def index():
        try:
            db = SessionLocal()
            db.execute(select(func.now())) # Use func.now() for broader compatibility
            return jsonify({"ok": "API de Gestion de Entregas"}), 200
        except Exception as e:
            return jsonify({"ok": False, "error": str(e)}), 500

    @app.get('/health')
    def health():
        try:
            db = SessionLocal()
            db.execute(select(func.now())) # Use func.now() for broader compatibility
            return jsonify({"ok": "Todo Bien, API funcionando"}), 200
        except Exception as e:
            return jsonify({"ok": False, "error": str(e)}), 500

    return app

# Expose the Flask application object for WSGI servers like gunicorn.
app = create_app()
