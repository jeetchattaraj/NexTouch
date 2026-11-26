import speech_recognition as sr
import pyttsx3
import webbrowser
import os
import pyautogui
import time
import pygetwindow as gw
import urllib.parse

def speak(text):
    """System ko bolkar reply dene ke liye (Crash-Safe)"""
    try:
        engine = pyttsx3.init()
        engine.setProperty('rate', 175)
        engine.say(text)
        engine.runAndWait()
    except Exception as e:
        print(f"[TTS Error]: {e}")

def open_desktop_app(app_name):
    """Windows Start Menu se koi bhi downloaded app open karne ke liye"""
    pyautogui.press("win")
    time.sleep(0.5)
    pyautogui.write(app_name, interval=0.05)
    time.sleep(0.5)
    pyautogui.press("enter")

def execute_command(command):
    command = command.lower()
    print(f"[Voice Command]: {command}")

    # 1. Video Pause / Stop / Resume Controls (Isse sabse upar rakhein)
    if command in ["pause", "stop", "pause video", "stop video", "top", "top video", "rok do", "ruko", "video ko rok do"]:
        pyautogui.press("playpause")
        speak("Paused")

    elif command in ["play", "resume", "play video", "start", "chalu karo", "chala do", "video ko chala do"]:
        pyautogui.press("playpause")
        speak("Playing")

    # 2. YouTube Desktop App me Search karke Play karna (Already open check ke saath)
    elif command.startswith("play ") or "play " in command:
        song = command.replace("play", "").strip()
        if not song or song == "music":
            song = "trending hindi songs"

        speak(f"Playing {song}")

        # Check karna ki YouTube App pehle se khula hai ya nahi (Chrome/Edge ko ignore karke)
        yt_windows = [
            w for w in gw.getWindowsWithTitle("YouTube")
            if "Chrome" not in w.title and "Edge" not in w.title
        ]

        if yt_windows:
            yt_win = yt_windows[0]
            try:
                if yt_win.isMinimized:
                    yt_win.restore()
                pyautogui.press("alt")   # Windows focus issue fix
                yt_win.activate()
                yt_win.maximize()
            except Exception:
                pass
            time.sleep(0.8)
        else:
            open_desktop_app("YouTube")
            time.sleep(3.5)
            pyautogui.hotkey("win", "up")
            time.sleep(0.5)

        # YouTube search bar me type karke search karna
        pyautogui.press("/")
        time.sleep(0.4)
        pyautogui.hotkey("ctrl", "a")
        pyautogui.press("backspace")
        pyautogui.write(song, interval=0.05)
        pyautogui.press("enter")

        time.sleep(3.5)                        # Results load hone ka wait
        screen_w, screen_h = pyautogui.size()

        # Mouse ko beech me la kar thoda neeche scroll karna (Ad skip karne ke liye)
        pyautogui.moveTo(int(screen_w * 0.35), int(screen_h * 0.45), duration=0.2)
        pyautogui.scroll(-400)                 # Upar ki Sponsored Ad ko bypass karega
        time.sleep(0.5)

        # Ab real video par click karna
        pyautogui.click(int(screen_w * 0.35), int(screen_h * 0.45))
    # 2. Downloaded Desktop Apps Open Karna
    elif "open youtube" in command:
        speak("Opening YouTube app")
        open_desktop_app("YouTube")

    elif "open whatsapp" in command:
        speak("Opening WhatsApp")
        open_desktop_app("WhatsApp")

    elif "open spotify" in command:
        speak("Opening Spotify")
        open_desktop_app("Spotify")

    elif "open gemini" in command:
            speak("Opening Gemini")
            open_desktop_app("Gemini")

    elif "open vs code" in command or  "open visual studio code" in command:
            speak("Opening Visual Studio Code")
            open_desktop_app("Visual Studio Code")

    elif "open pinterest" in command or "pinterest" in command:
        speak("Opening Pinterest")
        open_desktop_app("Pinterest")

    elif "open google" in command:
        speak("Opening Google")
        webbrowser.open("https://www.google.com")

    elif "open github" in command:
        speak("Opening GitHub")
        webbrowser.open("https://www.github.com")

    # 3. Laptop Apps Open Karna
    elif "open notepad" in command:
        speak("Opening Notepad")
        os.system("start notepad")

    elif "open calculator" in command:
        speak("Opening Calculator")
        os.system("start calc")

    elif "open chrome" in command:
        speak("Opening Chrome")
        os.system("start chrome")

    # 4. Browser & Quick System Controls (Smart Keyword Matching)
    elif "browser" in command or "edge" in command:
        speak("Opening Microsoft Edge")
        os.system("start msedge")

    elif "tab" in command and ("close" in command or "close tab" in command or "band" in command or "hatado" in command or "se" in command or "remove" in command):
        pyautogui.hotkey("ctrl", "w")
        speak("Tab closed")

    elif "desktop" in command or "minimize" in command or "mize" in command or "home screen" in command:
        pyautogui.hotkey("win", "d")
        speak("Desktop ready")

    elif "maximize" in command:
        app_name = command.replace("maximize", "").strip()

        # Agar sirf "maximize" bola -> jo window abhi khuli hai wahi maximize hogi
        if not app_name:
            pyautogui.hotkey("win", "up")
            speak("Maximized")
        else:
            # Saari open ya minimized windows me se app ka naam match karna
            matched_windows = [
                w for w in gw.getAllWindows()
                if w.title and app_name in w.title.lower()
            ]

            if matched_windows:
                target_win = matched_windows[0]
                try:
                    if target_win.isMinimized:
                        target_win.restore()
                    pyautogui.press("alt")      # Windows focus lock hatane ke liye
                    target_win.activate()
                    target_win.maximize()
                    speak(f"Maximizing {app_name}")
                except Exception:
                    speak(f"Could not maximize {app_name}")
            else:
                speak(f"{app_name} is not open")

    elif "search" in command:
        # "search about", "search for", ya "search" hata kar sirf topic nikalna
        query = command.replace("search about", "").replace("search for", "").replace("search", "").strip()

        if query:
            speak(f"Searching {query} on Microsoft Edge")
            encoded_query = urllib.parse.quote(query)
            os.system(f'start msedge "https://www.google.com/search?q={encoded_query}"')
        else:
            speak("What should I search?")

    elif "screenshot" in command or "screen shot" in command or "capture" in command:
        timestamp = int(time.time())
        pyautogui.screenshot(f"Voice_SS_{timestamp}.png")
        speak("Screenshot saved")

