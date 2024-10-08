import os
import json
import asyncio
import logging
import time
from queue import Queue, Empty
import telegram
from telegram.error import TelegramError
from watchdog.observers import Observer
from watchdog.events import FileSystemEventHandler

# Set up logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(message)s', datefmt='%Y-%m-%d %H:%M:%S')
logger = logging.getLogger(__name__)

# Reduce logging from telegram library
logging.getLogger('telegram').setLevel(logging.WARNING)
logging.getLogger('httpx').setLevel(logging.WARNING)

CONFIG_FILE = "ai_toolkit_helper_config.json"

class TelegramNotifier:
    def __init__(self, token, chat_id):
        self.token = token
        self.chat_id = chat_id
        self.bot = telegram.Bot(token=self.token)

    async def send_message(self, message):
        try:
            await self.bot.send_message(chat_id=self.chat_id, text=message)
            logger.info(f"Message sent: {message}")
        except TelegramError as e:
            logger.error(f"Failed to send message: {str(e)}")

    async def send_image(self, image_path, caption=None, max_retries=5, retry_delay=2, min_file_size=100):
        filename = os.path.basename(image_path)
        for attempt in range(max_retries):
            try:
                if not os.path.exists(image_path):
                    logger.error(f"Image file not found: {filename}")
                    return
                
                # Check file size and wait if it's too small
                file_size = os.path.getsize(image_path)
                if file_size < min_file_size:
                    logger.info(f"File {filename} is too small ({file_size} bytes). Waiting...")
                    await asyncio.sleep(retry_delay)
                    continue

                with open(image_path, 'rb') as image_file:
                    await self.bot.send_photo(
                        chat_id=self.chat_id, 
                        photo=image_file, 
                        caption=f"{caption}\nFilename: {filename}"
                    )
                logger.info(f"Image sent: {filename}")
                return
            except PermissionError:
                logger.warning(f"Permission denied for {filename}. Retrying...")
                await asyncio.sleep(retry_delay)
            except telegram.error.BadRequest as e:
                if "File must be non-empty" in str(e):
                    logger.warning(f"File {filename} is empty. Retrying...")
                    await asyncio.sleep(retry_delay)
                else:
                    logger.error(f"Bad request error for {filename}: {str(e)}")
                    break
            except Exception as e:
                logger.error(f"Error sending image {filename}: {str(e)}")
                break
        
        logger.error(f"Failed to send image after {max_retries} attempts: {filename}")

class OutputFolderHandler(FileSystemEventHandler):
    def __init__(self, queue):
        self.queue = queue

    def on_created(self, event):
        if not event.is_directory and event.src_path.lower().endswith(('.png', '.jpg', '.jpeg')):
            filename = os.path.basename(event.src_path)
            logger.info(f"Image detected: {filename}")
            self.queue.put(('image', event.src_path, "New image generated"))

    def on_modified(self, event):
        if event.is_directory:
            log_file = os.path.join(event.src_path, 'training.log')
            if os.path.exists(log_file):
                with open(log_file, 'r') as f:
                    lines = f.readlines()
                    if lines:
                        last_line = lines[-1].strip()
                        logger.info(f"Log update: {last_line}")
                        self.queue.put(('message', f"Training update: {last_line}"))

def load_config():
    if os.path.exists(CONFIG_FILE):
        with open(CONFIG_FILE, 'r') as config_file:
            return json.load(config_file)
    return {}

async def process_queue(queue, notifier):
    empty_queue_message_interval = 60
    last_empty_message_time = 0

    while True:
        try:
            item = queue.get(block=True, timeout=1)
            if item[0] == 'message':
                await notifier.send_message(item[1])
            elif item[0] == 'image':
                await notifier.send_image(item[1], item[2])
        except Empty:
            current_time = time.time()
            if current_time - last_empty_message_time > empty_queue_message_interval:
                logger.debug("Queue empty for the last minute.")
                last_empty_message_time = current_time
        except Exception as e:
            logger.error(f"Error processing queue item: {str(e)}")
        
        await asyncio.sleep(0.1)

async def main():
    config = load_config()
    token = config.get("telegram_bot_token")
    chat_id = config.get("telegram_chat_id")
    ai_toolkit_folder = config.get("ai_toolkit_folder")

    if not token or not chat_id or not ai_toolkit_folder:
        logger.error("Telegram bot token, chat ID, or AI Toolkit folder not set in config file.")
        return

    notifier = TelegramNotifier(token, chat_id)

    output_folder = os.path.join(ai_toolkit_folder, "output")
    if not os.path.exists(output_folder):
        logger.error(f"Output folder not found: {output_folder}")
        return

    queue = Queue()
    event_handler = OutputFolderHandler(queue)
    observer = Observer()
    observer.schedule(event_handler, output_folder, recursive=True)
    observer.start()

    logger.info(f"Monitoring started for folder: {output_folder}")
    await notifier.send_message("Telegram monitor started")

    try:
        await process_queue(queue, notifier)
    except KeyboardInterrupt:
        observer.stop()
    finally:
        observer.join()
        await notifier.send_message("Telegram monitor stopped")

if __name__ == "__main__":
    asyncio.run(main())