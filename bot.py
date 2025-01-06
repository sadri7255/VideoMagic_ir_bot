from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Updater, CommandHandler, MessageHandler, Filters, CallbackQueryHandler, ConversationHandler
import os
from moviepy.video.io.VideoFileClip import VideoFileClip
from pydub import AudioSegment
from mutagen.easyid3 import EasyID3
from mutagen.id3 import ID3, APIC

# توکن ربات
TOKEN = '7516805845:AAFik2DscnDjxPKWwrHihN_LOFk2m3q4Sc0'

# حالت‌های گفتگو
VIDEO, AUDIO = range(2)

# تابع شروع
def start(update, context):
    keyboard = [
        [InlineKeyboardButton("بخش ویدیویی", callback_data='video')],
        [InlineKeyboardButton("بخش صوتی", callback_data='audio')]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    update.message.reply_text('لطفا یک بخش را انتخاب کنید:', reply_markup=reply_markup)

# تابع مدیریت انتخاب بخش
def button(update, context):
    query = update.callback_query
    query.answer()
    if query.data == 'video':
        query.edit_message_text(text="شما بخش ویدیویی را انتخاب کرده‌اید. لطفا یک فایل ویدیویی ارسال کنید.")
        return VIDEO
    elif query.data == 'audio':
        query.edit_message_text(text="شما بخش صوتی را انتخاب کرده‌اید. لطفا یک فایل صوتی ارسال کنید.")
        return AUDIO

# تابع پردازش فایل ویدیویی
def process_video(update, context):
    file = update.message.video.get_file()
    file.download('video.mp4')
    update.message.reply_text("فایل ویدیویی دریافت شد. لطفا عملیات مورد نظر را انتخاب کنید.")
    # اضافه کردن منو برای انتخاب عملیات ویدیویی
    keyboard = [
        [InlineKeyboardButton("کم کردن حجم فایل ویدیویی", callback_data='compress_video')],
        [InlineKeyboardButton("برش فایل ویدیویی", callback_data='cut_video')],
        [InlineKeyboardButton("تبدیل فایل ویدیویی به صوت", callback_data='convert_video_to_audio')],
        [InlineKeyboardButton("بازگشت به منوی اصلی", callback_data='back_to_main')]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    update.message.reply_text('لطفا عملیات مورد نظر را انتخاب کنید:', reply_markup=reply_markup)
    return VIDEO

# تابع پردازش فایل صوتی
def process_audio(update, context):
    file = update.message.audio.get_file()
    file.download('audio.mp3')
    update.message.reply_text("فایل صوتی دریافت شد. لطفا عملیات مورد نظر را انتخاب کنید.")
    # اضافه کردن منو برای انتخاب عملیات صوتی
    keyboard = [
        [InlineKeyboardButton("تغییر اطلاعات آلبوم و خواننده", callback_data='edit_metadata')],
        [InlineKeyboardButton("برش موسیقی", callback_data='cut_audio')],
        [InlineKeyboardButton("تغییر عکس آلبوم", callback_data='change_album_art')],
        [InlineKeyboardButton("کم کردن حجم صوت", callback_data='compress_audio')],
        [InlineKeyboardButton("بازگشت به منوی اصلی", callback_data='back_to_main')]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    update.message.reply_text('لطفا عملیات مورد نظر را انتخاب کنید:', reply_markup=reply_markup)
    return AUDIO

# تابع بازگشت به منوی اصلی
def back_to_main_menu(update, context):
    keyboard = [
        [InlineKeyboardButton("بخش ویدیویی", callback_data='video')],
        [InlineKeyboardButton("بخش صوتی", callback_data='audio')]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    update.message.reply_text('لطفا یک بخش را انتخاب کنید:', reply_markup=reply_markup)
    return ConversationHandler.END

# تابع ریست کردن ربات
def reset(update, context):
    update.message.reply_text("ربات ریست شد. لطفا دوباره شروع کنید.")
    return start(update, context)

# تابع کم کردن حجم فایل ویدیویی
def compress_video(update, context):
    video = VideoFileClip("video.mp4")
    video.write_videofile("compressed_video.mp4", bitrate="500k")
    update.message.reply_video(video=open("compressed_video.mp4", 'rb'))
    os.remove("video.mp4")
    os.remove("compressed_video.mp4")
    return back_to_main_menu(update, context)

# تابع برش فایل ویدیویی
def cut_video(update, context):
    start_time = "00:00:10"  # زمان شروع برش
    end_time = "00:00:20"    # زمان پایان برش
    video = VideoFileClip("video.mp4").subclip(start_time, end_time)
    video.write_videofile("cut_video.mp4")
    update.message.reply_video(video=open("cut_video.mp4", 'rb'))
    os.remove("video.mp4")
    os.remove("cut_video.mp4")
    return back_to_main_menu(update, context)

# تابع تبدیل فایل ویدیویی به صوت
def convert_video_to_audio(update, context):
    video = VideoFileClip("video.mp4")
    video.audio.write_audiofile("converted_audio.mp3")
    update.message.reply_audio(audio=open("converted_audio.mp3", 'rb'))
    os.remove("video.mp4")
    os.remove("converted_audio.mp3")
    return back_to_main_menu(update, context)

# تابع تغییر اطلاعات آلبوم و خواننده موسیقی
def edit_metadata(update, context):
    audio = EasyID3("audio.mp3")
    audio['artist'] = 'خواننده جدید'
    audio['album'] = 'آلبوم جدید'
    audio.save()
    update.message.reply_audio(audio=open("audio.mp3", 'rb'))
    os.remove("audio.mp3")
    return back_to_main_menu(update, context)

# تابع برش موسیقی
def cut_audio(update, context):
    start_time = 10000  # زمان شروع برش به میلی‌ثانیه
    end_time = 20000    # زمان پایان برش به میلی‌ثانیه
    audio = AudioSegment.from_mp3("audio.mp3")
    cut_audio = audio[start_time:end_time]
    cut_audio.export("cut_audio.mp3", format="mp3")
    update.message.reply_audio(audio=open("cut_audio.mp3", 'rb'))
    os.remove("audio.mp3")
    os.remove("cut_audio.mp3")
    return back_to_main_menu(update, context)

# تابع تغییر عکس آلبوم
def change_album_art(update, context):
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
    update.message.reply_audio(audio=open("audio.mp3", 'rb'))
    os.remove("audio.mp3")
    os.remove("new_album_art.jpg")
    return back_to_main_menu(update, context)

# تابع کم کردن حجم صوت
def compress_audio(update, context):
    audio = AudioSegment.from_mp3("audio.mp3")
    audio = audio.set_channels(1)  # تبدیل به mono
    audio = audio.set_frame_rate(16000)  # تنظیم bit rate
    audio.export("compressed_audio.mp3", format="mp3", bitrate="16k")
    update.message.reply_audio(audio=open("compressed_audio.mp3", 'rb'))
    os.remove("audio.mp3")
    os.remove("compressed_audio.mp3")
    return back_to_main_menu(update, context)

# تابع اصلی
def main():
    updater = Updater(TOKEN, use_context=True)
    dp = updater.dispatcher

    # تعریف ConversationHandler برای مدیریت حالت‌های مختلف
    conv_handler = ConversationHandler(
        entry_points=[CommandHandler('start', start)],
        states={
            VIDEO: [
                MessageHandler(Filters.video, process_video),
                CallbackQueryHandler(compress_video, pattern='compress_video'),
                CallbackQueryHandler(cut_video, pattern='cut_video'),
                CallbackQueryHandler(convert_video_to_audio, pattern='convert_video_to_audio'),
                CallbackQueryHandler(back_to_main_menu, pattern='back_to_main')
            ],
            AUDIO: [
                MessageHandler(Filters.audio, process_audio),
                CallbackQueryHandler(edit_metadata, pattern='edit_metadata'),
                CallbackQueryHandler(cut_audio, pattern='cut_audio'),
                CallbackQueryHandler(change_album_art, pattern='change_album_art'),
                CallbackQueryHandler(compress_audio, pattern='compress_audio'),
                CallbackQueryHandler(back_to_main_menu, pattern='back_to_main')
            ]
        },
        fallbacks=[CommandHandler('reset', reset)]
    )

    dp.add_handler(conv_handler)
    dp.add_handler(CallbackQueryHandler(button))
    dp.add_handler(CommandHandler('reset', reset))

    updater.start_polling()
    updater.idle()

if __name__ == '__main__':
    main()
