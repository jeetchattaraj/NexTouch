import cv2
import numpy as np
from cvzone.HandTrackingModule import HandDetector
from pynput.mouse import Controller, Button
import math
import pyautogui
import time
import threading
from voice_assistant import start_voice_assistant

# --- Windows Volume Control Setup (PyCaw) ---
from ctypes import cast, POINTER
from comtypes import CLSCTX_ALL
from pycaw.pycaw import AudioUtilities, IAudioEndpointVolume

try:
    devices = AudioUtilities.GetSpeakers()
    interface = devices.Activate(IAudioEndpointVolume._iid_, CLSCTX_ALL, None)
    volume_ctrl = cast(interface, POINTER(IAudioEndpointVolume))
    vol_range = volume_ctrl.GetVolumeRange()
    min_vol, max_vol = vol_range[0], vol_range[1]
    AUDIO_ENABLED = True
except Exception as e:
    print(f"Audio control unavailable: {e}")
    AUDIO_ENABLED = False

# --- Camera & Detector Setup ---
mouse = Controller()
cap = cv2.VideoCapture(0)
cam_w, cam_h = 640, 480
cap.set(3, cam_w)
cap.set(4, cam_h)

detector = HandDetector(detectionCon=0.8, maxHands=2)

# Active workspace box
# frame_r = 45
frame_r_x = 45        # Left & Right se chauda area
frame_r_top = 50      # Top se HUD ke bilkul neeche
frame_r_bottom = 50  # Bottom ko upar rakhega taaki Taskbar aaram se mile
prev_x, prev_y = 0, 0
prev_hand_x, prev_hand_y = 0, 0
cursor_speed = 2.8   # Speed kam/zyada karne ke liye (2.0 se 3.5 ke beech rakhein)
curr_x, curr_y = 0, 0
smooth_factor = 2.5

# Screen dimensions
try:
    import tkinter as tk
    root = tk.Tk()
    screen_w = root.winfo_screenwidth()
    screen_h = root.winfo_screenheight()
    root.destroy()
except:
    screen_w, screen_h = 1920, 1080

# --- Tuning Thresholds ---
TOUCH_THRESHOLD = 45       # Index + Middle touch distance
TILT_THRESHOLD = 22        # Thoda sa tilt detect karne ke liye (Tip to PIP vertical distance)
CLICK_HOLD_FRAMES = 3      # Fast & steady click response
FIST_HOLD_FRAMES = 22      # ~0.8 - 1.0 sec hold for Screenshot

left_hold = 0
right_hold = 0
double_hold = 0
fist_hold = 0
prev_vol_y = 0

left_locked = False
right_locked = False
double_locked = False
volume_mode = False

prev_scroll_y = 0
last_screenshot_time = 0
last_window_action_time = 0
two_hand_state = None
prev_frame_time = 0
ppt_ready = True
last_ppt_time = 0

# --- Background Voice Assistant Thread ---
voice_thread = threading.Thread(target=start_voice_assistant, daemon=True)
voice_thread.start()

def calc_dist(p1, p2):
    return math.hypot(p1[0] - p2[0], p1[1] - p2[1])

