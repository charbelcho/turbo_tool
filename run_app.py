import sys
import subprocess
import time
import webview
import requests
import atexit
import os
import signal

# Globaler Prozess-Handle
streamlit_process = None


def is_streamlit_running():
    """Prüft ob Streamlit bereits läuft"""
    try:
        response = requests.get("http://localhost:8501", timeout=2)
        return True
    except:
        return False


def start_streamlit():
    """Startet Streamlit nur wenn nicht bereits läuft"""
    global streamlit_process

    if not is_streamlit_running():
        cmd = [sys.executable, "-m", "streamlit", "run", "app.py",
               "--server.headless=true", "--server.port=8501"]
        streamlit_process = subprocess.Popen(cmd)
        print("Streamlit wird gestartet...")

        # Warten bis Streamlit bereit ist
        for i in range(30):  # Max 30 Versuche
            if is_streamlit_running():
                print("Streamlit ist bereit")
                return True
            time.sleep(1)

        print("Streamlit konnte nicht gestartet werden")
        return False
    else:
        print("Streamlit läuft bereits")
        return True


def cleanup():
    """Beendet Streamlit Prozess beim Beenden der App"""
    global streamlit_process
    if streamlit_process:
        print("Beende Streamlit Prozess...")
        # Unter Windows
        if os.name == 'nt':
            streamlit_process.terminate()
        # Unter Unix/Linux/Mac
        else:
            os.killpg(os.getpgid(streamlit_process.pid), signal.SIGTERM)
        streamlit_process.wait()


# Cleanup bei Programmende registrieren
atexit.register(cleanup)


def main():
    if start_streamlit():
        webview.create_window("Turbo Tool", "http://localhost:8501", width=1200, height=800)
        webview.start()
    else:
        print("Fehler: Streamlit konnte nicht gestartet werden")


if __name__ == "__main__":
    main()

