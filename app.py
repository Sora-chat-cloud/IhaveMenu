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
    with open('menubase.json', 'r', encoding='utf-8') as f:
        menu_data = json.load(f)

    return render_template('userInput.html', menu_json=json.dumps(menu_data, ensure_ascii=False))

@app.route('/pre-ingredients', methods=['POST'])
def pre_ingredients():
    data_raw = request.form.get('selected_menus_data')
    selected_menus = json.loads(data_raw) if data_raw else []
    
    # ส่งข้อมูลเมนูที่เลือกไปแสดงในหน้าพรีวิวเพื่อให้ User ติ๊กวัตถุดิบแยกแต่ละเมนู
    return render_template('pre-ingredients.html', menus=selected_menus)

@app.route('/api/get-menu', methods=['POST'])
def get_menu():
    try:
        user_ingredients = request.form.get('all_ingredients')
        user_data = json.loads(user_ingredients) if user_ingredients else []

        # เก็บ Map ของชื่อเมนูคู่กับ URL ไว้ (เพื่อเอาไว้ดึงมาแปะคืนทีหลัง)
        url_map = {m['name']: m['image_url'] for m in user_data}

        # สร้างชุดข้อมูลที่ไม่มี Image_url ส่งให้ AI
        menu_pool_for_ai = []
        for m in user_data:
            menu_pool_for_ai.append({
                "name": m['name'],
                "ingredients": m['ingredients']
            })

        results = gemie_menu_recommendation(menu_pool_for_ai)

        # --- กระบวนการ Mapping URL กลับคืน ---
        for item in results:
            item['Image_url'] = url_map.get(item['recipe_name'])

        return render_template('createMenu.html', menus=results)
    except Exception as e:
        print(f"\nError occurred: {str(e)}\n")
        return render_template('error.html', error_message=str(e))


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