def start_voice_assistant():
    """Background me lagatar sunne wala loop (Viva-Room Noise Safe)"""
    recognizer = sr.Recognizer()
    recognizer.energy_threshold = 350            # Door ki halki aawaz ignore karega
    recognizer.dynamic_energy_threshold = True   # Room ke shor ke hisaab se auto-adjust
    recognizer.pause_threshold = 0.65            # Bolna band karte hi fast response

    try:
        mic = sr.Microphone()
        with mic as source:
            print("[Voice Assistant]: Calibrating for room noise...")
            recognizer.adjust_for_ambient_noise(source, duration=1.2)
            print("[Voice Assistant]: Ready! Listening in background...")
            speak("NexTouch is online and ready")
    except Exception as e:
        print(f"[Mic Init Error]: {e}")
        return

    while True:
        try:
            with mic as source:
                audio = recognizer.listen(source, timeout=3, phrase_time_limit=5)
            command = recognizer.recognize_google(audio, language="en-IN")
            execute_command(command)
        except sr.WaitTimeoutError:
            pass
        except sr.UnknownValueError:
            pass
        except sr.RequestError:
            # Internet slow ya off hone par crash/spam nahi hoga
            print("[Voice Assistant]: Network issue, retrying...")
            time.sleep(2)
        except Exception as e:
            print(f"[Voice Error]: {e}")
            time.sleep(1)

            