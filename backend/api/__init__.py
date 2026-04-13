from .setup    import bp as setup_bp
from .workflow import bp as workflow_bp
from .bench    import bp as bench_bp
from .security import bp as security_bp

def register_blueprints(app):
    app.register_blueprint(setup_bp,    url_prefix="/api/setup")
    app.register_blueprint(workflow_bp, url_prefix="/api/workflow")
    app.register_blueprint(bench_bp,    url_prefix="/api/bench")
    app.register_blueprint(security_bp, url_prefix="/api/security")
