"""Blueprint registration for the OCR Flask app."""
from routes.crop_routes import crop_bp
from routes.layout_routes import layout_bp
from routes.ocr_routes import ocr_bp
from routes.template_routes import template_bp


def register_routes(app):
    app.register_blueprint(ocr_bp)
    app.register_blueprint(template_bp)
    app.register_blueprint(layout_bp)
    app.register_blueprint(crop_bp)
