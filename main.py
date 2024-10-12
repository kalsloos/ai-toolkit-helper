import tkinter as tk
from tkinter import ttk
import subprocess
import atexit
import os
import sys
import threading
from gui.captioning import create_captioning_tab
from gui.training import create_training_tab
from gui.config_generator import create_config_generator_tab
from gui.settings import create_settings_tab, load_config

class App(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title("AI Toolkit Helper")
        self.geometry("1200x1000")
        self.minsize(1200, 900)

        # Shared Variable: AI Toolkit Folder Path
        self.ai_toolkit_folder = tk.StringVar()

        # Load existing configuration
        self.config = load_config()
        self.ai_toolkit_folder.set(self.config.get("ai_toolkit_folder", ""))

        # Create tabs
        tab_control = ttk.Notebook(self)

        # Create different frames for each tab
        captioning_tab = ttk.Frame(tab_control)
        config_generator_tab = ttk.Frame(tab_control)
        training_tab = ttk.Frame(tab_control)
        settings_tab = ttk.Frame(tab_control)

        # Add tabs to the notebook
        tab_control.add(captioning_tab, text='Image Captioning')
        tab_control.add(config_generator_tab, text='Config Generator')
        tab_control.add(training_tab, text='Training')
        tab_control.add(settings_tab, text='Settings')

        tab_control.pack(expand=1, fill='both')

        # Call functions to build the tabs
        create_captioning_tab(captioning_tab)
        create_config_generator_tab(config_generator_tab, self.ai_toolkit_folder)
        create_training_tab(training_tab, self.ai_toolkit_folder)
        self.telegram_enabled = create_settings_tab(settings_tab, self.ai_toolkit_folder)

        # Bind the telegram_enabled variable to update_telegram_monitoring
        self.telegram_enabled.trace_add("write", self.update_telegram_monitoring)

        # Start Telegram monitoring if enabled
        self.telegram_process = None
        self.update_telegram_monitoring()

        # Bind the close event
        self.protocol("WM_DELETE_WINDOW", self.on_closing)

    def update_telegram_monitoring(self, *args):
        if self.telegram_enabled.get():
            self.start_telegram_monitoring()
        else:
            self.stop_telegram_monitoring()

    def start_telegram_monitoring(self):
        if not self.telegram_process:
            venv_python = os.path.join(self.ai_toolkit_folder.get(), 'venv', 'Scripts', 'python.exe')
            if not os.path.exists(venv_python):
                venv_python = os.path.join(self.ai_toolkit_folder.get(), 'venv', 'bin', 'python')
            
            if os.path.exists(venv_python):
                telegram_script = os.path.join(os.path.dirname(os.path.abspath(__file__)), "telegram_monitor.py")
                self.telegram_process = subprocess.Popen([venv_python, telegram_script], 
                                                         stdout=subprocess.PIPE, 
                                                         stderr=subprocess.PIPE, 
                                                         universal_newlines=True)
                
                # Start a thread to read the output
                threading.Thread(target=self.read_telegram_output, daemon=True).start()
            else:
                print("Virtual environment Python not found. Telegram monitoring not started.")

    def read_telegram_output(self):
        for line in self.telegram_process.stdout:
            print("Telegram monitor:", line.strip())
        for line in self.telegram_process.stderr:
            print("Telegram monitor error:", line.strip())

    def stop_telegram_monitoring(self):
        if self.telegram_process:
            self.telegram_process.terminate()
            self.telegram_process = None

    def on_closing(self):
        self.stop_telegram_monitoring()
        self.destroy()

if __name__ == "__main__":
    app = App()
    atexit.register(app.stop_telegram_monitoring)
    app.mainloop()