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
    RECEIVE_VIDEO,
    COMPRESS_VIDEO,
    CONVERT_TO_AUDIO,
    TRIM_VIDEO,
    TRIM_VIDEO_AUDIO,
    GET_START_TIME,
    GET_END_TIME,
    CONFIRM_CANCEL,
) = range(9)

# تابع تبدیل زمان به ثانیه
def time_to_seconds(time_str):
    try:
        hh, mm, ss = map(int, time_str.split(":"))
        return hh * 3600 + mm * 60 + ss
    except ValueError:
        return None

# تابع شروع
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    keyboard = [
        [InlineKeyboardButton("دریافت فایل ویدیویی 🎥", callback_data="receive_video")],
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    await update.message.reply_text("لطفا فایل ویدیویی خود را ارسال کنید:", reply_markup=reply_markup)
    return CHOOSING

# تابع لغو عملیات
async def cancel(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("عملیات لغو شد.")
    return await start(update, context)

# تابع ریست ربات
async def reset(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data.clear()
    await update.message.reply_text("ربات ریست شد. لطفا دوباره شروع کنید.")
    return await start(update, context)

# تابع دریافت فایل ویدیویی
async def receive_video(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.callback_query.answer()
    await update.callback_query.edit_message_text("لطفا فایل ویدیویی خود را ارسال کنید.")
    context.user_data["state"] = RECEIVE_VIDEO
    return RECEIVE_VIDEO

# تابع مدیریت فایل دریافتی
async def handle_video(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_data = context.user_data

    if update.message.video:
        file = await update.message.video.get_file()
    elif update.message.document and update.message.document.mime_type.startswith('video'):
        file = await update.message.document.get_file()
    else:
        await update.message.reply_text("لطفا یک فایل ویدیویی ارسال کنید.")
        return await show_main_menu(update, context)

    file_path = f"temp_{update.message.from_user.id}.mp4"
    await file.download_to_drive(file_path)
    user_data["file_path"] = file_path
    return await show_main_menu(update, context)

# تابع نمایش منوی اصلی
async def show_main_menu(update: Update, context: ContextTypes.DEFAULT_TYPE):
    keyboard = [
        [InlineKeyboardButton("کاهش حجم ویدیو 🎥", callback_data="compress_video")],
        [InlineKeyboardButton("تبدیل ویدیو به صوت 🎶", callback_data="convert_to_audio")],
        [InlineKeyboardButton("برش کلیپ ✂️", callback_data="trim_video")],
        [InlineKeyboardButton("برش کلیپ و صوت 🎬", callback_data="trim_video_audio")],
        [InlineKeyboardButton("لغو عملیات ❌", callback_data="cancel_operation")],
        [InlineKeyboardButton("بازگشت به منوی اصلی 🔙", callback_data="back_to_main")],
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    await update.message.reply_text("فایل دریافت شد. لطفا یک عملیات را انتخاب کنید:", reply_markup=reply_markup)
    return CHOOSING

# تابع بازگشت به منوی اصلی
async def back_to_main(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.callback_query.answer()
    return await show_main_menu(update, context)

# تابع کاهش حجم ویدیو
async def compress_video(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.callback_query.answer()
    await update.callback_query.edit_message_text("در حال کاهش حجم ویدیو... لطفا منتظر بمانید.")
    context.user_data["state"] = COMPRESS_VIDEO
    return await process_file(update, context)

# تابع تبدیل ویدیو به صوت
async def convert_to_audio(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.callback_query.answer()
    await update.callback_query.edit_message_text("در حال تبدیل ویدیو به صوت... لطفا منتظر بمانید.")
    context.user_data["state"] = CONVERT_TO_AUDIO
    return await process_file(update, context)

# تابع برش کلیپ
async def trim_video(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.callback_query.answer()
    keyboard = [
        [InlineKeyboardButton("لغو ❌", callback_data="cancel_operation")],
        [InlineKeyboardButton("برگشت به منوی قبل 🔙", callback_data="back_to_main")],
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    await update.callback_query.edit_message_text(
        "لطفا زمان شروع برش را به فرمت `HH:MM:SS` وارد کنید.\nمثال: 01:06:05",
        reply_markup=reply_markup,
    )
    context.user_data["state"] = TRIM_VIDEO
    return GET_START_TIME

# تابع برش کلیپ و صوت
async def trim_video_audio(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.callback_query.answer()
    keyboard = [
        [InlineKeyboardButton("لغو ❌", callback_data="cancel_operation")],
        [InlineKeyboardButton("برگشت به منوی قبل 🔙", callback_data="back_to_main")],
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    await update.callback_query.edit_message_text(
        "لطفا زمان شروع برش را به فرمت `HH:MM:SS` وارد کنید.\nمثال: 01:06:05",
        reply_markup=reply_markup,
    )
    context.user_data["state"] = TRIM_VIDEO_AUDIO
    return GET_START_TIME

# تابع دریافت زمان شروع برش
async def get_start_time(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.callback_query:
        await update.callback_query.answer()
        if update.callback_query.data == "cancel_operation":
            return await cancel(update, context)
        elif update.callback_query.data == "back_to_main":
            return await back_to_main(update, context)
    else:
        time_str = update.message.text
        start_time = time_to_seconds(time_str)

        if start_time is None:
            keyboard = [
                [InlineKeyboardButton("لغو ❌", callback_data="cancel_operation")],
                [InlineKeyboardButton("برگشت به منوی قبل 🔙", callback_data="back_to_main")],
            ]
            reply_markup = InlineKeyboardMarkup(keyboard)
            await update.message.reply_text(
                "فرمت زمان نامعتبر است. لطفا زمان را به فرمت `HH:MM:SS` وارد کنید.\nمثال: 01:06:05",
                reply_markup=reply_markup,
            )
            return GET_START_TIME

        context.user_data["start_time"] = start_time
        keyboard = [
            [InlineKeyboardButton("لغو ❌", callback_data="cancel_operation")],
            [InlineKeyboardButton("برگشت به منوی قبل 🔙", callback_data="back_to_main")],
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)
        await update.message.reply_text(
            "لطفا زمان پایان برش را به فرمت `HH:MM:SS` وارد کنید.\nمثال: 01:06:05",
            reply_markup=reply_markup,
        )
        return GET_END_TIME

# تابع دریافت زمان پایان برش
async def get_end_time(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.callback_query:
        await update.callback_query.answer()
        if update.callback_query.data == "cancel_operation":
            return await cancel(update, context)
        elif update.callback_query.data == "back_to_main":
            return await back_to_main(update, context)
    else:
        time_str = update.message.text
        end_time = time_to_seconds(time_str)

        if end_time is None:
            keyboard = [
                [InlineKeyboardButton("لغو ❌", callback_data="cancel_operation")],
                [InlineKeyboardButton("برگشت به منوی قبل 🔙", callback_data="back_to_main")],
            ]
            reply_markup = InlineKeyboardMarkup(keyboard)
            await update.message.reply_text(
                "فرمت زمان نامعتبر است. لطفا زمان را به فرمت `HH:MM:SS` وارد کنید.\nمثال: 01:06:05",
                reply_markup=reply_markup,
            )
            return GET_END_TIME

        context.user_data["end_time"] = end_time
        return await process_file(update, context)

# تابع پردازش فایل
async def process_file(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_data = context.user_data
    file_path = user_data.get("file_path")

    if not file_path or not os.path.exists(file_path):
        await update.message.reply_text("فایل یافت نشد. لطفا دوباره امتحان کنید.")
        return await show_main_menu(update, context)

    try:
        if user_data["state"] == COMPRESS_VIDEO:
            output_path = f"compressed_{update.message.from_user.id}.mp4"
            clip = VideoFileClip(file_path)
            clip.write_videofile(output_path, bitrate="500k", threads=4)
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
            trimmed_clip.write_videofile(output_path, threads=4)
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

        keyboard = [[InlineKeyboardButton("شروع مجدد 🔄", callback_data="start")]]
        reply_markup = InlineKeyboardMarkup(keyboard)
        await update.message.reply_text("عملیات با موفقیت انجام شد. برای شروع مجدد کلیک کنید:", reply_markup=reply_markup)

    except Exception as e:
        logger.error(f"خطا در پردازش فایل: {e}")
        keyboard = [
            [InlineKeyboardButton("برگشت به منوی قبل 🔙", callback_data="back_to_main")],
            [InlineKeyboardButton("لغو ❌", callback_data="cancel_operation")],
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)
        await update.message.reply_text(
            "متاسفانه مشکلی در پردازش فایل رخ داده است. لطفا دوباره امتحان کنید.",
            reply_markup=reply_markup,
        )
    finally:
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
    return await start(update, context)

# تابع رد لغو عملیات
async def deny_cancel(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.callback_query.answer()
    await update.callback_query.edit_message_text("عملیات ادامه می‌یابد.")
    return context.user_data.get("state", CHOOSING)

# تابع اصلی
def main():
    token = os.getenv("7516805845:AAFik2DscnDjxPKWwrHihN_LOFk2m3q4Sc0")
    if not token:
        raise ValueError("لطفا توکن ربات را تنظیم کنید.")
    application = Application.builder().token(token).build()

    conv_handler = ConversationHandler(
        entry_points=[CommandHandler("start", start), CommandHandler("reset", reset)],
        states={
            CHOOSING: [
                CallbackQueryHandler(receive_video, pattern="^receive_video$"),
                CallbackQueryHandler(compress_video, pattern="^compress_video$"),
                CallbackQueryHandler(convert_to_audio, pattern="^convert_to_audio$"),
                CallbackQueryHandler(trim_video, pattern="^trim_video$"),
                CallbackQueryHandler(trim_video_audio, pattern="^trim_video_audio$"),
                CallbackQueryHandler(cancel_operation, pattern="^cancel_operation$"),
                CallbackQueryHandler(back_to_main, pattern="^back_to_main$"),
            ],
            RECEIVE_VIDEO: [MessageHandler(filters.VIDEO | filters.Document.VIDEO, handle_video)],
            COMPRESS_VIDEO: [CallbackQueryHandler(process_file)],
            CONVERT_TO_AUDIO: [CallbackQueryHandler(process_file)],
            TRIM_VIDEO: [CallbackQueryHandler(process_file)],
            TRIM_VIDEO_AUDIO: [CallbackQueryHandler(process_file)],
            GET_START_TIME: [
                MessageHandler(filters.TEXT & ~filters.COMMAND, get_start_time),
                CallbackQueryHandler(cancel_operation, pattern="^cancel_operation$"),
                CallbackQueryHandler(back_to_main, pattern="^back_to_main$"),
            ],
            GET_END_TIME: [
                MessageHandler(filters.TEXT & ~filters.COMMAND, get_end_time),
                CallbackQueryHandler(cancel_operation, pattern="^cancel_operation$"),
                CallbackQueryHandler(back_to_main, pattern="^back_to_main$"),
            ],
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
