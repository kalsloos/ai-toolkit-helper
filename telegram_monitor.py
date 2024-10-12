import os
import asyncio
import logging
import time
from queue import Queue, Empty
import telegram
from telegram.error import TelegramError
from watchdog.observers import Observer
from watchdog.events import FileSystemEventHandler

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(message)s', datefmt='%Y-%m-%d %H:%M:%S')
logger = logging.getLogger(__name__)

logging.getLogger('telegram').setLevel(logging.WARNING)
logging.getLogger('httpx').setLevel(logging.WARNING)

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

    async def send_image(self, image_path, caption=None):
        try:
            with open(image_path, 'rb') as image_file:
                await self.bot.send_photo(
                    chat_id=self.chat_id, 
                    photo=image_file, 
                    caption=caption
                )
            logger.info(f"Image sent: {image_path}")
        except Exception as e:
            logger.error(f"Error sending image {image_path}: {str(e)}")

class OutputFolderHandler(FileSystemEventHandler):
    def __init__(self, queue):
        self.queue = queue

    def on_created(self, event):
        if not event.is_directory and event.src_path.lower().endswith(('.png', '.jpg', '.jpeg')):
            self.queue.put(('image', event.src_path, "New image generated"))

    def on_modified(self, event):
        if event.is_directory:
            log_file = os.path.join(event.src_path, 'training.log')
            if os.path.exists(log_file):
                with open(log_file, 'r') as f:
                    lines = f.readlines()
                    if lines:
                        last_line = lines[-1].strip()
                        self.queue.put(('message', f"Training update: {last_line}"))

async def process_queue(queue, notifier):
    while True:
        try:
            item = queue.get(block=False)
            if item[0] == 'message':
                await notifier.send_message(item[1])
            elif item[0] == 'image':
                await notifier.send_image(item[1], item[2])
        except Empty:
            await asyncio.sleep(1)
        except Exception as e:
            logger.error(f"Error processing queue item: {str(e)}")

async def main():
    token = os.environ.get("TELEGRAM_BOT_TOKEN")
    chat_id = os.environ.get("TELEGRAM_CHAT_ID")
    ai_toolkit_folder = os.environ.get("AI_TOOLKIT_FOLDER")

    if not token or not chat_id or not ai_toolkit_folder:
        logger.error("Telegram bot token, chat ID, or AI Toolkit folder not set in environment variables.")
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