while cap.isOpened():
    success, frame = cap.read()
    if not success:
        break

    frame = cv2.flip(frame, 1)
    hands, frame = detector.findHands(frame, draw=False)

    curr_time = time.time()
    fps = int(1 / (curr_time - prev_frame_time)) if (curr_time - prev_frame_time) > 0 else 0
    prev_frame_time = curr_time

    # cv2.rectangle(frame, (frame_r, frame_r), (cam_w - frame_r, cam_h - frame_r), (255, 0, 255), 2)
    cv2.rectangle(frame, (frame_r_x, frame_r_top), (cam_w - frame_r_x, cam_h - frame_r_bottom), (255, 0, 255), 2)

    current_mode = "Idle / Ready"
    mode_color = (200, 200, 200)

    # ==========================================================
    # 8. TWO-HAND GESTURES (Maximize & Minimize with Fists)
    # ==========================================================
    if len(hands) == 2:
        f1 = detector.fingersUp(hands[0])
        f2 = detector.fingersUp(hands[1])

        both_open = (sum(f1) >= 4 and sum(f2) >= 4)
        # Dono haathon ki mutthi band (4 fingers closed on both hands)
        both_fists = (f1[1:] == [0, 0, 0, 0] and f2[1:] == [0, 0, 0, 0])

        if both_fists:
            current_mode = "2 Hands: Closed Fists"
            mode_color = (0, 165, 255)
            if two_hand_state == "open" and (curr_time - last_window_action_time > 1.5):
                pyautogui.hotkey('win', 'down')
                current_mode = "Window Minimized!"
                mode_color = (0, 0, 255)
                last_window_action_time = curr_time
            two_hand_state = "fist"

        elif both_open:
            current_mode = "2 Hands: Open Palm"
            mode_color = (0, 255, 0)
            if two_hand_state == "fist" and (curr_time - last_window_action_time > 1.5):
                pyautogui.hotkey('win', 'up')
                current_mode = "Window Maximized!"
                mode_color = (0, 255, 0)
                last_window_action_time = curr_time
            two_hand_state = "open"

    # ==========================================================
    # SINGLE-HAND GESTURES
    # ==========================================================
    elif len(hands) == 1:
        two_hand_state = None
        hand = hands[0]
        lmList = hand["lmList"]
        fingers = detector.fingersUp(hand)  # [Thumb, Index, Middle, Ring, Pinky]

        x_thumb, y_thumb = lmList[4][0], lmList[4][1]
        x_index, y_index = lmList[8][0], lmList[8][1]
        x_middle, y_middle = lmList[12][0], lmList[12][1]

        dist_index_middle = math.hypot(x_index - x_middle, y_index - y_middle)
        dist_thumb_index = math.hypot(x_thumb - x_index, y_thumb - y_index)

        # Angle-independent check for PPT Thumb-Tilt (4 fingers closed + Thumb clearly open)
        wrist = lmList[0]
        four_fingers_closed = (
            calc_dist(lmList[8], wrist) < calc_dist(lmList[6], wrist) and
            calc_dist(lmList[12], wrist) < calc_dist(lmList[10], wrist) and
            calc_dist(lmList[16], wrist) < calc_dist(lmList[14], wrist) and
            calc_dist(lmList[20], wrist) < calc_dist(lmList[18], wrist)
        )
        thumb_open = calc_dist(lmList[4], lmList[5]) > 48

        # --- 10. CURSOR FREEZE (All 5 Fingers Open / Palm) ---
        if fingers == [1, 1, 1, 1, 1]:
            current_mode = "Cursor Frozen (Palm)"
            mode_color = (0, 0, 255)
            prev_scroll_y = 0
            fist_hold = 0
            volume_mode = False
            prev_hand_x, prev_hand_y = 0, 0   # <-- YEH LINE ADD KAREIN

        # --- 11. PPT SLIDE CONTROL (Thumb Open + 4 Fingers Closed -> Tilt Left/Right) ---
        elif four_fingers_closed and thumb_open:
            prev_scroll_y = 0
            prev_vol_y = 0
            fist_hold = 0

            dx = lmList[4][0] - lmList[2][0]  # Thumb Tip X - Thumb Base X
            dy = lmList[4][1] - lmList[2][1]  # Thumb Tip Y - Thumb Base Y

            cv2.circle(frame, (x_thumb, y_thumb), 10, (255, 0, 255), cv2.FILLED)

            # Neutral Position: Thumb seedha upar -> Ready for next tilt
            if dy < -30 and abs(dx) < 35:
                ppt_ready = True
                current_mode = "PPT: Ready (Tilt Left/Right)"
                mode_color = (0, 255, 0)

            # Tilt Detection (0.7 sec cooldown ke saath)
            elif ppt_ready and (curr_time - last_ppt_time > 0.7):
                # Right Tilt -> Next Slide
                if dx > 40 and abs(dx) > abs(dy):
                    pyautogui.press("right")
                    ppt_ready = False
                    last_ppt_time = curr_time
                    current_mode = "PPT: Next Slide ->"
                    mode_color = (0, 255, 0)

                # Left Tilt -> Previous Slide
                elif dx < -40 and abs(dx) > abs(dy):
                    pyautogui.press("left")
                    ppt_ready = False
                    last_ppt_time = curr_time
                    current_mode = "PPT: <- Previous Slide"
                    mode_color = (0, 165, 255)
            else:
                current_mode = "PPT: Bring Thumb Up to Reset"
                mode_color = (255, 0, 255)

        # --- 5. VERTICAL SCROLLING (Closed Fist / Mutthi Band) ---
        elif fingers[1:] == [0, 0, 0, 0]:
            prev_vol_y = 0
            fist_hold = 0
            current_mode = "Scroll Mode (Fist Up/Down)"
            mode_color = (0, 255, 255)

            # Mutthi ke center (Middle knuckle) ko track karna for zero jitter
            x_fist, y_fist = lmList[9][0], lmList[9][1]
            cv2.circle(frame, (x_fist, y_fist), 10, (0, 255, 255), cv2.FILLED)

            if prev_scroll_y != 0:
                diff = y_fist - prev_scroll_y
                if diff > 8:       # Mutthi neeche le jane par -> Scroll Down
                    mouse.scroll(0, -3)
                    current_mode = "Scrolling Down"
                elif diff < -8:    # Mutthi upar le jane par -> Scroll Up
                    mouse.scroll(0, 2)
                    current_mode = "Scrolling Up"
            prev_scroll_y = y_fist

        # --- 9. VOLUME CONTROL (3 Fingers: Index + Middle + Ring Up) ---
        elif fingers[1:] == [1, 1, 1, 0]:
            prev_scroll_y = 0
            fist_hold = 0
            current_mode = "Volume Mode (Move Up/Down)"
            mode_color = (255, 165, 0)

            cv2.circle(frame, (x_middle, y_middle), 10, (255, 165, 0), cv2.FILLED)

            if prev_vol_y != 0:
                diff = y_middle - prev_vol_y
                if diff < -8:      # Thoda sa upar -> Fast Volume UP
                    pyautogui.press("volumeup", presses=3)
                    current_mode = "Volume UP (++)"
                elif diff > 8:     # Thoda sa neeche -> Fast Volume DOWN
                    pyautogui.press("volumedown", presses=3)
                    current_mode = "Volume DOWN (--)"
            prev_vol_y = y_middle

        # --- 7. SCREENSHOT (Yo / Rock Sign: Index + Pinky Up, Middle + Ring Down) ---
        elif fingers[1:] == [1, 0, 0, 1]:
            prev_scroll_y = 0
            prev_vol_y = 0
            fist_hold += 1
            current_mode = f"Screenshot in... ({fist_hold}/10)"
            mode_color = (0, 255, 255)

            if fist_hold == 10 and (curr_time - last_screenshot_time > 2.0):
                timestamp = int(time.time())
                filename = f"NexTouch_SS_{timestamp}.png"
                pyautogui.screenshot(filename)
                last_screenshot_time = curr_time
                current_mode = "Screenshot Saved!"
                mode_color = (0, 255, 0)
                print(f"[Saved]: {filename}")
                # Camera screen par halka sa flash effect
                frame[:] = 255

        else:
            prev_scroll_y = 0
            prev_vol_y = 0
            fist_hold = 0

            # --- MOUSE NAVIGATION & SLIGHT TILT CLICKS (Ring & Pinky Closed) ---
            if fingers[3] == 0 and fingers[4] == 0:
                # Tip se middle joint (PIP) ki vertical height check karna
                index_straight_len = lmList[6][1] - y_index
                middle_straight_len = lmList[10][1] - y_middle

                index_tilted = index_straight_len < TILT_THRESHOLD
                middle_tilted = middle_straight_len < TILT_THRESHOLD

                # --- INSTANT UNLOCK: Jaise hi ungli wapas seedhi ho, lock reset ho jaye ---
                if not index_tilted:
                    right_locked = False
                    right_hold = 0
                if not middle_tilted:
                    left_locked = False
                    left_hold = 0
                if not index_tilted and not middle_tilted:
                    double_locked = False
                    double_hold = 0

                # 1. CURSOR MOVE (Touchpad / Relative Mode with Anti-Jitter)
                if not index_tilted and not middle_tilted and dist_index_middle < TOUCH_THRESHOLD:
                    current_mode = "Cursor Moving (Touchpad)"
                    mode_color = (255, 100, 100)

                    mid_x = (x_index + x_middle) // 2
                    mid_y = (y_index + y_middle) // 2

                    if prev_hand_x != 0 and prev_hand_y != 0:
                        raw_dx = mid_x - prev_hand_x
                        raw_dy = mid_y - prev_hand_y

                        # Deadzone: 3 pixel se kam hilne par ignore karein (No Vibration)
                        if math.hypot(raw_dx, raw_dy) > 3:
                            mouse.move(raw_dx * cursor_speed, raw_dy * cursor_speed)
                            prev_hand_x, prev_hand_y = mid_x, mid_y
                    else:
                        prev_hand_x, prev_hand_y = mid_x, mid_y

                    cv2.circle(frame, (mid_x, mid_y), 7, (255, 0, 0), cv2.FILLED)

                    
                # 2. RIGHT CLICK (Index thoda sa tilt, Middle straight)
                elif index_tilted and not middle_tilted:
                    right_hold += 1
                    cv2.circle(frame, (x_index, y_index), 10, (0, 165, 255), cv2.FILLED)
                    if right_hold >= CLICK_HOLD_FRAMES and not right_locked:
                        mouse.click(Button.right, 1)
                        right_locked = True
                        current_mode = "Right Click!"
                        mode_color = (0, 165, 255)

                # 3. LEFT CLICK (Middle thoda sa tilt, Index straight)
                elif middle_tilted and not index_tilted:
                    left_hold += 1
                    cv2.circle(frame, (x_middle, y_middle), 10, (0, 255, 0), cv2.FILLED)
                    if left_hold >= CLICK_HOLD_FRAMES and not left_locked:
                        mouse.click(Button.left, 1)
                        left_locked = True
                        current_mode = "Left Click!"
                        mode_color = (0, 255, 0)

                # 4. DOUBLE CLICK (Dono Index + Middle thoda sa tilt)
                elif index_tilted and middle_tilted:
                    double_hold += 1
                    cv2.circle(frame, (x_index, y_index), 10, (255, 255, 0), cv2.FILLED)
                    cv2.circle(frame, (x_middle, y_middle), 10, (255, 255, 0), cv2.FILLED)
                    if double_hold >= CLICK_HOLD_FRAMES and not double_locked:
                        mouse.click(Button.left, 2)
                        double_locked = True
                        current_mode = "Double Click!"
                        mode_color = (255, 255, 0)

    else:
        two_hand_state = None
        prev_hand_x, prev_hand_y = 0, 0       # <-- YEH LINE ADD KAREIN

        
