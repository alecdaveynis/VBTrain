# def process_video(filepath):
#     # Dummy output for now
#     return [
#         "Serve by #12, Pass by #4, Set by #10, Spike by #8",
#         "Serve by #5, Pass by #2, Set by #11, Block by #6"
#     ]

import cv2

def process_video(filepath):
    cap = cv2.VideoCapture(filepath)
    fps = cap.get(cv2.CAP_PROP_FPS)
    frame_interval = int(fps * 2)  # every 2 seconds

    events = []
    count = 0

    while cap.isOpened():
        ret, frame = cap.read()
        if not ret:
            break
        if count % frame_interval == 0:
            # Dummy example: replace with action recognition later
            events.append(f"Analyzed frame at {count/fps:.1f}s - potential play event")
        count += 1

    cap.release()
    return events
