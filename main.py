import cv2
import mediapipe as mp
import pyautogui
import time
import os
import platform
from mediapipe.tasks.python import vision

try:
    import pyttsx3
    voice_engine = pyttsx3.init()
    voice_enabled = True
except:
    voice_engine = None
    voice_enabled = False


WINDOW_NAME = "Premium AI Gesture Controller"

model_path = os.path.join(os.path.dirname(__file__), "models", "hand_landmarker.task")

if not os.path.exists(model_path):
    print(f"Model file not found: {model_path}")
    print("Run: python setup_models.py")
    exit(1)

base_options = mp.tasks.BaseOptions(model_asset_path=model_path)

options = vision.HandLandmarkerOptions(
    base_options=base_options,
    num_hands=1,
    min_hand_detection_confidence=0.75,
    min_hand_presence_confidence=0.75,
    min_tracking_confidence=0.75
)

hand_landmarker = vision.HandLandmarker.create_from_options(options)

cap = cv2.VideoCapture(0)

if not cap.isOpened():
    print("Webcam not found")
    exit(1)

cap.set(cv2.CAP_PROP_FRAME_WIDTH, 1920)
cap.set(cv2.CAP_PROP_FRAME_HEIGHT, 1080)

cv2.namedWindow(WINDOW_NAME, cv2.WINDOW_NORMAL)
cv2.setWindowProperty(
    WINDOW_NAME,
    cv2.WND_PROP_FULLSCREEN,
    cv2.WINDOW_FULLSCREEN
)

pyautogui.FAILSAFE = False

last_action_time = 0
cooldown = 1.5

last_gesture = "WAIT"
stable_count = 0
required_stable_frames = 8

prev_time = time.time()
action_text = "Waiting..."

connections = [
    (0, 1), (1, 2), (2, 3), (3, 4),
    (5, 6), (6, 7), (7, 8),
    (9, 10), (10, 11), (11, 12),
    (13, 14), (14, 15), (15, 16),
    (17, 18), (18, 19), (19, 20),
    (0, 5), (5, 9), (9, 13), (13, 17), (0, 17)
]


def speak(text):
    if voice_enabled and voice_engine:
        try:
            voice_engine.say(text)
            voice_engine.runAndWait()
        except:
            pass


def fingers_up(hand_landmarks):
    tips = [8, 12, 16, 20]
    pips = [6, 10, 14, 18]

    fingers = []

    for tip, pip in zip(tips, pips):
        if hand_landmarks[tip].y < hand_landmarks[pip].y:
            fingers.append(1)
        else:
            fingers.append(0)

    return fingers


def get_gesture(total):
    if total == 4:
        return "NEXT", "Open Palm", "Next Slide"
    elif total == 3:
        return "PREVIOUS", "Three Fingers", "Previous Slide"
    elif total == 2:
        return "START", "Two Fingers", "Start Slideshow"
    elif total == 0:
        return "EXIT", "Fist", "Exit Slideshow"
    else:
        return "WAIT", "Unknown", "Waiting..."


def perform_action(gesture):
    if gesture == "NEXT":
        pyautogui.press("right")
        return "Next Slide"

    elif gesture == "PREVIOUS":
        pyautogui.press("left")
        return "Previous Slide"

    elif gesture == "START":
        if platform.system() == "Darwin":
            pyautogui.hotkey("command", "enter")
        else:
            pyautogui.press("f5")
        return "Start Slideshow"

    elif gesture == "EXIT":
        pyautogui.press("esc")
        return "Exit Slideshow"

    return "Waiting..."


def draw_hand(frame, landmarks, w, h):
    for start_idx, end_idx in connections:
        start = landmarks[start_idx]
        end = landmarks[end_idx]

        x1, y1 = int(start.x * w), int(start.y * h)
        x2, y2 = int(end.x * w), int(end.y * h)

        cv2.line(frame, (x1, y1), (x2, y2), (0, 255, 130), 2)

    for landmark in landmarks:
        x = int(landmark.x * w)
        y = int(landmark.y * h)

        cv2.circle(frame, (x, y), 6, (255, 255, 255), -1)
        cv2.circle(frame, (x, y), 8, (0, 255, 130), 2)


