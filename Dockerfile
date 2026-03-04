FROM python:3.10-slim

# Tizimga FFmpeg o'rnatamiz
RUN apt-get update && apt-get install -y ffmpeg && apt-get clean

# Ishchi papkani yaratamiz
WORKDIR /app

# Kutubxonalarni o'rnatamiz
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Bot kodini ko'chiramiz
COPY . .

# Botni ishga tushiramiz
CMD ["python", "bot.py"]
