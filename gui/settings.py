import os
import json
import tkinter as tk
from tkinter import filedialog, messagebox, ttk
import asyncio
from telegram import Bot
from telegram.error import TelegramError
from cryptography.fernet import Fernet, InvalidToken
import base64

CONFIG_FILE = "ai_toolkit_helper_config.json"
KEY_FILE = "encryption_key.key"

def generate_key():
    return Fernet.generate_key()

def load_or_create_key():
    if os.path.exists(KEY_FILE):
        with open(KEY_FILE, "rb") as key_file:
            return key_file.read()
    else:
        key = generate_key()
        with open(KEY_FILE, "wb") as key_file:
            key_file.write(key)
        return key

def is_encrypted(value):
    try:
        # Check if the value is a valid base64 string
        base64.b64decode(value)
        return True
    except:
        return False

def encrypt_value(value, key):
    f = Fernet(key)
    return base64.b64encode(f.encrypt(value.encode())).decode()

def decrypt_value(encrypted_value, key):
    if not is_encrypted(encrypted_value):
        return encrypted_value  # Return as-is if it's not encrypted
    try:
        f = Fernet(key)
        return f.decrypt(base64.b64decode(encrypted_value)).decode()
    except (InvalidToken, UnicodeDecodeError):
        # If decryption fails, return the original value
        return encrypted_value

def load_config():
    key = load_or_create_key()
    if os.path.exists(CONFIG_FILE):
        with open(CONFIG_FILE, 'r') as config_file:
            config = json.load(config_file)
            if 'telegram_bot_token' in config:
                config['telegram_bot_token'] = decrypt_value(config['telegram_bot_token'], key)
            if 'telegram_chat_id' in config:
                config['telegram_chat_id'] = decrypt_value(config['telegram_chat_id'], key)
            return config
    return {}

def save_config(config):
    key = load_or_create_key()
    config_to_save = config.copy()
    if 'telegram_bot_token' in config_to_save:
        config_to_save['telegram_bot_token'] = encrypt_value(config_to_save['telegram_bot_token'], key)
    if 'telegram_chat_id' in config_to_save:
        config_to_save['telegram_chat_id'] = encrypt_value(config_to_save['telegram_chat_id'], key)
    with open(CONFIG_FILE, 'w') as config_file:
        json.dump(config_to_save, config_file)

class TelegramNotifier:
    def __init__(self, token, chat_id):
        self.token = token
        self.chat_id = chat_id
        self.bot = Bot(token=self.token)

    async def send_message(self, message):
        try:
            await self.bot.send_message(chat_id=self.chat_id, text=message)
            print(f"Telegram message sent: {message}")
        except TelegramError as e:
            print(f"Failed to send Telegram message: {e}")

def create_settings_tab(settings_tab, ai_toolkit_folder):
    # Load existing configuration
    config = load_config()

    # Set up text variables
    ai_toolkit_folder.set(config.get("ai_toolkit_folder", ""))
    telegram_bot_token = tk.StringVar(value=config.get("telegram_bot_token", ""))
    telegram_chat_id = tk.StringVar(value=config.get("telegram_chat_id", ""))
    telegram_enabled = tk.BooleanVar(value=config.get("telegram_enabled", False))

    # Create a main frame for all settings
    main_frame = ttk.Frame(settings_tab)
    main_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)

    # AI Toolkit Settings
    ttk.Label(main_frame, text="AI Toolkit Settings", font=("TkDefaultFont", 12, "bold")).grid(row=0, column=0, columnspan=3, sticky="w", padx=5, pady=5)

    ttk.Label(main_frame, text="AI Toolkit Installation Folder:").grid(row=1, column=0, sticky="w", padx=5, pady=5)
    folder_path_entry = ttk.Entry(main_frame, textvariable=ai_toolkit_folder, width=50)
    folder_path_entry.grid(row=1, column=1, padx=5, pady=5)

    def browse_ai_toolkit_folder():
        folder_selected = filedialog.askdirectory()
        if folder_selected:
            ai_toolkit_folder.set(folder_selected)

    browse_button = ttk.Button(main_frame, text="Browse", command=browse_ai_toolkit_folder)
    browse_button.grid(row=1, column=2, padx=5, pady=5)

    # Separator
    ttk.Separator(main_frame, orient='horizontal').grid(row=2, column=0, columnspan=3, sticky="ew", pady=10)

    # Telegram Settings
    ttk.Label(main_frame, text="Telegram Notifications", font=("TkDefaultFont", 12, "bold")).grid(row=3, column=0, columnspan=3, sticky="w", padx=5, pady=5)

    ttk.Checkbutton(main_frame, text="Enable Telegram Notifications", variable=telegram_enabled).grid(row=4, column=0, columnspan=3, sticky="w", padx=5, pady=5)

    ttk.Label(main_frame, text="Telegram Bot Token:").grid(row=5, column=0, sticky="w", padx=5, pady=5)
    ttk.Entry(main_frame, textvariable=telegram_bot_token, width=50, show="*").grid(row=5, column=1, columnspan=2, padx=5, pady=5)

    ttk.Label(main_frame, text="Telegram Chat ID:").grid(row=6, column=0, sticky="w", padx=5, pady=5)
    ttk.Entry(main_frame, textvariable=telegram_chat_id, width=50).grid(row=6, column=1, columnspan=2, padx=5, pady=5)

    # Instructions for Telegram setup
    instructions = (
        "To set up Telegram notifications:\n"
        "1. Create a new bot using BotFather on Telegram:\n"
        "   - Open Telegram and search for @BotFather\n"
        "   - Send /newbot and follow the instructions\n"
        "2. Copy the Bot Token provided by BotFather and paste it above\n"
        "3. Start a chat with your new bot\n"
        "4. Visit https://api.telegram.org/bot<YourBOTToken>/getUpdates\n"
        "5. Find your Chat ID in the JSON response and paste it above\n"
        "6. Click 'Test Connection' to verify your settings"
    )
    ttk.Label(main_frame, text=instructions, justify=tk.LEFT, wraplength=400).grid(row=7, column=0, columnspan=3, padx=5, pady=10)

    def test_telegram_connection():
        bot_token = telegram_bot_token.get()
        chat_id = telegram_chat_id.get()
        
        if not bot_token or not chat_id:
            messagebox.showerror("Error", "Please enter both Bot Token and Chat ID.")
            return

        async def send_test_message():
            try:
                notifier = TelegramNotifier(bot_token, chat_id)
                await notifier.send_message("Test message from AI Toolkit Helper!")
                messagebox.showinfo("Success", "Test message sent successfully!")
            except Exception as e:
                messagebox.showerror("Error", f"Failed to send test message: {str(e)}")

        asyncio.run(send_test_message())

    test_button = ttk.Button(main_frame, text="Test Connection", command=test_telegram_connection)
    test_button.grid(row=8, column=0, columnspan=3, pady=10)

    # Save Button
    def save_settings():
        config["ai_toolkit_folder"] = ai_toolkit_folder.get()
        config["telegram_bot_token"] = telegram_bot_token.get()
        config["telegram_chat_id"] = telegram_chat_id.get()
        config["telegram_enabled"] = telegram_enabled.get()
        save_config(config)
        messagebox.showinfo("Settings Saved", "Settings have been saved successfully.")

    save_button = ttk.Button(main_frame, text="Save All Settings", command=save_settings)
    save_button.grid(row=9, column=0, columnspan=3, pady=10)

    return telegram_enabled  # Return this so we can use it in the main app to control the background script