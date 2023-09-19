
from config import Config
from config import BaseFlaskConfig as FlaskConfig
from flask_restx import Api
from flask import Blueprint, Flask
from base_api.api import api_ns
import logging

logging.basicConfig(level=Config.LOG_LEVEL)
formatter = logging.Formatter(
    "[%(asctime)s] %(levelname)s: %(message)s", datefmt="%Y-%m-%d %H:%M:%S"
)
handler = logging.FileHandler("status.log", encoding="utf-8")
handler.setFormatter(formatter)

api_bp = Blueprint("api", __name__, url_prefix="/api")

flask_api = Api(
    api_bp,
    title="Flask API",
    version="1.0",
    description="APIs for Flask",
    doc="/docs",
)


def create_app():
    app = Flask(__name__)
    app.config.from_object(FlaskConfig)
    app.logger.addHandler(handler)
    # configure/initialize all your extensions

    flask_api.add_namespace(api_ns)
    app.register_blueprint(api_bp)

    return app
