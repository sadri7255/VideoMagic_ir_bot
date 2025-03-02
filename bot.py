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
VIDEO, AUDIO, GET_START_TIME, GET_END_TIME = range(4)

# تابع تبدیل زمان به میلی‌ثانیه
def time_to_milliseconds(time_str):
    try:
        hh, mm, ss = map(int, time_str.split(':'))
        return (hh * 3600 + mm * 60 + ss) * 1000
    except Exception as e:
        logger.error(f"خطا در تبدیل زمان به میلی‌ثانیه: {e}")
        return None

# تابع شروع
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    keyboard = [
        [InlineKeyboardButton("بخش ویدیویی", callback_data='video')],
        [InlineKeyboardButton("بخش صوتی", callback_data='audio')]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    await update.message.reply_text('لطفا یک بخش را انتخاب کنید:', reply_markup=reply_markup)
    return VIDEO if context.user_data.get('selected_section') == 'video' else AUDIO

# تابع مدیریت انتخاب بخش
async def button(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    if query.data == 'video':
        await query.edit_message_text(text="شما بخش ویدیویی را انتخاب کرده‌اید. لطفا یک فایل ویدیویی ارسال کنید.")
        context.user_data['selected_section'] = 'video'
        return VIDEO
    elif query.data == 'audio':
        await query.edit_message_text(text="شما بخش صوتی را انتخاب کرده‌اید. لطفا یک فایل صوتی ارسال کنید.")
        context.user_data['selected_section'] = 'audio'
        return AUDIO
    elif query.data == 'back_to_main':
        return await start(update, context)
    elif query.data == 'send_final_file':
        return await send_final_file(update, context)

# تابع پردازش فایل ویدیویی
async def process_video(update: Update, context: ContextTypes.DEFAULT_TYPE):
    try:
        logger.info("پیام دریافتی: %s", update.message)
        if update.message.video:
            logger.info("فایل ویدیویی دریافت شد.")
            file = await update.message.video.get_file()
        elif update.message.document and update.message.document.mime_type.startswith('video/'):
            logger.info("فایل ویدیویی به عنوان document دریافت شد.")
            file = await update.message.document.get_file()
        else:
            await update.message.reply_text("لطفا یک فایل ویدیویی ارسال کنید.")
            return VIDEO

        logger.info(f"فایل دانلود می‌شود: {file.file_path}")
        await file.download_to_drive('video.mp4')
        logger.info("فایل ویدیویی ذخیره شد.")
        await update.message.reply_text("فایل ویدیویی دریافت شد. لطفا عملیات مورد نظر را انتخاب کنید.")
        
        # اضافه کردن منو برای انتخاب عملیات ویدیویی
        keyboard = [
            [InlineKeyboardButton("کم کردن حجم فایل ویدیویی", callback_data='compress_video')],
            [InlineKeyboardButton("برش فایل ویدیویی", callback_data='cut_video')],
            [InlineKeyboardButton("تبدیل فایل ویدیویی به صوت", callback_data='convert_video_to_audio')],
            [InlineKeyboardButton("ارسال فایل", callback_data='send_file')],
            [InlineKeyboardButton("بازگشت به منوی اصلی", callback_data='back_to_main')]
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)
        await update.message.reply_text('لطفا عملیات مورد نظر را انتخاب کنید:', reply_markup=reply_markup)
        return VIDEO
    except Exception as e:
        logger.error(f"خطا در پردازش فایل ویدیویی: {e}")
        await update.message.reply_text("خطایی در پردازش فایل ویدیویی رخ داد. لطفا دوباره امتحان کنید.")
        return ConversationHandler.END

# تابع کم کردن حجم فایل ویدیویی
async def compress_video(update: Update, context: ContextTypes.DEFAULT_TYPE):
    try:
        # بررسی وجود update.message
        if update.message:
            message = update.message
        elif update.callback_query and update.callback_query.message:
            message = update.callback_query.message
        else:
            logger.error("خطا: پیامی برای پاسخ‌گویی یافت نشد.")
            return ConversationHandler.END

        video = VideoFileClip("video.mp4")
        video.write_videofile("compressed_video.mp4", bitrate="500k")
        os.replace("compressed_video.mp4", "video.mp4")  # جایگزینی فایل موقت
        await message.reply_text("حجم فایل ویدیویی کاهش یافت.")
        return VIDEO
    except Exception as e:
        logger.error(f"خطا در کم کردن حجم فایل ویدیویی: {e}")
        if update.message:
            await update.message.reply_text("خطایی در کم کردن حجم فایل ویدیویی رخ داد. لطفا دوباره امتحان کنید.")
        elif update.callback_query and update.callback_query.message:
            await update.callback_query.message.reply_text("خطایی در کم کردن حجم فایل ویدیویی رخ داد. لطفا دوباره امتحان کنید.")
        return ConversationHandler.END

# تابع برش فایل ویدیویی
async def cut_video(update: Update, context: ContextTypes.DEFAULT_TYPE):
    try:
        # بررسی وجود update.message
        if update.message:
            message = update.message
        elif update.callback_query and update.callback_query.message:
            message = update.callback_query.message
        else:
            logger.error("خطا: پیامی برای پاسخ‌گویی یافت نشد.")
            return ConversationHandler.END

        start_time = "00:00:10"  # زمان شروع برش
        end_time = "00:00:20"    # زمان پایان برش
        video = VideoFileClip("video.mp4").subclip(start_time, end_time)
        video.write_videofile("cut_video.mp4")
        os.replace("cut_video.mp4", "video.mp4")  # جایگزینی فایل موقت
        await message.reply_text("فایل ویدیویی برش داده شد.")
        return VIDEO
    except Exception as e:
        logger.error(f"خطا در برش فایل ویدیویی: {e}")
        if update.message:
            await update.message.reply_text("خطایی در برش فایل ویدیویی رخ داد. لطفا دوباره امتحان کنید.")
        elif update.callback_query and update.callback_query.message:
            await update.callback_query.message.reply_text("خطایی در برش فایل ویدیویی رخ داد. لطفا دوباره امتحان کنید.")
        return ConversationHandler.END

# تابع تبدیل فایل ویدیویی به صوت
async def convert_video_to_audio(update: Update, context: ContextTypes.DEFAULT_TYPE):
    try:
        # بررسی وجود update.message
        if update.message:
            message = update.message
        elif update.callback_query and update.callback_query.message:
            message = update.callback_query.message
        else:
            logger.error("خطا: پیامی برای پاسخ‌گویی یافت نشد.")
            return ConversationHandler.END

        video = VideoFileClip("video.mp4")
        video.audio.write_audiofile("converted_audio.mp3")
        os.replace("converted_audio.mp3", "audio.mp3")  # جایگزینی فایل موقت
        await message.reply_text("فایل ویدیویی به صوت تبدیل شد.")
        return AUDIO
    except Exception as e:
        logger.error(f"خطا در تبدیل فایل ویدیویی به صوت: {e}")
        if update.message:
            await update.message.reply_text("خطایی در تبدیل فایل ویدیویی به صوت رخ داد. لطفا دوباره امتحان کنید.")
        elif update.callback_query and update.callback_query.message:
            await update.callback_query.message.reply_text("خطایی در تبدیل فایل ویدیویی به صوت رخ داد. لطفا دوباره امتحان کنید.")
        return ConversationHandler.END

# تابع پردازش فایل صوتی
async def process_audio(update: Update, context: ContextTypes.DEFAULT_TYPE):
    try:
        logger.info("پیام دریافتی: %s", update.message)
        if update.message.audio:
            logger.info("فایل صوتی دریافت شد.")
            file = await update.message.audio.get_file()
        elif update.message.document and update.message.document.mime_type.startswith('audio/'):
            logger.info("فایل صوتی به عنوان document دریافت شد.")
            file = await update.message.document.get_file()
        else:
            await update.message.reply_text("لطفا یک فایل صوتی ارسال کنید.")
            return AUDIO

        logger.info(f"فایل دانلود می‌شود: {file.file_path}")
        await file.download_to_drive('audio.mp3')
        logger.info("فایل صوتی ذخیره شد.")
        await update.message.reply_text("فایل صوتی دریافت شد. لطفا عملیات مورد نظر را انتخاب کنید.")
        
        # اضافه کردن منو برای انتخاب عملیات صوتی
        keyboard = [
            [InlineKeyboardButton("تغییر اطلاعات آلبوم و خواننده", callback_data='edit_metadata')],
            [InlineKeyboardButton("برش موسیقی", callback_data='cut_audio')],
            [InlineKeyboardButton("تغییر عکس آلبوم", callback_data='change_album_art')],
            [InlineKeyboardButton("کم کردن حجم صوت", callback_data='compress_audio')],
            [InlineKeyboardButton("ارسال فایل", callback_data='send_file')],
            [InlineKeyboardButton("بازگشت به منوی اصلی", callback_data='back_to_main')]
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)
        await update.message.reply_text('لطفا عملیات مورد نظر را انتخاب کنید:', reply_markup=reply_markup)
        return AUDIO
    except Exception as e:
        logger.error(f"خطا در پردازش فایل صوتی: {e}")
        await update.message.reply_text("خطایی در پردازش فایل صوتی رخ داد. لطفا دوباره امتحان کنید.")
        return ConversationHandler.END

# تابع دریافت زمان شروع برش
async def get_start_time(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("لطفا زمان شروع برش را به فرمت HH:MM:SS وارد کنید:")
    return GET_START_TIME

# تابع دریافت زمان پایان برش
async def get_end_time(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data['start_time'] = update.message.text
    await update.message.reply_text("لطفا زمان پایان برش را به فرمت HH:MM:SS وارد کنید:")
    return GET_END_TIME

# تابع برش موسیقی
async def cut_audio(update: Update, context: ContextTypes.DEFAULT_TYPE):
    try:
        # بررسی وجود update.message
        if update.message:
            message = update.message
        elif update.callback_query and update.callback_query.message:
            message = update.callback_query.message
        else:
            logger.error("خطا: پیامی برای پاسخ‌گویی یافت نشد.")
            return ConversationHandler.END

        end_time = update.message.text
        start_time = context.user_data.get('start_time')

        # تبدیل زمان به میلی‌ثانیه
        start_ms = time_to_milliseconds(start_time)
        end_ms = time_to_milliseconds(end_time)

        if start_ms is None or end_ms is None:
            await message.reply_text("فرمت زمان وارد شده نامعتبر است. لطفا دوباره امتحان کنید.")
            return AUDIO

        audio = AudioSegment.from_mp3("audio.mp3")
        cut_audio = audio[start_ms:end_ms]
        cut_audio.export("cut_audio.mp3", format="mp3")
        os.replace("cut_audio.mp3", "audio.mp3")  # جایگزینی فایل موقت
        await message.reply_text("فایل صوتی برش داده شد.")
        return AUDIO
    except Exception as e:
        logger.error(f"خطا در برش موسیقی: {e}")
        if update.message:
            await update.message.reply_text("خطایی در برش موسیقی رخ داد. لطفا دوباره امتحان کنید.")
        elif update.callback_query and update.callback_query.message:
            await update.callback_query.message.reply_text("خطایی در برش موسیقی رخ داد. لطفا دوباره امتحان کنید.")
        return ConversationHandler.END

# تابع تغییر اطلاعات آلبوم و خواننده موسیقی
async def edit_metadata(update: Update, context: ContextTypes.DEFAULT_TYPE):
    try:
        # بررسی وجود update.message
        if update.message:
            message = update.message
        elif update.callback_query and update.callback_query.message:
            message = update.callback_query.message
        else:
            logger.error("خطا: پیامی برای پاسخ‌گویی یافت نشد.")
            return ConversationHandler.END

        audio = EasyID3("audio.mp3")
        audio['artist'] = 'خواننده جدید'
        audio['album'] = 'آلبوم جدید'
        audio.save()
        await message.reply_text("اطلاعات آلبوم و خواننده تغییر یافت.")
        return AUDIO
    except Exception as e:
        logger.error(f"خطا در تغییر اطلاعات آلبوم و خواننده: {e}")
        if update.message:
            await update.message.reply_text("خطایی در تغییر اطلاعات آلبوم و خواننده رخ داد. لطفا دوباره امتحان کنید.")
        elif update.callback_query and update.callback_query.message:
            await update.callback_query.message.reply_text("خطایی در تغییر اطلاعات آلبوم و خواننده رخ داد. لطفا دوباره امتحان کنید.")
        return ConversationHandler.END

# تابع تغییر عکس آلبوم
async def change_album_art(update: Update, context: ContextTypes.DEFAULT_TYPE):
    try:
        # بررسی وجود update.message
        if update.message:
            message = update.message
        elif update.callback_query and update.callback_query.message:
            message = update.callback_query.message
        else:
            logger.error("خطا: پیامی برای پاسخ‌گویی یافت نشد.")
            return ConversationHandler.END

        audio = ID3("audio.mp3")
        with open("new_album_art.jpg", 'rb') as album_art:
            audio['APIC'] = APIC(
                encoding=3,
                mime='image/jpeg',
                type=3,
                desc=u'Cover',
                data=album_art.read()
            )
        audio.save()
        await message.reply_text("عکس آلبوم تغییر یافت.")
        return AUDIO
    except Exception as e:
        logger.error(f"خطا در تغییر عکس آلبوم: {e}")
        if update.message:
            await update.message.reply_text("خطایی در تغییر عکس آلبوم رخ داد. لطفا دوباره امتحان کنید.")
        elif update.callback_query and update.callback_query.message:
            await update.callback_query.message.reply_text("خطایی در تغییر عکس آلبوم رخ داد. لطفا دوباره امتحان کنید.")
        return ConversationHandler.END

# تابع کم کردن حجم صوت
async def compress_audio(update: Update, context: ContextTypes.DEFAULT_TYPE):
    try:
        # بررسی وجود update.message
        if update.message:
            message = update.message
        elif update.callback_query and update.callback_query.message:
            message = update.callback_query.message
        else:
            logger.error("خطا: پیامی برای پاسخ‌گویی یافت نشد.")
            return ConversationHandler.END

        audio = AudioSegment.from_mp3("audio.mp3")
        audio = audio.set_channels(1)  # تبدیل به mono
        audio = audio.set_frame_rate(16000)  # تنظیم bit rate
        audio.export("compressed_audio.mp3", format="mp3", bitrate="16k")
        os.replace("compressed_audio.mp3", "audio.mp3")  # جایگزینی فایل موقت
        await message.reply_text("حجم فایل صوتی کاهش یافت.")
        return AUDIO
    except Exception as e:
        logger.error(f"خطا در کم کردن حجم صوت: {e}")
        if update.message:
            await update.message.reply_text("خطایی در کم کردن حجم صوت رخ داد. لطفا دوباره امتحان کنید.")
        elif update.callback_query and update.callback_query.message:
            await update.callback_query.message.reply_text("خطایی در کم کردن حجم صوت رخ داد. لطفا دوباره امتحان کنید.")
        return ConversationHandler.END

# تابع ارسال فایل نهایی
async def send_final_file(update: Update, context: ContextTypes.DEFAULT_TYPE):
    try:
        # بررسی وجود update.message
        if update.message:
            message = update.message
        elif update.callback_query and update.callback_query.message:
            message = update.callback_query.message
        else:
            logger.error("خطا: پیامی برای پاسخ‌گویی یافت نشد.")
            return ConversationHandler.END

        if context.user_data.get('selected_section') == 'video':
            await message.reply_video(video=open("video.mp4", 'rb'))
            os.remove("video.mp4")
        elif context.user_data.get('selected_section') == 'audio':
            await message.reply_audio(audio=open("audio.mp3", 'rb'))
            os.remove("audio.mp3")
        
        return await back_to_main_menu(update, context)
    except Exception as e:
        logger.error(f"خطا در ارسال فایل نهایی: {e}")
        if update.message:
            await update.message.reply_text("خطایی در ارسال فایل نهایی رخ داد. لطفا دوباره امتحان کنید.")
        elif update.callback_query and update.callback_query.message:
            await update.callback_query.message.reply_text("خطایی در ارسال فایل نهایی رخ داد. لطفا دوباره امتحان کنید.")
        return ConversationHandler.END

# تابع ارسال فایل در هر مرحله
async def send_file(update: Update, context: ContextTypes.DEFAULT_TYPE):
    try:
        # بررسی وجود update.message
        if update.message:
            message = update.message
        elif update.callback_query and update.callback_query.message:
            message = update.callback_query.message
        else:
            logger.error("خطا: پیامی برای پاسخ‌گویی یافت نشد.")
            return ConversationHandler.END

        if context.user_data.get('selected_section') == 'video':
            await message.reply_video(video=open("video.mp4", 'rb'))
        elif context.user_data.get('selected_section') == 'audio':
            await message.reply_audio(audio=open("audio.mp3", 'rb'))
        
        return await back_to_main_menu(update, context)
    except Exception as e:
        logger.error(f"خطا در ارسال فایل: {e}")
        if update.message:
            await update.message.reply_text("خطایی در ارسال فایل رخ داد. لطفا دوباره امتحان کنید.")
        elif update.callback_query and update.callback_query.message:
            await update.callback_query.message.reply_text("خطایی در ارسال فایل رخ داد. لطفا دوباره امتحان کنید.")
        return ConversationHandler.END

# تابع بازگشت به منوی اصلی
async def back_to_main_menu(update: Update, context: ContextTypes.DEFAULT_TYPE):
    keyboard = [
        [InlineKeyboardButton("بخش ویدیویی", callback_data='video')],
        [InlineKeyboardButton("بخش صوتی", callback_data='audio')],
        [InlineKeyboardButton("ارسال فایل نهایی", callback_data='send_final_file')]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    if update.message:
        await update.message.reply_text('لطفا یک بخش را انتخاب کنید:', reply_markup=reply_markup)
    elif update.callback_query and update.callback_query.message:
        await update.callback_query.message.reply_text('لطفا یک بخش را انتخاب کنید:', reply_markup=reply_markup)
    return ConversationHandler.END

# تابع ریست کردن ربات
async def reset(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.message:
        await update.message.reply_text("ربات ریست شد. لطفا دوباره شروع کنید.")
    elif update.callback_query and update.callback_query.message:
        await update.callback_query.message.reply_text("ربات ریست شد. لطفا دوباره شروع کنید.")
    return await start(update, context)

# تابع اصلی
def main():
    application = ApplicationBuilder().token(TOKEN).build()

    # تعریف ConversationHandler برای مدیریت حالت‌های مختلف
    conv_handler = ConversationHandler(
        entry_points=[CommandHandler('start', start)],
        states={
            VIDEO: [
                MessageHandler(filters.VIDEO | filters.Document.VIDEO, process_video),
                CallbackQueryHandler(compress_video, pattern='compress_video'),
                CallbackQueryHandler(cut_video, pattern='cut_video'),
                CallbackQueryHandler(convert_video_to_audio, pattern='convert_video_to_audio'),
                CallbackQueryHandler(send_file, pattern='send_file'),
                CallbackQueryHandler(back_to_main_menu, pattern='back_to_main')
            ],
            AUDIO: [
                MessageHandler(filters.AUDIO | filters.Document.AUDIO, process_audio),
                CallbackQueryHandler(edit_metadata, pattern='edit_metadata'),
                CallbackQueryHandler(get_start_time, pattern='cut_audio'),
                CallbackQueryHandler(change_album_art, pattern='change_album_art'),
                CallbackQueryHandler(compress_audio, pattern='compress_audio'),
                CallbackQueryHandler(send_file, pattern='send_file'),
                CallbackQueryHandler(back_to_main_menu, pattern='back_to_main')
            ],
            GET_START_TIME: [
                MessageHandler(filters.TEXT & ~filters.COMMAND, get_end_time)
            ],
            GET_END_TIME: [
                MessageHandler(filters.TEXT & ~filters.COMMAND, cut_audio)
            ]
        },
        fallbacks=[CommandHandler('reset', reset)]
    )

    application.add_handler(conv_handler)
    application.add_handler(CallbackQueryHandler(button))  # این خط اضافه شده است
    application.add_handler(CommandHandler('reset', reset))

    application.run_polling()

if __name__ == '__main__':
    main()
