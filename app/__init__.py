import os
from flask import Flask
from config import UPLOAD_FOLDER, MAX_CONTENT_LENGTH_MB

def create_app():
    app = Flask(__name__)
    app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER

    # Upload hard limit (Flask rejects larger)
    app.config['MAX_CONTENT_LENGTH'] = MAX_CONTENT_LENGTH_MB * 1024 * 1024

    os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)

    from .routes import main
    app.register_blueprint(main)
    return app
