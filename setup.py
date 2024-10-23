# setup.py
import os
import subprocess
import sys

def check_requirements():
    try:
        import flask
        import pyautogui
        import qrcode
        import pyngrok
        print("All required packages are installed.")
    except ImportError as e:
        print(f"Missing package: {e.name}")
        print("Installing required packages...")
        subprocess.check_call([sys.executable, "-m", "pip", "install", 
                             "flask", "pyautogui", "qrcode", "pyngrok", "pillow"])

def main():
    print("Checking requirements...")
    check_requirements()
    
    print("\nStarting Mouse Controller Server...")
    os.system(f"{sys.executable} app.py")

if __name__ == "__main__":
    main()