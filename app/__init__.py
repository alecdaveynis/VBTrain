import os
from flask import Flask

def create_app():
    app = Flask(__name__)
    # static folder is app/static by default now
    app.config['UPLOAD_FOLDER'] = os.path.join(app.static_folder, 'uploads')
    os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)

    from .routes import main
    app.register_blueprint(main)
    return app
