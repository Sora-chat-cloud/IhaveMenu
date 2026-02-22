from flask import Flask, render_template, jsonify

app = Flask(__name__)

# หน้าแรกของ Web App (ให้แสดงไฟล์ index.html)
@app.route('/')
def index():
    return render_template('index.html')

@app.route('/user-input')
def user_input_page():
    return render_template('userInput.html')


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

@app.errorhandler(405)
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