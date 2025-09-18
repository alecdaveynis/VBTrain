import cv2
import os

def process_video(filepath: str, mode: str = "clip", interval_sec: int = 2):
    """
    mode = 'clip'  -> sample every interval_sec
    mode = 'match' -> segment rallies (simple motion-based heuristic)
    returns: list[str] event descriptions with timestamps
    """
    if mode == "match":
        return _events_by_rally(filepath)
    return _events_by_interval(filepath, interval_sec=interval_sec)

def _events_by_interval(filepath: str, interval_sec: int = 2):
    cap = cv2.VideoCapture(filepath)
    fps = cap.get(cv2.CAP_PROP_FPS) or 30.0
    frame_interval = max(int(fps * max(1, interval_sec)), 1)

    events = []
    count = 0
    while cap.isOpened():
        ret, _ = cap.read()
        if not ret:
            break
        if count % frame_interval == 0:
            t = count / fps
            events.append(f"[{_fmt_time(t)}] Frame sample — analyze moment")
        count += 1
    cap.release()
    return events

def _events_by_rally(filepath: str):
    """
    Very lightweight rally segmentation using motion magnitude:
    - Compute gray frame diffs & accumulate motion energy.
    - When motion stays low for a 'gap' window -> rally boundary.
    This is a heuristic (not perfect), but works well enough to split long matches.
    """
    cap = cv2.VideoCapture(filepath)
    fps = cap.get(cv2.CAP_PROP_FPS) or 30.0
    width = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH)) or 1280
    height = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT)) or 720

    # Downscale for speed (processing only; keeps original file intact)
    scale = 640 / max(width, 1)
    if scale < 1.0:
        new_w, new_h = int(width * scale), int(height * scale)
    else:
        new_w, new_h = width, height

    # parameters
    motion_alpha = 0.9        # smoothing factor
    motion_thresh = 4.0       # threshold to consider “in play” (tune)
    gap_sec = 2.0             # how long of low-motion gap = rally break
    gap_frames = int(fps * gap_sec)

    prev_gray = None
    motion_smooth = 0.0
    in_rally = False
    rally_start_f = 0
    gap_count = 0

    rallies = []

    frame_idx = 0
    while True:
        ret, frame = cap.read()
        if not ret:
            # close any open rally
            if in_rally:
                rallies.append((rally_start_f, frame_idx - 1))
            break

        if new_w != frame.shape[1] or new_h != frame.shape[0]:
            frame = cv2.resize(frame, (new_w, new_h), interpolation=cv2.INTER_AREA)

        gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)

        if prev_gray is None:
            prev_gray = gray
            frame_idx += 1
            continue

        # simple motion magnitude = mean absolute difference
        diff = cv2.absdiff(gray, prev_gray)
        motion = float(diff.mean())
        prev_gray = gray

        # smooth
        motion_smooth = motion_alpha * motion_smooth + (1 - motion_alpha) * motion

        if motion_smooth > motion_thresh:
            # likely ball in play
            if not in_rally:
                in_rally = True
                rally_start_f = frame_idx
            gap_count = 0
        else:
            # low motion — count towards gap
            if in_rally:
                gap_count += 1
                if gap_count >= gap_frames:
                    # close rally
                    rally_end_f = frame_idx - gap_frames
                    rallies.append((rally_start_f, max(rally_start_f, rally_end_f)))
                    in_rally = False
                    gap_count = 0

        frame_idx += 1

    cap.release()

    # Build event strings at rally midpoints
    events = []
    for (fs, fe) in rallies:
        if fe <= fs:
            continue
        mid = (fs + fe) / 2.0
        t = mid / fps
        duration = (fe - fs) / fps
        events.append(f"[{_fmt_time(t)}] Rally ({duration:.1f}s) — analyze key sequence")
    return events

def _fmt_time(seconds: float) -> str:
    s = int(seconds)
    ms = int((seconds - s) * 1000)
    m, s = divmod(s, 60)
    h, m = divmod(m, 60)
    if h > 0:
        return f"{h:02d}:{m:02d}:{s:02d}.{ms:03d}"
    return f"{m:02d}:{s:02d}.{ms:03d}"
