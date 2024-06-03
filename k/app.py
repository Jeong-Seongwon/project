import os
from flask import Flask, render_template, request, redirect, url_for, session, Response
import sqlite3
import cv2
import datetime
from ultralytics import YOLO
import threading
import time

app = Flask(__name__)
app.secret_key = 'your_secret_key'  # 세션을 보호하기 위한 비밀 키 설정

UPLOAD_FOLDER = 'static/uploads'  # 파일 업로드 폴더 경로 설정
RESULT_FOLDER = 'static/results'  # 결과 파일 저장 폴더 경로 설정
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER
app.config['RESULT_FOLDER'] = RESULT_FOLDER

class CCTVStream:
    def __init__(self, url):
        self.url = url
        self.size = (960, 540)
        self.model = YOLO('./model_train/runs/detect/train/weights/best.pt')
        # label.txt 에서 label 목록 가져오기
        self.labels=[]
        with open("./model_train/label.txt", "r", encoding="utf-8") as f:
            lines = f.readlines()
            for line in lines:
                line = line.strip()
                self.labels.append(line)
        self.continuous_detection_count = 0
        self.printed_detection = False
        
    def generate_frames(self):
        self.camera = cv2.VideoCapture(self.url)
        if not self.camera.isOpened():
            print(f"Error: Unable to open camera with URL {self.url}.")
            return
        
        fps = int(self.camera.get(cv2.CAP_PROP_FPS))
        date = datetime.date.today()
        directory = "static/results"
        if not os.path.exists(directory):
            os.makedirs(directory)
        self.cctv = os.path.splitext(self.url.split("/")[-1])[0] # 동영상 파일
        # cctv = "cctv_" + self.url # 카메라 순서대로
        filename = f"{self.cctv}_{date.strftime('%Y-%m-%d')}_yolo.avi"
        filepath = os.path.join(directory, filename)
        fourcc = cv2.VideoWriter_fourcc(*'XVID')
        out = cv2.VideoWriter(filepath, fourcc, fps, self.size)
        
        while self.camera.isOpened():
            success, frame = self.camera.read()
            if not success:
                break
            else:
                # Assuming `predictor.size` gives the desired size for resizing
                resized_frame = cv2.resize(frame, self.size)
                
                # Convert BGR to RGB for model prediction
                rgb_frame = cv2.cvtColor(resized_frame, cv2.COLOR_BGR2RGB)
                
                # Model prediction
                results = self.model(rgb_frame)
                
                # Assuming `results[0].plot()` returns an image in RGB format
                plots = results[0].plot()
                
                # Convert the RGB image to BGR format for OpenCV
                bgr_plots = cv2.cvtColor(plots, cv2.COLOR_RGB2BGR)
                out.write(bgr_plots)

                # 검출된 객체 정보를 데이터베이스에 저장
                if results[0].boxes:
                    if self.continuous_detection_count < 150:
                        self.continuous_detection_count += 1
        
                    # 결과가 이미 출력되지 않았고, 연속 객체 검출 횟수가 150이 되었을 때
                    if not self.printed_detection and self.continuous_detection_count == 150:
                        # 5초간 지속되면
                        self.predict_results(results)
                        self.results_to_database()  # db에 저장
                        self.printed_detection = True  # 결과 출력 플래그를 설정
                        self.start_timer()
        
                else:
                    if self.continuous_detection_count > 0:
                        self.continuous_detection_count -= 1

                # Encode frame to JPEG
                ret, buffer = cv2.imencode('.jpg', bgr_plots)
                if not ret:
                    continue
                
                frame = buffer.tobytes()
                yield (b'--frame\r\n'
                       b'Content-Type: image/jpeg\r\n\r\n' + frame + b'\r\n')

        self.camera.release()
        out.release()
        
    def start_timer(self): # 결과 출력 여부 타이머 쓰레드
        timer_thread = threading.Thread(target=self.reset_printed_detection)
        timer_thread.daemon = True
        timer_thread.start()
    
    
    
    def reset_printed_detection(self):
        # 1분 후에 결과 출력 여부 초기화
        time.sleep(60)
        self.printed_detection = False
        
    
    
    def predict_results(self, results):
        # 결과에서 라벨인덱스 검출
        for r in results:
            self.results_label = []
            for cls_value in r.boxes.cls:
                label_index = int(cls_value.item())
                # label 검출
                self.results_label.append(self.labels[label_index])
        
        self.incident = ",".join(self.results_label)

        # 현재 날짜를 가져옵니다.
        self.current_date = datetime.date.today()

        # 년월일 형식으로 날짜를 출력합니다.
        self.formatted_date = self.current_date.strftime("%Y-%m-%d")

        # 재생 시간 얻기
        playback_time_ms = self.camera.get(cv2.CAP_PROP_POS_MSEC)

        # 밀리초(ms)를 시, 분, 초로 변환
        playback_time_sec = playback_time_ms // 1000
        self.hours = int(playback_time_sec // 3600)
        self.minutes = int((playback_time_sec % 3600) // 60)
        self.seconds = int(playback_time_sec % 60)

        self.occurrence_time = "{:02d}:{:02d}:{:02d}".format(self.hours, self.minutes, self.seconds)


    def results_to_database(self):
        db_path = "cctv_manager.sqlite"
        
        # 데이터베이스 연결 설정
        with sqlite3.connect(db_path) as conn:
            cursor = conn.cursor()

            # 예측 결과를 데이터베이스에 삽입하는 SQL 쿼리
            insert_query = "INSERT INTO cctvlog (cctv, date, occurrence_time, incident) VALUES (?, ?, ?, ?)"  # 필요한 만큼 열과 값을 적절히 수정

            # 쿼리 실행
            cursor.execute(insert_query, (self.cctv, self.formatted_date, self.occurrence_time, self.incident))  # 결과 값에 맞게 값을 수정

            # 변경사항 커밋
            conn.commit()
            
            
# SQLite 데이터베이스 연결 함수
def get_db_connection():
    conn = sqlite3.connect('C:/Users/602-13/k/cctv_manager.sqlite')
    conn.row_factory = sqlite3.Row
    return conn

# 로그 정보 가져오기
def get_logs():
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM cctvlog")
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

# 로그 정보 조회 및 추가 처리
@app.route('/logs', methods=['GET', 'POST'])
def logs():
    if request.method == 'POST':
        cctv = request.form['cctv']
        date = request.form['date']
        occurrence_time = request.form['occurrence_time']
        incident = request.form['incident']
        
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute("INSERT INTO cctvlog (cctv, date, occurrence_time, incident) VALUES (?, ?, ?, ?)", (cctv, date, occurrence_time, incident))
        conn.commit()
        conn.close()
        
        logs_data = get_logs()
        return render_template('index_frame.html', logs=logs_data)
    else:
        logs_data = get_logs()
        return render_template('index_frame.html', logs=logs_data)

# 기본 경로로 접근할 때 로그인 페이지 렌더링
@app.route('/')
def home():
    return render_template('login.html')

# 로그인 페이지 렌더링
@app.route('/login', methods=['GET'])
def login_page():
    return render_template('login.html')

# CCTV 페이지 렌더링
@app.route('/cctv_page', methods=['GET'])
def cctv_page():
    return render_template('cctv.html')

# 로그인 처리
@app.route('/login', methods=['POST'])
def login():
    username = request.form['username']
    password = request.form['password']
    
    conn = get_db_connection()
    cursor = conn.cursor()
    
    # 사용자 인증
    cursor.execute("SELECT * FROM PLAYERS WHERE id = ? AND password = ?", (username, password))
    user = cursor.fetchone()
    
    if user:
        user_name = user['NAME']
        session['username'] = user_name  # 세션에 사용자 이름 저장
        return redirect(url_for('cctv_page'))  # CCTV 페이지로 리디렉트
    else:
        return "Invalid username or password"  # 로그인 실패 메시지 출력
    
    conn.close()

# CCTV 스트림 URL 리스트
stream_urls = [
    'static/swoon.mp4',
    'static/fight.mp4',
    'static/dump.mp4',
    'static/vandalism.mp4'
]

# CCTV 프레임 페이지 렌더링
@app.route('/cctv_frame')
def cctv_frame():
    if 'username' in session:
        username = session['username']
        logs = get_logs()
        video_feed_urls = []

        for i, url in enumerate(stream_urls):
            cctv_name = os.path.splitext(url.split("/")[-1])[0]
            function_name = 'video_feed_{}_{}'.format(cctv_name, i)  # 고유한 이름 생성
            video_feed_urls.append(function_name)

        return render_template('cctv_frame.html', username=username, logs=logs, stream_urls=video_feed_urls)
    else:
        return redirect(url_for('login'))

# 동적 URL 라우팅을 사용하여 동적 변수 처리
@app.route('/video_feed/<cctv_name>')
def generate_video_feed_route(cctv_name):
    url = stream_urls[int(cctv_name.split("_")[-1])]  # CCTV 이름에서 인덱스 추출하여 URL 가져오기
    return Response(CCTVStream(url).generate_frames(), mimetype='multipart/x-mixed-replace; boundary=frame')

# 결과 페이지 렌더링
@app.route('/show_result')
def show_result():
    result_file = 'static/swoon.mp4'
    sub_cctv1_file = 'static/fight.mp4'
    sub_cctv2_file = 'static/dump.mp4'
    sub_cctv3_file = 'static/vandalism.mp4'
    return render_template('show_result.html', result_file=result_file, sub_cctv1_file=sub_cctv1_file,sub_cctv2_file=sub_cctv2_file, sub_cctv3_file=sub_cctv3_file)

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

'''
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
        result_path = predictor.detect_objects(filepath)  # Predict 클래스의 메서드 호출
        result_filename = os.path.basename(result_path)
        return redirect(url_for('show_result', filename=result_filename))
'''
# 애플리케이션 실행
if __name__ == '__main__':
    app.run(debug=True)
