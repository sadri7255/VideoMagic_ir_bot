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
(
    CHOOSING,
    COMPRESS_VIDEO,
    CONVERT_TO_AUDIO,
    TRIM_VIDEO,
    TRIM_VIDEO_AUDIO,
    GET_START_TIME,
    GET_END_TIME,
    CONFIRM_CANCEL,
) = range(8)

# تابع شروع
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    keyboard = [
        [InlineKeyboardButton("کاهش حجم ویدیو 🎥", callback_data="compress_video")],
        [InlineKeyboardButton("تبدیل ویدیو به صوت 🎶", callback_data="convert_to_audio")],
        [InlineKeyboardButton("برش کلیپ ✂️", callback_data="trim_video")],
        [InlineKeyboardButton("برش کلیپ و صوت 🎬", callback_data="trim_video_audio")],
        [InlineKeyboardButton("لغو عملیات ❌", callback_data="cancel_operation")],
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    await update.message.reply_text("لطفا یک گزینه را انتخاب کنید:", reply_markup=reply_markup)
    return CHOOSING

# تابع لغو عملیات
async def cancel(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("عملیات لغو شد.")
    return ConversationHandler.END

# تابع ریست ربات
async def reset(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data.clear()
    await update.message.reply_text("ربات ریست شد. لطفا دوباره شروع کنید.")
    return await start(update, context)

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
    await update.callback_query.edit_message_text("لطفا زمان شروع برش را به ثانیه وارد کنید:")
    context.user_data["state"] = TRIM_VIDEO
    return GET_START_TIME

# تابع برش کلیپ و صوت
async def trim_video_audio(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.callback_query.answer()
    await update.callback_query.edit_message_text("لطفا زمان شروع برش را به ثانیه وارد کنید:")
    context.user_data["state"] = TRIM_VIDEO_AUDIO
    return GET_START_TIME

# تابع دریافت زمان شروع برش
async def get_start_time(update: Update, context: ContextTypes.DEFAULT_TYPE):
    try:
        start_time = float(update.message.text)
        context.user_data["start_time"] = start_time
        await update.message.reply_text("لطفا زمان پایان برش را به ثانیه وارد کنید:")
        return GET_END_TIME
    except ValueError:
        await update.message.reply_text("زمان وارد شده نامعتبر است. لطفا یک عدد وارد کنید.")
        return GET_START_TIME

# تابع دریافت زمان پایان برش
async def get_end_time(update: Update, context: ContextTypes.DEFAULT_TYPE):
    try:
        end_time = float(update.message.text)
        context.user_data["end_time"] = end_time
        await update.message.reply_text("لطفا ویدیوی خود را ارسال کنید.")
        return context.user_data["state"]
    except ValueError:
        await update.message.reply_text("زمان وارد شده نامعتبر است. لطفا یک عدد وارد کنید.")
        return GET_END_TIME

# تابع مدیریت ویدیو
async def handle_video(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_data = context.user_data

    # بررسی آیا فایل ویدیویی ارسال شده است
    if update.message.video:
        file = await update.message.video.get_file()
    elif update.message.document:
        file = await update.message.document.get_file()
    else:
        await update.message.reply_text("لطفا یک ویدیو یا فایل ویدیویی ارسال کنید.")
        return user_data["state"]

    # دانلود فایل ویدیویی
    file_path = f"temp_{update.message.from_user.id}.mp4"
    await file.download_to_drive(file_path)

    try:
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
            start_time = user_data.get("start_time", 0)
            end_time = user_data.get("end_time", clip.duration)
            trimmed_clip = clip.subclip(start_time, end_time)
            trimmed_clip.write_videofile(output_path)
            await update.message.reply_video(video=open(output_path, "rb"))
            os.remove(output_path)
        elif user_data["state"] == TRIM_VIDEO_AUDIO:
            output_path = f"trimmed_audio_{update.message.from_user.id}.mp3"
            clip = VideoFileClip(file_path)
            start_time = user_data.get("start_time", 0)
            end_time = user_data.get("end_time", clip.duration)
            trimmed_clip = clip.subclip(start_time, end_time)
            trimmed_clip.audio.write_audiofile(output_path)
            await update.message.reply_audio(audio=open(output_path, "rb"))
            os.remove(output_path)
    except Exception as e:
        logger.error(f"خطا در پردازش ویدیو: {e}")
        await update.message.reply_text("متاسفانه مشکلی در پردازش ویدیو رخ داده است. لطفا دوباره امتحان کنید.")
    finally:
        # حذف فایل موقت
        if os.path.exists(file_path):
            os.remove(file_path)

    return ConversationHandler.END

# تابع لغو عملیات با تأیید کاربر
async def cancel_operation(update: Update, context: ContextTypes.DEFAULT_TYPE):
    keyboard = [
        [InlineKeyboardButton("بله ✅", callback_data="confirm_cancel")],
        [InlineKeyboardButton("خیر ❌", callback_data="deny_cancel")],
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    await update.callback_query.answer()
    await update.callback_query.edit_message_text("آیا مطمئن هستید که می‌خواهید عملیات را لغو کنید؟", reply_markup=reply_markup)
    return CONFIRM_CANCEL

# تابع تأیید لغو عملیات
async def confirm_cancel(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.callback_query.answer()
    await update.callback_query.edit_message_text("عملیات لغو شد.")
    return ConversationHandler.END

# تابع رد لغو عملیات
async def deny_cancel(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.callback_query.answer()
    await update.callback_query.edit_message_text("عملیات ادامه می‌یابد.")
    return context.user_data.get("state", CHOOSING)

# تابع اصلی
def main():
    # استفاده از توکن ربات شما
    application = Application.builder().token("7516805845:AAFik2DscnDjxPKWwrHihN_LOFk2m3q4Sc0").build()

    conv_handler = ConversationHandler(
        entry_points=[CommandHandler("start", start), CommandHandler("reset", reset)],
        states={
            CHOOSING: [
                CallbackQueryHandler(compress_video, pattern="^compress_video$"),
                CallbackQueryHandler(convert_to_audio, pattern="^convert_to_audio$"),
                CallbackQueryHandler(trim_video, pattern="^trim_video$"),
                CallbackQueryHandler(trim_video_audio, pattern="^trim_video_audio$"),
                CallbackQueryHandler(cancel_operation, pattern="^cancel_operation$"),
            ],
            COMPRESS_VIDEO: [MessageHandler(filters.VIDEO | filters.Document.VIDEO, handle_video)],
            CONVERT_TO_AUDIO: [MessageHandler(filters.VIDEO | filters.Document.VIDEO, handle_video)],
            TRIM_VIDEO: [MessageHandler(filters.VIDEO | filters.Document.VIDEO, handle_video)],
            TRIM_VIDEO_AUDIO: [MessageHandler(filters.VIDEO | filters.Document.VIDEO, handle_video)],
            GET_START_TIME: [MessageHandler(filters.TEXT & ~filters.COMMAND, get_start_time)],
            GET_END_TIME: [MessageHandler(filters.TEXT & ~filters.COMMAND, get_end_time)],
            CONFIRM_CANCEL: [
                CallbackQueryHandler(confirm_cancel, pattern="^confirm_cancel$"),
                CallbackQueryHandler(deny_cancel, pattern="^deny_cancel$"),
            ],
        },
        fallbacks=[CommandHandler("cancel", cancel)],
    )

    application.add_handler(conv_handler)
    application.run_polling()

if __name__ == "__main__":
    main()
