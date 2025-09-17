import os
from flask import Blueprint, render_template, request, redirect, url_for, current_app
from werkzeug.utils import secure_filename
from config import ALLOWED_EXTENSIONS
from .video_processor import process_video
from .gpt_analyzer import analyze_play

main = Blueprint('main', __name__)

def allowed_file(filename: str) -> bool:
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

@main.route('/', methods=['GET'])
def home():
    return render_template('home.html')

@main.route('/upload', methods=['GET', 'POST'])
def upload():
    if request.method == 'POST':
        if 'video' not in request.files:
            return "No file part in form.", 400

        file = request.files['video']
        if file.filename == '':
            return "No selected file.", 400

        if file and allowed_file(file.filename):
            filename = secure_filename(file.filename)
            save_path = os.path.join(current_app.config['UPLOAD_FOLDER'], filename)
            file.save(save_path)

            # Optional metadata / user coaching notes
            jersey_number = request.form.get('jersey_number', '').strip()
            position = request.form.get('position', '').strip()
            notes = request.form.get('notes', '').strip()

            # Extract simple "events" from video (dummy logic every ~2s)
            events = process_video(save_path)

            # Build a shared context string for the analyzer
            extra_context = []
            if jersey_number:
                extra_context.append(f"Player jersey number: {jersey_number}")
            if position:
                extra_context.append(f"Player role/position: {position}")
            if notes:
                extra_context.append(f"Focus areas: {notes}")
            context_str = "\n".join(extra_context)

            # Ask GPT for coaching feedback per event with context
            feedback = [analyze_play(e, context_str) for e in events]

            # URL for inline video preview
            video_rel = os.path.join('uploads', filename).replace("\\", "/")
            video_url = url_for('static', filename=video_rel)

            return render_template(
                'results.html',
                feedback=feedback,
                video_url=video_url,
                original_name=file.filename,
                jersey_number=jersey_number,
                position=position,
                notes=notes
            )

        return "Invalid file type. Please upload a .mp4, .avi, or .mov file.", 400

    return render_template('upload.html')
