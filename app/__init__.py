import os
from flask import Flask
from config import MAX_CONTENT_LENGTH_MB  # don't import UPLOAD_FOLDER anymore

def create_app():
    app = Flask(__name__)

    # Put uploads *inside* the app's static folder so url_for('static', ...) works
    upload_dir = os.path.join(app.static_folder, 'uploads')
    os.makedirs(upload_dir, exist_ok=True)

    app.config['UPLOAD_FOLDER'] = upload_dir
    app.config['MAX_CONTENT_LENGTH'] = MAX_CONTENT_LENGTH_MB * 1024 * 1024

    from .routes import main
    app.register_blueprint(main)
    return app
