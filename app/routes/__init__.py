from app.routes.alerts import alerts_bp
from app.routes.dashboard import dashboard_bp
from app.routes.health import health_bp
from app.routes.logs import logs_bp


def register_routes(app):
    app.register_blueprint(health_bp)
    app.register_blueprint(logs_bp)
    app.register_blueprint(alerts_bp)
    app.register_blueprint(dashboard_bp)

