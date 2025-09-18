import os
from flask import Blueprint, render_template, request, redirect, url_for, current_app
from werkzeug.utils import secure_filename

from config import ALLOWED_EXTENSIONS
from .video_processor import process_video
from .gpt_analyzer import analyze_play, suggest_lineup, build_practice_schedule
from .data_store import (
    load_players, upsert_player, compute_lineup_simple, collect_struggles,
    load_practice, save_practice, save_practice_plan
)

main = Blueprint('main', __name__)

# -------- Helpers --------
def allowed_file(filename: str) -> bool:
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

# -------- Core pages --------
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

            # Read analysis settings
            mode = (request.form.get('mode') or 'clip').strip()
            try:
                interval_sec = int(request.form.get('interval_sec') or 2)
            except ValueError:
                interval_sec = 2

            # Optional metadata / coaching context
            jersey_number = request.form.get('jersey_number', '').strip()
            position = request.form.get('position', '').strip()
            notes = request.form.get('notes', '').strip()

            # Extract events (clip = fixed interval, match = rally segmentation)
            events = process_video(save_path, mode=mode, interval_sec=interval_sec)

            # Build shared context string for the analyzer
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
                notes=notes,
                analysis_mode=mode,
                interval_sec=interval_sec
            )

        return "Invalid file type. Please upload a .mp4, .avi, or .mov file.", 400

    # GET request: just show the upload page
    return render_template('upload.html')


# -------- Players --------
@main.route('/players', methods=['GET', 'POST'])
def players():
    if request.method == 'POST':
        form = request.form
        player = {
            "name": form.get("name","").strip(),
            "jersey": form.get("jersey","").strip(),
            "role": form.get("role","").strip(),
            "attack_pct": form.get("attack_pct","") or 0,
            "pass_rating": form.get("pass_rating","") or 0,
            "block_eff": form.get("block_eff","") or 0,
            "serve_pct": form.get("serve_pct","") or 0,
            "dig_pct": form.get("dig_pct","") or 0,
            "notes": form.get("notes","").strip(),
            "struggles": form.get("struggles","").strip()  # comma-separated tags
        }
        upsert_player(player)
        return redirect(url_for('main.players'))

    roster = load_players()
    return render_template('players.html', roster=roster)

# -------- Lineup --------
@main.route('/lineup', methods=['GET', 'POST'])
def lineup():
    roster = load_players()
    simple = compute_lineup_simple(roster)
    llm_notes = None  # default: don’t call GPT

    if request.method == 'POST' and request.form.get('action') == 'generate':
        llm_notes = suggest_lineup(roster, simple)

    return render_template(
        'lineup.html',
        roster=roster,
        simple=simple,
        llm_notes=llm_notes
    )

# -------- Practice (with schedule + explicit Generate) --------
@main.route('/practice', methods=['GET', 'POST'])
def practice():
    roster = load_players()
    struggles = collect_struggles(roster)
    settings = load_practice()  # days, start_time, duration_min, location, last_plan

    if request.method == 'POST':
        # Update settings first (so user edits persist even if they don't generate)
        days = request.form.get('days', settings.get('days', 'Mon, Wed, Fri')).strip()
        start_time = request.form.get('start_time', settings.get('start_time', '18:00')).strip()
        duration_min = int(request.form.get('duration_min', settings.get('duration_min', 90)) or 90)
        location = request.form.get('location', settings.get('location', '')).strip()

        save_practice({
            "days": days,
            "start_time": start_time,
            "duration_min": duration_min,
            "location": location
        })

        # Only generate when the user clicked the "Generate Practice Plan" button
        if request.form.get('action') == 'generate':
            plan = build_practice_schedule(
                roster, struggles,
                days=days, start_time=start_time, duration_min=duration_min, location=location
            )
            save_practice_plan(plan)

        # Reload settings to reflect any changes & possibly new plan
        settings = load_practice()

    return render_template(
        'practice.html',
        roster=roster,
        struggles=struggles,
        settings=settings  # includes last_plan
    )