def draw_panel(frame, gesture, action, fps, confidence, progress, fingers, status):
    h, w, _ = frame.shape

    panel_w = 460
    panel_h = 225
    x1 = 35
    y1 = 35
    x2 = x1 + panel_w
    y2 = y1 + panel_h

    overlay = frame.copy()

    cv2.rectangle(overlay, (x1, y1), (x2, y2), (15, 15, 15), -1)
    cv2.addWeighted(overlay, 0.70, frame, 0.30, 0, frame)

    cv2.rectangle(frame, (x1, y1), (x2, y2), (0, 255, 130), 2)

    cv2.putText(frame, "AI Gesture Slide Controller", (x1 + 25, y1 + 35),
                cv2.FONT_HERSHEY_SIMPLEX, 0.72, (0, 255, 130), 2)

    cv2.putText(frame, f"Gesture : {gesture}", (x1 + 25, y1 + 75),
                cv2.FONT_HERSHEY_SIMPLEX, 0.58, (255, 255, 255), 2)

    cv2.putText(frame, f"Action  : {action}", (x1 + 25, y1 + 105),
                cv2.FONT_HERSHEY_SIMPLEX, 0.58, (255, 255, 255), 2)

    cv2.putText(frame, f"Status  : {status}", (x1 + 25, y1 + 135),
                cv2.FONT_HERSHEY_SIMPLEX, 0.58, (220, 220, 220), 1)

    cv2.putText(frame, f"FPS: {int(fps)}", (x1 + 25, y1 + 168),
                cv2.FONT_HERSHEY_SIMPLEX, 0.5, (200, 200, 200), 1)

    cv2.putText(frame, f"Confidence: {confidence}", (x1 + 125, y1 + 168),
                cv2.FONT_HERSHEY_SIMPLEX, 0.5, (200, 200, 200), 1)

    cv2.putText(frame, f"Fingers: {fingers}", (x1 + 305, y1 + 168),
                cv2.FONT_HERSHEY_SIMPLEX, 0.5, (200, 200, 200), 1)

    bar_x1 = x1 + 25
    bar_y1 = y1 + 190
    bar_x2 = x2 - 25
    bar_y2 = y1 + 207

    cv2.rectangle(frame, (bar_x1, bar_y1), (bar_x2, bar_y2), (80, 80, 80), 1)

    fill_width = int((bar_x2 - bar_x1) * progress)
    cv2.rectangle(frame, (bar_x1, bar_y1), (bar_x1 + fill_width, bar_y2), (0, 255, 130), -1)

    cv2.putText(frame, "Q = Quit | ESC Gesture = Exit Slideshow",
                (35, h - 35),
                cv2.FONT_HERSHEY_SIMPLEX, 0.65, (230, 230, 230), 1)


while True:
    success, frame = cap.read()

    if not success:
        break

    frame = cv2.flip(frame, 1)
    h, w, _ = frame.shape

    now = time.time()
    fps = 1 / max((now - prev_time), 0.001)
    prev_time = now

    rgb_frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
    mp_image = mp.Image(image_format=mp.ImageFormat.SRGB, data=rgb_frame)

    detection_result = hand_landmarker.detect(mp_image)

    gesture_name = "No Hand"
    detected_action = "Show your hand"
    fingers_count = 0
    confidence_text = "0%"
    status = "Waiting"
    progress = 0

    if detection_result.hand_landmarks:
        hand_landmarks = detection_result.hand_landmarks[0]

        draw_hand(frame, hand_landmarks, w, h)

        fingers = fingers_up(hand_landmarks)
        fingers_count = fingers.count(1)

        gesture_code, gesture_name, detected_action = get_gesture(fingers_count)

        if detection_result.handedness:
            confidence = detection_result.handedness[0][0].score
            confidence_text = f"{confidence * 100:.1f}%"

        if gesture_code == last_gesture:
            stable_count += 1
        else:
            stable_count = 0
            last_gesture = gesture_code

        progress = min(stable_count / required_stable_frames, 1)

        if gesture_code != "WAIT":
            status = "Tracking"
        else:
            status = "Waiting"

        if (
            gesture_code != "WAIT"
            and stable_count >= required_stable_frames
            and now - last_action_time > cooldown
        ):
            action_text = perform_action(gesture_code)
            speak(action_text)

            last_action_time = now
            stable_count = 0
            status = "Action Done"
        else:
            action_text = detected_action

    else:
        stable_count = 0
        action_text = "Show your hand"

    cv2.rectangle(frame, (10, 10), (w - 10, h - 10), (0, 255, 130), 2)

    draw_panel(
        frame,
        gesture_name,
        action_text,
        fps,
        confidence_text,
        progress,
        fingers_count,
        status
    )

    cv2.imshow(WINDOW_NAME, frame)

    if cv2.waitKey(1) & 0xFF == ord("q"):
        break


cap.release()
cv2.destroyAllWindows()