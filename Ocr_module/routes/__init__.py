"""Blueprint registration for the OCR Flask app."""
from routes.auth_routes import auth_bp
from routes.claims_routes import claims_bp
from routes.crop_routes import crop_bp
from routes.diagnostic_routes import diagnostic_bp
from routes.layout_routes import layout_bp
from routes.learning_routes import learning_bp
from routes.ocr_routes import ocr_bp
from routes.review_routes import review_bp
from routes.settings_routes import settings_bp
from routes.setup_routes import setup_bp
from routes.template_routes import template_bp
from routes.testing_routes import testing_bp


def register_routes(app):
    app.register_blueprint(auth_bp)
    app.register_blueprint(ocr_bp)
    app.register_blueprint(template_bp)
    app.register_blueprint(layout_bp)
    app.register_blueprint(crop_bp)
    app.register_blueprint(testing_bp)
    app.register_blueprint(claims_bp)
    app.register_blueprint(review_bp)
    app.register_blueprint(settings_bp)
    app.register_blueprint(learning_bp)
    app.register_blueprint(setup_bp)
    # TEMPORARY - Phase 1 DB integration diagnostic. Remove alongside
    # routes/diagnostic_routes.py once the patients CRUD test is done.
    app.register_blueprint(diagnostic_bp)
