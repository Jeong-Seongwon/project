from flask import Flask, render_template, request, redirect, url_for, session
import os
import sqlite3
from predict import Predict

app = Flask(__name__)
app.secret_key = 'your_secret_key'
predict_instance = Predict()

UPLOAD_FOLDER = 'static/uploads'
RESULT_FOLDER = 'static/results'
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER
app.config['RESULT_FOLDER'] = RESULT_FOLDER

# SQLite 데이터베이스 연결
def get_db_connection():
    conn = sqlite3.connect('C:/Users/602-13/k/cctv_manager.sqlite')
    conn.row_factory = sqlite3.Row
    return conn

# 로그 정보 가져오기
def get_logs():
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT date, occurrence_time, incident FROM cctvlog")
    logs = cursor.fetchall()
    conn.close()
    return logs

# 특정 날짜의 로그 정보 가져오기
def get_logs_by_date(date):
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT occurrence_time, incident FROM cctvlog WHERE date = ?", (date,))
    logs = cursor.fetchall()
    conn.close()
    return logs

# logs() 함수 수정
@app.route('/logs', methods=['GET', 'POST'])
def logs():
    if request.method == 'POST':
        date = request.form['date']
        occurrence_time = request.form['occurrence_time']
        incident = request.form['incident']
        
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute("INSERT INTO cctvlog (date, occurrence_time, incident) VALUES (?, ?, ?)", (date, occurrence_time, incident))
        conn.commit()
        conn.close()
        
        # POST 요청 후 리다이렉트하지 않고, logs_data를 다시 가져와서 페이지를 렌더링합니다.
        logs_data = get_logs()
        return render_template('index_frame.html', logs=logs_data)
    else:
        logs_data = get_logs()
        return render_template('index_frame.html', logs=logs_data)

@app.route('/')
def home():
    return render_template('login.html')

# 로그인 페이지 렌더링
@app.route('/login', methods=['GET'])
def login_page():
    return render_template('login.html')

# 로그인 처리
@app.route('/login', methods=['POST'])
def login():
    username = request.form['username']
    password = request.form['password']
    
    # SQLite 데이터베이스 연결
    conn = get_db_connection()
    cursor = conn.cursor()
    
    # 사용자 인증
    cursor.execute("SELECT * FROM PLAYERS WHERE id = ? AND password = ?", (username, password))
    user = cursor.fetchone()
    
    if user:
        # 로그인 성공 시 사용자의 이름 가져오기
        user_name = user['NAME']
        
        # CCTV 페이지로 리다이렉트
        session['username'] = user_name  # 세션에 사용자 이름 저장
        return redirect(url_for('cctv_page'))
    else:
        # 로그인 실패
        return "Invalid username or password"  # 로그인 실패 메시지 출력
    
    conn.close()

# CCTV 페이지 렌더링
@app.route('/cctv_page')
def cctv_page():
    if 'username' in session:
        username = session['username']
        logs = get_logs()  # CCTV 로그 가져오기

        return render_template('cctv.html', username=username, logs=logs)
    else:
        return redirect(url_for('login'))

# CCTV 프레임 페이지 렌더링
@app.route('/cctv_frame')
def cctv_frame():
    if 'username' in session:
        username = session['username']
        logs = get_logs()  # CCTV 로그 가져오기

        return render_template('cctv_frame.html', username=username, logs=logs)
    else:
        return redirect(url_for('login'))

# 인덱스 프레임 렌더링
@app.route('/index_frame')
def index_frame():
    if 'username' in session:
        username = session['username']
        logs = get_logs()
        return render_template('index_frame.html', username=username, logs=logs)
    else:
        return redirect(url_for('login'))

# 특정 날짜 로그 페이지 렌더링
@app.route('/index')
def index():
    if 'username' in session:
        date = request.args.get('date')
        logs = get_logs_by_date(date)
        return render_template('index.html', date=date, logs=logs)
    else:
        return redirect(url_for('login'))

# 로그아웃 처리
@app.route('/logout', methods=['GET'])
def logout():
    session.pop('username', None)  # 세션에서 사용자 이름 제거
    return redirect(url_for('login'))

# 비디오 파일 업로드 및 객체 검출
@app.route('/upload', methods=['POST'])
def upload_file():
    if 'file' not in request.files:
        return redirect(request.url)
    file = request.files['file']
    if file.filename == '':
        return redirect(request.url)
    if file:
        filename = file.filename
        filepath = os.path.join(app.config['UPLOAD_FOLDER'], filename)
        file.save(filepath)
        result_path = predict_instance.detect_objects(filepath)
        result_filename = os.path.basename(result_path)
        return redirect(url_for('show_result', filename=result_filename))

@app.route('/result/<filename>')
def show_result(filename):
    result_file_url = os.path.join(app.config['RESULT_FOLDER'], filename)
    return render_template('cctv_frame.html', result_file=result_file_url)

if __name__ == '__main__':
    app.run(debug=True)
