from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import (
    ApplicationBuilder,
    CommandHandler,
    MessageHandler,
    filters,
    CallbackQueryHandler,
    ConversationHandler,
    ContextTypes,
)
import os
from moviepy.video.io.VideoFileClip import VideoFileClip
from pydub import AudioSegment
from mutagen.easyid3 import EasyID3
from mutagen.id3 import ID3, APIC
import logging

# تنظیمات لاگ‌گیری
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(__name__)

# توکن ربات
TOKEN = '7516805845:AAFik2DscnDjxPKWwrHihN_LOFk2m3q4Sc0'

# حالت‌های گفتگو
VIDEO, AUDIO = range(2)

# تابع شروع
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    keyboard = [
        [InlineKeyboardButton("بخش ویدیویی", callback_data='video')],
        [InlineKeyboardButton("بخش صوتی", callback_data='audio')]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    await update.message.reply_text('لطفا یک بخش را انتخاب کنید:', reply_markup=reply_markup)

# تابع مدیریت انتخاب بخش
async def button(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    if query.data == 'video':
        await query.edit_message_text(text="شما بخش ویدیویی را انتخاب کرده‌اید. لطفا یک فایل ویدیویی ارسال کنید.")
        return VIDEO
    elif query.data == 'audio':
        await query.edit_message_text(text="شما بخش صوتی را انتخاب کرده‌اید. لطفا یک فایل صوتی ارسال کنید.")
        return AUDIO

# تابع پردازش فایل ویدیویی
async def process_video(update: Update, context: ContextTypes.DEFAULT_TYPE):
    try:
        file = await update.message.video.get_file()
        await file.download_to_drive('video.mp4')
        logger.info("فایل ویدیویی دریافت و ذخیره شد.")
        await update.message.reply_text("فایل ویدیویی دریافت شد. لطفا عملیات مورد نظر را انتخاب کنید.")
        
        # اضافه کردن منو برای انتخاب عملیات ویدیویی
        keyboard = [
            [InlineKeyboardButton("کم کردن حجم فایل ویدیویی", callback_data='compress_video')],
            [InlineKeyboardButton("برش فایل ویدیویی", callback_data='cut_video')],
            [InlineKeyboardButton("تبدیل فایل ویدیویی به صوت", callback_data='convert_video_to_audio')],
            [InlineKeyboardButton("بازگشت به منوی اصلی", callback_data='back_to_main')]
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)
        await update.message.reply_text('لطفا عملیات مورد نظر را انتخاب کنید:', reply_markup=reply_markup)
        return VIDEO
    except Exception as e:
        logger.error(f"خطا در پردازش فایل ویدیویی: {e}")
        await update.message.reply_text("خطایی در پردازش فایل ویدیویی رخ داد. لطفا دوباره امتحان کنید.")
        return ConversationHandler.END

# تابع پردازش فایل صوتی
async def process_audio(update: Update, context: ContextTypes.DEFAULT_TYPE):
    try:
        file = await update.message.audio.get_file()
        await file.download_to_drive('audio.mp3')
        logger.info("فایل صوتی دریافت و ذخیره شد.")
        await update.message.reply_text("فایل صوتی دریافت شد. لطفا عملیات مورد نظر را انتخاب کنید.")
        
        # اضافه کردن منو برای انتخاب عملیات صوتی
        keyboard = [
            [InlineKeyboardButton("تغییر اطلاعات آلبوم و خواننده", callback_data='edit_metadata')],
            [InlineKeyboardButton("برش موسیقی", callback_data='cut_audio')],
            [InlineKeyboardButton("تغییر عکس آلبوم", callback_data='change_album_art')],
            [InlineKeyboardButton("کم کردن حجم صوت", callback_data='compress_audio')],
            [InlineKeyboardButton("بازگشت به منوی اصلی", callback_data='back_to_main')]
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)
        await update.message.reply_text('لطفا عملیات مورد نظر را انتخاب کنید:', reply_markup=reply_markup)
        return AUDIO
    except Exception as e:
        logger.error(f"خطا در پردازش فایل صوتی: {e}")
        await update.message.reply_text("خطایی در پردازش فایل صوتی رخ داد. لطفا دوباره امتحان کنید.")
        return ConversationHandler.END

# تابع بازگشت به منوی اصلی
async def back_to_main_menu(update: Update, context: ContextTypes.DEFAULT_TYPE):
    keyboard = [
        [InlineKeyboardButton("بخش ویدیویی", callback_data='video')],
        [InlineKeyboardButton("بخش صوتی", callback_data='audio')]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    await update.message.reply_text('لطفا یک بخش را انتخاب کنید:', reply_markup=reply_markup)
    return ConversationHandler.END

# تابع ریست کردن ربات
async def reset(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("ربات ریست شد. لطفا دوباره شروع کنید.")
    return await start(update, context)

# تابع اصلی
def main():
    application = ApplicationBuilder().token(TOKEN).build()

    # تعریف ConversationHandler برای مدیریت حالت‌های مختلف
    conv_handler = ConversationHandler(
        entry_points=[CommandHandler('start', start)],
        states={
            VIDEO: [
                MessageHandler(filters.VIDEO, process_video),
                CallbackQueryHandler(compress_video, pattern='compress_video'),
                CallbackQueryHandler(cut_video, pattern='cut_video'),
                CallbackQueryHandler(convert_video_to_audio, pattern='convert_video_to_audio'),
                CallbackQueryHandler(back_to_main_menu, pattern='back_to_main')
            ],
            AUDIO: [
                MessageHandler(filters.AUDIO, process_audio),
                CallbackQueryHandler(edit_metadata, pattern='edit_metadata'),
                CallbackQueryHandler(cut_audio, pattern='cut_audio'),
                CallbackQueryHandler(change_album_art, pattern='change_album_art'),
                CallbackQueryHandler(compress_audio, pattern='compress_audio'),
                CallbackQueryHandler(back_to_main_menu, pattern='back_to_main')
            ]
        },
        fallbacks=[CommandHandler('reset', reset)]
    )

    application.add_handler(conv_handler)
    application.add_handler(CallbackQueryHandler(button))
    application.add_handler(CommandHandler('reset', reset))

    application.run_polling()

if __name__ == '__main__':
    main()
