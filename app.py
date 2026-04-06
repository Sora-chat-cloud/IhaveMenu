from flask import Flask, render_template, jsonify, request
from services.Head_Chef import gemie_menu_recommendation
import json

app = Flask(__name__)

# หน้าแรกของ Web App (ให้แสดงไฟล์ index.html)
@app.route('/')
def index():
    return render_template('index.html')

@app.route('/user-input')
def user_input_page():
    return render_template('userInput.html')

def score_ingredients(user_ingredients_str, menu_ingredients_str):
    if not user_ingredients_str or not menu_ingredients_str:
        return 0
    
    # 1. เตรียมข้อมูล User: เปลี่ยนเป็นตัวเล็กและตัดช่องว่าง 
    user_input = user_ingredients_str.lower()
    
    # 2. เตรียมข้อมูลเมนู: แยกเป็นลิสต์ของวัตถุดิบแต่ละชนิด
    menu_items = [item.strip().lower() for item in menu_ingredients_str.split(',')]
    
    score = 0
    # 3. เช็คทีละอย่างว่า วัตถุดิบในเมนู 'มีอยู่ใน' ข้อความที่ User ส่งมาไหม
    for item in menu_items:
        if item in user_input:
            score += 1
            
    return score

@app.route('/api/get-menu', methods=['POST'])
def get_menu():
    try:
        # 1. รับข้อมูลจาก User
        user_ingredients = request.form.get('ingredients') 
        food_type = request.form.get('food_type')         
        time_limit = request.form.get('time')

        # 2. โหลดฐานข้อมูล MenuBase.json
        with open('menubase.json', 'r', encoding='utf-8') as f:
            all_menus = json.load(f)

        # 3. กรองเฉพาะ Category ที่ใช้
        filtered_menus = [m for m in all_menus if m['Category'] == food_type]

        # 4. กระบวนการ Scoring
        scored_list = []
        for menu in filtered_menus:
            score = score_ingredients(user_ingredients, menu['ingredients'])
            scored_list.append({
                "menu_data": menu,
                "score": score
            })

        # 5. เรียงลำดับตามคะแนน (มากไปน้อย) และเลือก Top 3
        top_menus = sorted(scored_list, key=lambda x: x['score'], reverse=True)[:3]
        
        # ดึงเฉพาะข้อมูลเมนูออกมาเป็น List
        final_menu_pool = [item['menu_data'] for item in top_menus]
        # เก็บ Map ของชื่อเมนูคู่กับ URL ไว้ (เพื่อเอาไว้ดึงมาแปะคืนทีหลัง)
        url_map = {m['name']: m['Image_url'] for m in final_menu_pool}

        # สร้างชุดข้อมูลที่ไม่มี Image_url ส่งให้ AI
        menu_pool_for_ai = []
        for m in final_menu_pool:
            menu_pool_for_ai.append({
                "Category": m['Category'],
                "name": m['name'],
                "ingredients": m['ingredients']
            })
        
        results = gemie_menu_recommendation(
            user_ingredients=user_ingredients,
            menu_pool=menu_pool_for_ai,
            time_limit=time_limit
        )

        # --- กระบวนการ Mapping URL กลับคืน ---
        for item in results:
            item['Image_url'] = url_map.get(item['recipe_name'])

        return render_template('createMenu.html', menus=results)

    except Exception as e:
        print(f"Scoring Error: {e}")
        return f"เกิดข้อผิดพลาด: {str(e)}", 500


# ------ errorhandler ------
@app.errorhandler(404)
def not_found(e):
    return jsonify({
        "msg": "ไม่รู้จัก Route ที่เรียกใช้นะจ๊ะ",
        "code": 404
    }), 404

@app.errorhandler(405)
def method_not_allowed(e):
    return jsonify({
        "msg": "Method ไม่ถูกต้องจร้า",
        "code": 405
    }), 405

@app.errorhandler(400)
def bad_request(e):
    return jsonify({
        "msg": "ส่งข้อมูลมาไม่ถูก pattern",
        "code": 400
    }), 400

@app.errorhandler(500)
def server_error(e):
    return jsonify({
        "msg": "Internal Server Error",
        "code": 500
    }), 500

@app.errorhandler(502)
def bad_gateway(e):
    return jsonify({
        "msg": "Bad Gateway",
        "code": 502
    }), 502

@app.errorhandler(503)
def service_unavailable(e):
    return jsonify({
        "msg": "Service Unavailable",
        "code": 503
    }), 503

@app.errorhandler(504)
def gateway_timeout(e):
    return jsonify({
        "msg": "Gateway Timeout",
        "code": 504
    }), 504    

if __name__ == '__main__':
    # รันบน Port 5000 และเปิด Debug mode ไว้ตอนพัฒนา
    app.run(host='0.0.0.0', port=5000, debug=True)