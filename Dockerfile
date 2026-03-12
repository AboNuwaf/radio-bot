FROM python:3.11-slim

# تثبيت FFmpeg
RUN apt-get update && apt-get install -y ffmpeg && apt-get clean

# مجلد العمل
WORKDIR /app

# تثبيت المتطلبات
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# نسخ ملفات البوت
COPY AboNuwaf.py .

# تشغيل البوت
CMD ["python", "AboNuwaf.py"]
