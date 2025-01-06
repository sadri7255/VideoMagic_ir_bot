# استفاده از یک تصویر پایه پایتون
FROM python:3.9-slim

# تنظیم دایرکتوری کاری
WORKDIR /app

# کپی فایل‌های پروژه
COPY . .

# نصب وابستگی‌های سیستم (ffmpeg)
RUN apt-get update && apt-get install -y ffmpeg && rm -rf /var/lib/apt/lists/*

# نصب وابستگی‌های پایتون
RUN pip install --no-cache-dir -r requirements.txt

# اجرای ربات
CMD ["python", "bot.py"]