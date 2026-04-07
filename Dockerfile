# 1. ใช้ Image ตามที่คุณต้องการ
FROM python:3.12-slim

# 2. ตั้งค่าพื้นที่ทำงานใน Container
WORKDIR /app

# 3. คัดลอกไฟล์ requirements เพื่อติดตั้ง Library
COPY requirements.txt .

# 4. ติดตั้ง Library 
RUN pip install --no-cache-dir -r requirements.txt

# 5. คัดลอกไฟล์ทั้งหมดในโปรเจคเข้าไปใน Container
COPY . .

# 6. ตั้ง Port สำหรับ Render (ปกติ Render จะกำหนด Port มาให้ผ่าน Env)
ENV PORT=10000
EXPOSE 10000

# 7. คำสั่งรัน Server โดยใช้ Gunicorn (แนะนำสำหรับ Production)
# app:app หมายถึง ไฟล์ app.py และตัวแปร app = Flask(__name__)
CMD ["sh", "-c", "gunicorn --bind 0.0.0.0:$PORT app:app"]