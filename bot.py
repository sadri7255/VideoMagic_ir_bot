import os
import logging
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import (
    Application,
    CommandHandler,
    MessageHandler,
    filters,
    CallbackQueryHandler,
    ConversationHandler,
    ContextTypes,
)
from moviepy.editor import VideoFileClip, AudioFileClip

# تنظیمات لاگ
logging.basicConfig(format="%(asctime)s - %(name)s - %(levelname)s - %(message)s", level=logging.INFO)
logger = logging.getLogger(__name__)

# حالت‌های گفتگو
CHOOSING, COMPRESS_VIDEO, CONVERT_TO_AUDIO, TRIM_VIDEO, TRIM_VIDEO_AUDIO = range(5)

# تابع شروع
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    keyboard = [
        [InlineKeyboardButton("کاهش حجم ویدیو 🎥", callback_data="compress_video")],
        [InlineKeyboardButton("تبدیل ویدیو به صوت 🎶", callback_data="convert_to_audio")],
        [InlineKeyboardButton("برش کلیپ ✂️", callback_data="trim_video")],
        [InlineKeyboardButton("برش کلیپ و صوت 🎬", callback_data="trim_video_audio")],
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    await update.message.reply_text("لطفا یک گزینه را انتخاب کنید:", reply_markup=reply_markup)
    return CHOOSING

# تابع لغو عملیات
async def cancel(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("عملیات لغو شد.")
    return ConversationHandler.END

# تابع کاهش حجم ویدیو
async def compress_video(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.callback_query.answer()
    await update.callback_query.edit_message_text("لطفا ویدیوی خود را ارسال کنید.")
    context.user_data["state"] = COMPRESS_VIDEO
    return COMPRESS_VIDEO

# تابع تبدیل ویدیو به صوت
async def convert_to_audio(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.callback_query.answer()
    await update.callback_query.edit_message_text("لطفا ویدیوی خود را ارسال کنید.")
    context.user_data["state"] = CONVERT_TO_AUDIO
    return CONVERT_TO_AUDIO

# تابع برش کلیپ
async def trim_video(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.callback_query.answer()
    await update.callback_query.edit_message_text("لطفا ویدیوی خود را ارسال کنید.")
    context.user_data["state"] = TRIM_VIDEO
    return TRIM_VIDEO

# تابع برش کلیپ و صوت
async def trim_video_audio(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.callback_query.answer()
    await update.callback_query.edit_message_text("لطفا ویدیوی خود را ارسال کنید.")
    context.user_data["state"] = TRIM_VIDEO_AUDIO
    return TRIM_VIDEO_AUDIO

# تابع مدیریت ویدیو
async def handle_video(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_data = context.user_data

    # بررسی آیا ویدیو به صورت فایل مستقیم ارسال شده است
    if update.message.video:
        file = await update.message.video.get_file()
    elif update.message.document:
        file = await update.message.document.get_file()
    else:
        await update.message.reply_text("لطفا یک ویدیو یا فایل ویدیویی ارسال کنید.")
        return user_data["state"]

    # دانلود ویدیو
    file_path = f"temp_{update.message.from_user.id}.mp4"
    await file.download_to_drive(file_path)

    # پردازش ویدیو بر اساس حالت انتخاب شده
    if user_data["state"] == COMPRESS_VIDEO:
        output_path = f"compressed_{update.message.from_user.id}.mp4"
        clip = VideoFileClip(file_path)
        clip.write_videofile(output_path, bitrate="500k")
        await update.message.reply_video(video=open(output_path, "rb"))
        os.remove(output_path)
    elif user_data["state"] == CONVERT_TO_AUDIO:
        output_path = f"converted_{update.message.from_user.id}.mp3"
        clip = VideoFileClip(file_path)
        clip.audio.write_audiofile(output_path)
        await update.message.reply_audio(audio=open(output_path, "rb"))
        os.remove(output_path)
    elif user_data["state"] == TRIM_VIDEO:
        output_path = f"trimmed_{update.message.from_user.id}.mp4"
        clip = VideoFileClip(file_path)
        start_time = 10  # زمان شروع (ثانیه)
        end_time = 20  # زمان پایان (ثانیه)
        trimmed_clip = clip.subclip(start_time, end_time)
        trimmed_clip.write_videofile(output_path)
        await update.message.reply_video(video=open(output_path, "rb"))
        os.remove(output_path)
    elif user_data["state"] == TRIM_VIDEO_AUDIO:
        output_path = f"trimmed_audio_{update.message.from_user.id}.mp3"
        clip = VideoFileClip(file_path)
        start_time = 10  # زمان شروع (ثانیه)
        end_time = 20  # زمان پایان (ثانیه)
        trimmed_clip = clip.subclip(start_time, end_time)
        trimmed_clip.audio.write_audiofile(output_path)
        await update.message.reply_audio(audio=open(output_path, "rb"))
        os.remove(output_path)

    # حذف فایل موقت
    os.remove(file_path)
    return ConversationHandler.END

# تابع اصلی
def main():
    # استفاده از توکن ربات شما
    application = Application.builder().token("7516805845:AAFik2DscnDjxPKWwrHihN_LOFk2m3q4Sc0").build()

    conv_handler = ConversationHandler(
        entry_points=[CommandHandler("start", start)],
        states={
            CHOOSING: [
                CallbackQueryHandler(compress_video, pattern="^compress_video$"),
                CallbackQueryHandler(convert_to_audio, pattern="^convert_to_audio$"),
                CallbackQueryHandler(trim_video, pattern="^trim_video$"),
                CallbackQueryHandler(trim_video_audio, pattern="^trim_video_audio$"),
            ],
            COMPRESS_VIDEO: [MessageHandler(filters.VIDEO | filters.Document.VIDEO, handle_video)],
            CONVERT_TO_AUDIO: [MessageHandler(filters.VIDEO | filters.Document.VIDEO, handle_video)],
            TRIM_VIDEO: [MessageHandler(filters.VIDEO | filters.Document.VIDEO, handle_video)],
            TRIM_VIDEO_AUDIO: [MessageHandler(filters.VIDEO | filters.Document.VIDEO, handle_video)],
        },
        fallbacks=[CommandHandler("cancel", cancel)],
    )

    application.add_handler(conv_handler)
    application.run_polling()

if __name__ == "__main__":
    main()
