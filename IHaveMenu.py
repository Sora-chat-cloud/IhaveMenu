from flask import Flask, render_template, request, jsonify, session
import os, json
from dotenv import load_dotenv
from google import genai
from pymongo import MongoClient
from datetime import datetime

mongo_client = MongoClient(os.getenv("MONGODB_URI"))
db = mongo_client["recipe_finder"]
recipes_col = db["recipes"]


# =========================
# Setup
# =========================
load_dotenv()

app = Flask(__name__)
app.secret_key = 'recipe_finder_secret_key'

client = genai.Client(api_key=os.getenv("GEMINI_API_KEY"))
MODEL_NAME = "models/gemini-2.5-flash"

# =========================
# Pages
# =========================
@app.route('/')
def index():
    return render_template('Home.html')

@app.route('/settings')
def settings():
    return render_template('settings.html')

@app.route('/results')
def results():
    return render_template('results.html')

@app.route('/login')
def login():
    return render_template('login.html')

@app.route('/history')
def history():
    return render_template('history.html')

@app.route('/display')
def display():
    return render_template('display.html')

@app.route('/favorites')
def favorites():
    favorite_recipes = session.get('favorites', [])
    return render_template('Favorite.html', recipes=favorite_recipes)

# =========================
# Save user settings
# =========================
@app.route('/api/settings', methods=['POST'])
def save_settings():
    data = request.get_json()
    session['user_settings'] = {
        'time': data.get('time', 30),
        'styles': data.get('styles', []),
        'appliances': data.get('appliances', []),
        'ingredients': data.get('ingredients', [])
    }
    return jsonify({'status': 'success'})


# =========================
# Save ingredients
# =========================
@app.route('/api/ingredients', methods=['POST'])
def save_ingredients():
    data = request.get_json()
    session['ingredients'] = data.get('ingredients', [])
    return jsonify({'status': 'success'})

# =========================
# Generate recipes from Gemini
# =========================
@app.route('/api/generate', methods=['POST'])
def generate_recipes():
    settings = session.get('user_settings', {})
    ingredients = session.get('ingredients', [])

    # 🔹 CACHE CHECK
    styles = settings.get('styles', [])
    cached = list(
        recipes_col.find(
            {"user_settings.styles": {"$in": styles}},
            {"_id": 0}
        ).limit(3)
    )
    if cached:
        return jsonify({"recipes": cached})

    prompt = f"""
    คุณคือ AI ผู้ช่วยแนะนำเมนูอาหาร

    หน้าที่ของคุณคือแนะนำเมนูอาหารตามเงื่อนไขของผู้ใช้ โดยอธิบายให้กระชับ ชัดเจน และเข้าใจง่าย

    ❗ ข้อกำหนดสำคัญ (ต้องทำตามอย่างเคร่งครัด)
    - ค่า "type" ของเมนูอาหาร ต้องเลือกได้จากรายการที่ผู้ใช้เลือกไว้เท่านั้น
    - ห้ามสร้างประเภทอาหารใหม่เด็ดขาด
    - ห้ามใช้คำอื่นนอกเหนือจากรายการนี้
    - ถ้าไม่สามารถเลือกได้ ให้สุ่มเลือกจากรายการที่ผู้ใช้เลือกไว้

    รายการประเภทอาหารที่อนุญาต (Allowed Types):
    {settings.get('styles', [])}

    ตัวอย่างที่ถูกต้อง:
    - หาก Allowed Types = ["thai", "clean"]
    type ต้องเป็น "thai" หรือ "clean" เท่านั้น

    ตัวอย่างที่ผิด (ห้ามทำ):
    - asian
    - healthy
    - fusion
    - japanese
    - diet

    ---

    เงื่อนไขการแนะนำ:
    - แนะนำอาหารจำนวน 3 เมนู
    - เวลาทำอาหารต้องไม่เกิน {settings.get('time', 30)} นาที
    - ใช้อุปกรณ์ที่ผู้ใช้มีเท่านั้น: {settings.get('appliances', [])}
    - ใช้วัตถุดิบที่ผู้ใช้มีเป็นหลัก: {ingredients}

    ข้อมูลที่ต้องให้ในแต่ละเมนู:
    - title: ชื่อเมนูอาหาร (ภาษาไทย)
    - description: คำอธิบายสั้น กระชับ ได้ใจความ
    - type: ต้องเป็นหนึ่งใน Allowed Types เท่านั้น
    - kcal: พลังงานโดยประมาณ (kcal)
    - time: เวลาในการทำอาหาร (นาที)
    - protein: ปริมาณโปรตีน (กรัม)
    - carb: ปริมาณคาร์โบไฮเดรต (กรัม)
    - fat: ปริมาณไขมัน (กรัม)
    - image: URL รูปภาพจาก Unsplash เท่านั้น  
    รูปแบบ: https://source.unsplash.com/600x400/?english-food-name
    - steps: ขั้นตอนการทำอาหาร 3–4 ขั้นตอน กระชับ เข้าใจง่าย

    ตอบเป็น JSON เท่านั้น ห้ามมีข้อความอื่นนอกเหนือจาก JSON

    รูปแบบ JSON:
    {{
    "recipes": [
        {{
        "id": 1,
        "title": "",
        "description": "",
        "type": "",
        "kcal": 0,
        "time": 0,
        "protein": 0,
        "carb": 0,
        "fat": 0,
        "image": "https://source.unsplash.com/600x400/?english-food-name",
        "steps": ["", "", ""]
        }}
    ]
    }}
    """
    try:
        response = client.models.generate_content(
            model=MODEL_NAME,
            contents=prompt
        )

        text = response.text.strip()

        if text.startswith("```"):
            text = text.replace("```json", "").replace("```", "").strip()

        data = json.loads(text)

        # 🔹 SAVE TO DB
        for r in data.get("recipes", []):
            r["createdAt"] = datetime.utcnow()
            r["source"] = "gemini"
            r["user_settings"] = settings
            r["ingredients"] = ingredients
            recipes_col.insert_one(r)

        return jsonify(data)

    except Exception as e:
        print("Gemini ERROR:", e)
        return jsonify({
            "error": "ไม่สามารถสร้างเมนูจาก AI ได้",
            "detail": str(e)
        }), 500

# =========================
# Run server
# =========================
if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5001, debug=True)