# NexTouch — Multi-Modal Touchless HCI

**NexTouch** is a real-time, touchless Human-Computer Interface (HCI) for Windows that combines **offline hand-gesture recognition** with a **noise-safe background voice assistant**. Built using only a standard laptop webcam and microphone, it enables smooth, hands-free desktop navigation, media control, and presentation management without any external sensors.

---

## Key Features

- **Touchpad-Style Relative Cursor:** Smooth two-finger cursor movement with a 3-pixel anti-jitter deadzone—lift your hand to reposition without the cursor jumping back.
- **Zero-Clash Gesture Controls:** Intuitive single-hand and two-hand gestures for clicking, scrolling, volume control, screenshots, window management, and PowerPoint slide navigation.
- **Thumb-Tilt PPT Joystick:** Neutral upright-thumb lock prevents accidental double slide-skips during presentations.
- **Semi-Transparent Glass HUD:** Clean live camera overlay displaying the active gesture mode, voice assistant status, real-time FPS, and a bottom control cheat-sheet.
- **Viva-Room Noise-Safe Voice Assistant:** Runs concurrently on a daemon thread with automatic ambient noise calibration, dynamic energy thresholding, and crash-safe network recovery.
- **One-Click Desktop Launcher:** Includes a Windows `.bat` launcher (`Launch_NexTouch.bat`) for standalone app-like startup.

---

## Hand Gesture Controls

| Feature | Gesture / Hand Pose | Action |
| :--- | :--- | :--- |
| **Move Cursor** | Index + Middle straight & touching | Relative touchpad-style cursor movement |
| **Left Click** | Slight tilt of Middle finger (Index straight) | Single Left Click |
| **Right Click** | Slight tilt of Index finger (Middle straight) | Single Right Click |
| **Double Click** | Slight tilt of both Index & Middle fingers | Double Left Click |
| **Freeze Cursor** | Open Palm (All 5 fingers up) | Pauses cursor to reposition hand |
| **Vertical Scroll** | Closed Fist moved Up / Down | Scrolls active window Up / Down |
| **Volume Control** | 3 Fingers Up (Index + Middle + Ring) | Move Up / Down to increase / decrease volume |
| **PPT Slides** | Thumb Up + 4 Fingers Closed (Tilt Left/Right) | Previous / Next slide (return thumb upright to reset) |
| **Screenshot** | Rock / Yo Sign (Index + Pinky up, hold) | Saves timestamped PNG screenshot |
| **Window Control** | Two Hands: Open Palms $\leftrightarrow$ Closed Fists | Maximize / Minimize active window |

*Press **`Q`** in the camera window at any time to exit cleanly.*

---

## Voice Commands

The background voice assistant listens continuously and supports natural commands (English / Hinglish):

- **Media:** `"play <song name>"` (opens YouTube Desktop App & bypasses sponsored ads), `"pause"` / `"stop"` / `"rok do"`, `"resume"` / `"chala do"`
- **Desktop Apps:** `"open youtube"`, `"open whatsapp"`, `"open spotify"`, `"open vs code"`, `"open gemini"`, `"open pinterest"`, `"open notepad"`, `"open calculator"`, `"open chrome"`, `"open edge"`
- **Web & Search:** `"open google"`, `"open github"`, `"search <topic>"`
- **System Controls:** `"close tab"`, `"minimize"` / `"desktop"`, `"maximize <app name>"`, `"screenshot"`

---

## Tech Stack

- **Computer Vision:** OpenCV, MediaPipe, cvzone, NumPy
- **Voice & Speech:** SpeechRecognition (Google Speech API), pyttsx3, Python `threading`
- **OS & Window Automation:** PyAutoGUI, pynput, PyGetWindow, PyCaw

---

## Project Structure

```text
NexTouch/
├── app.py                  # Main CV engine, gesture logic & Glass HUD
├── voice_assistant.py      # Background daemon thread for noise-safe voice control
├── Launch_NexTouch.bat     # One-click Windows desktop launcher
├── requirements.txt        # Python dependencies
├── .gitignore              # Git ignore rules
└── README.md               # Project documentation
```

---

## Setup & Installation

1. **Clone the repository**
   ```bash
   git clone https://github.com/<your-username>/NexTouch.git
   cd NexTouch
   ```

2. **Install dependencies** *(Python 3.10+ recommended on Windows)*
   ```bash
   pip install -r requirements.txt
   ```

3. **Run NexTouch**
   - Double-click **`Launch_NexTouch.bat`**, or run via terminal:
     ```bash
     python app.py
     ```

---

## Future Scope

- **100% Offline Speech AI:** Integrating a local Whisper / Vosk model with custom wake-word detection (`"Hey NexTouch"`).
- **Visual Settings Dashboard:** GUI for custom gesture remapping and sensitivity sliders.
- **IoT & Accessibility:** Expanding touchless controls to smart-home devices and gaze-assisted navigation.