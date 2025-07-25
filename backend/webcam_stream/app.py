# app.py (이 파일을 웹캠이 연결된 노트북에서 실행합니다)

from flask import Flask, Response, render_template
import cv2
import threading
import time

app = Flask(__name__)

# 웹캠 객체 및 프레임 저장 변수 초기화
camera = None
output_frame = None
lock = threading.Lock() # 스레드 간 안전한 프레임 공유를 위한 락

# 웹캠 초기화 함수
def initialize_camera():
    global camera
    if camera is None or not camera.isOpened():
        camera = cv2.VideoCapture(0)  # 0은 기본 웹캠을 의미합니다. 다른 카메라라면 번호를 변경하세요.
        time.sleep(1) # 카메라가 완전히 초기화될 시간을 줍니다.
        if not camera.isOpened():
            print("웹캠을 열 수 없습니다. 카메라가 연결되어 있고 사용 중이 아닌지 확인하세요.")
            return False
    return True

# 웹캠으로부터 프레임을 읽고 MJPEG 형식으로 인코딩하는 함수
def generate_frames():
    global output_frame, lock
    print("프레임 생성 시작...")

    if not initialize_camera():
        yield (b'--frame\r\n'
               b'Content-Type: text/plain\r\n\r\n'
               b'Webcam initialization failed. Cannot start stream.\r\n') # 한글 메시지를 영문으로 변경
        return

    while True:
        success, frame = camera.read()
        if not success:
            print("프레임을 읽는 데 실패했습니다. 스트림 종료.")
            break
        else:
            # JPEG로 인코딩
            ret, buffer = cv2.imencode('.jpg', frame)
            if not ret:
                print("프레임 인코딩 실패.")
                continue

            # 인코딩된 프레임을 공유 변수에 저장
            with lock:
                output_frame = buffer.tobytes()
            
            # 클라이언트에게 프레임 전송
            yield (b'--frame\r\n'
                   b'Content-Type: image/jpeg\r\n\r\n' + output_frame + b'\r\n')
        
        # CPU 사용량을 줄이기 위해 잠시 대기
        time.sleep(0.05) # 약 30 FPS를 목표 (조정 가능)

# MJPEG 스트림을 제공하는 라우트
@app.route('/video_feed')
def video_feed():
    print("'/video_feed' 요청 수신.")
    return Response(generate_frames(),
                    mimetype='multipart/x-mixed-replace; boundary=frame')

# 루트 경로 ('/')로 접속하면 viewer.html을 보여주는 라우트 추가 또는 수정
@app.route('/')
def index():
    # Flask는 기본적으로 'templates' 폴더 안에서 'viewer.html' 파일을 찾습니다.
    return render_template('viewer.html')


if __name__ == '__main__':
    print("Flask 애플리케이션 시작...")
    # 0.0.0.0은 모든 네트워크 인터페이스에서 접근 가능하게 합니다.
    # 포트는 5000 (기본 Flask 포트)
    app.run(host='0.0.0.0', port=5000, debug=False) # 개발 완료 후 debug=False 권장
    
    # 애플리케이션 종료 시 웹캠 자원 해제
    if camera:
        camera.release()
        cv2.destroyAllWindows()