# --- Clean Semi-Transparent HUD (Top & Bottom) ---
    overlay = frame.copy()

    # 1. Top & Bottom Dark Glass Bars
    cv2.rectangle(overlay, (0, 0), (cam_w, 42), (18, 18, 22), cv2.FILLED)
    cv2.rectangle(overlay, (0, cam_h - 30), (cam_w, cam_h), (18, 18, 22), cv2.FILLED)
    cv2.addWeighted(overlay, 0.72, frame, 0.28, 0, frame)

    # Subtle neon divider lines
    cv2.line(frame, (0, 42), (cam_w, 42), (180, 0, 255), 1)
    cv2.line(frame, (0, cam_h - 30), (cam_w, cam_h - 30), (80, 80, 90), 1)

    # 2. Top Left: Live Status Dot + Current Mode
    cv2.circle(frame, (20, 21), 6, mode_color, cv2.FILLED)
    cv2.putText(frame, f"{current_mode}", (35, 27), cv2.FONT_HERSHEY_SIMPLEX, 0.6, mode_color, 2, cv2.LINE_AA)

    # 3. Top Right: Voice Status Badge + FPS
    cv2.circle(frame, (cam_w - 195, 21), 5, (0, 255, 120), cv2.FILLED)
    cv2.putText(frame, "Voice: ON", (cam_w - 183, 26), cv2.FONT_HERSHEY_SIMPLEX, 0.52, (0, 255, 120), 1, cv2.LINE_AA)
    cv2.putText(frame, f"FPS: {fps}", (cam_w - 82, 26), cv2.FONT_HERSHEY_SIMPLEX, 0.55, (220, 220, 220), 1, cv2.LINE_AA)

    # 4. Bottom Bar: Quick Controls Hint
    hint_text = "2-Fingers: Cursor | Palm: Freeze | Fist: Scroll | Thumb: PPT | Q: Exit"
    cv2.putText(frame, hint_text, (18, cam_h - 10), cv2.FONT_HERSHEY_SIMPLEX, 0.45, (190, 190, 200), 1, cv2.LINE_AA)

    cv2.imshow("NexTouch: Gesture Controller", frame)

    if cv2.waitKey(1) & 0xFF == ord('q'):
        break

cap.release()
cv2.destroyAllWindows()

