# Pic-tag 대시보드 시스템

## 개요

Pic-tag 대시보드는 실시간 영상 스트리밍과 모니터링 기능을 제공하는 웹 기반 CCTV 관리 인터페이스입니다. Django와 WebSocket을 기반으로 구축되어 다중 위치의 실시간 웹캠 스트리밍과 고급 통계 분석 기능을 지원합니다.

## 주요 기능

### 🎥 실시간 CCTV 모니터링
- 위치별 웹캠을 통한 실시간 영상 스트리밍
- 4개 위치 동시 모니터링 (현관 입구, 주차장, 복도, 비상구)
- WebRTC 기반 P2P 영상 전송
- 통합 관리자 대시보드 및 위치별 카메라 송출

### 🔍 객체 감지 및 탐색
- AI 모델을 통한 실시간 객체 감지 (준비 중)
- 감지된 객체의 크롭 이미지 표시
- 시간별 감지 로그 추적
- 감지 이벤트 타임라인

### 📊 고급 통계 분석
- **시각화 차트**: Chart.js 기반 4종 차트
  - 시간대별 감지 현황 (라인 차트)
  - 카메라별 감지 분포 (도넛 차트)
  - 주간 감지 추이 (바 차트)
  - 신뢰도 분포 (컬러 바 차트)
- **실시간 지표**: 감지 수, 고유 인원, 활성 카메라, 평균 신뢰도
- **identity_log 기반 데이터**: SQLite 스키마 준비 완료
- **인원 추적**: 개별 인원별 상태 모니터링
- **필터링 및 검색**: 카메라별 로그 필터링

### ⚙️ 시스템 설정
- 영상 인식 옵션 설정
- 알림 기능 관리
- 시스템 백업 및 모니터링 설정

## 프로젝트 구조

```
backend/
├── backend/                    # Django 프로젝트 설정
│   ├── settings.py            # 설정 파일
│   ├── urls.py               # 메인 URL 라우팅
│   ├── asgi.py               # ASGI 설정 (WebSocket)
│   └── wsgi.py               # WSGI 설정
├── monitoring/                 # 실시간 모니터링 앱 (핵심)
│   ├── views.py              # 웹 뷰 핸들러
│   ├── consumers.py          # WebSocket 컨슈머
│   ├── routing.py            # WebSocket 라우팅
│   ├── urls.py               # URL 패턴
│   └── migrations/           # 데이터베이스 마이그레이션
├── static/                     # 정적 파일 (새로 생성)
│   ├── css/                  # CSS 스타일시트
│   ├── js/                   # JavaScript 파일
│   └── images/               # 이미지 리소스
├── templates/
│   └── dashboard.html        # 메인 대시보드 템플릿
├── cert.pem                   # SSL 인증서 (gitignore됨)
├── key.pem                    # SSL 개인키 (gitignore됨)
└── requirements              # Python 의존성 목록
```

## 기술 스택

- **백엔드**: Django 5.2.4, Django Channels 4.0.0
- **프론트엔드**: HTML5, CSS3, JavaScript (ES6+)
- **차트 라이브러리**: Chart.js 4.x
- **실시간 통신**: WebSocket, WebRTC
- **데이터베이스**: SQLite (개발용)
- **채널 레이어**: InMemoryChannelLayer (개발용)
- **ASGI 서버**: Daphne (WebSocket 지원)

## 설치 및 실행

### 1. 의존성 설치
```bash
cd backend
pip install -r requirements
```

### 2. 데이터베이스 마이그레이션
```bash
python manage.py migrate
```

### 3. ASGI 서버 실행 (WebSocket 지원)
```bash
# HTTP 서버 (개발용)
daphne -b 0.0.0.0 -p 8000 backend.asgi:application

# HTTPS 서버 (권장 - 웹캠 접근)
daphne -e ssl:8000:privateKey=key.pem:certKey=cert.pem backend.asgi:application
```

### 4. 접속
- **로컬**: http://localhost:8000 또는 https://localhost:8000
- **네트워크**: http://[IP]:8000 또는 https://[IP]:8000

### 5. 로그인 계정

#### 통합 관리자 (모든 CCTV 수신)
- **ID**: `admin`, **PW**: `admin123` (위치 선택 안함)

#### 위치별 카메라 송출 계정
- **현관 입구**: `entrance` / `entrance123`
- **주차장**: `parking` / `parking123`
- **복도**: `hallway` / `hallway123`
- **비상구**: `emergency` / `emergency123`

## 사용 방법

### 로그인
1. 메인 페이지에서 로그인 폼 확인
2. 기본 계정으로 로그인 (admin/admin123)
3. 대시보드 메인 화면 진입

### 실시간 영상 모니터링
1. 좌측 사이드바에서 "실시간 영상감지" 선택
2. 브라우저 카메라 권한 허용
3. 메인 화면에서 실시간 웹캠 영상 확인
4. 우측 카메라 썸네일에서 다른 뷰 선택 가능
5. 하단 타임라인과 컨트롤 버튼으로 영상 제어

### 다중 사용자 화상통화
1. 여러 브라우저 창 또는 다른 기기에서 동시 접속
2. WebSocket을 통한 자동 P2P 연결 설정
3. 각 사용자의 영상이 카메라 썸네일에 표시
4. 썸네일 클릭으로 메인 화면에서 해당 사용자 영상 확인

### 객체 탐색 (UI 준비 완료)
1. "탐색" 메뉴 선택
2. 메인 영상 화면에서 감지 결과 확인 (AI 모델 연동 예정)
3. 하단 크롭 영역에서 감지된 객체들 확인
4. 우측 패널에서 실시간 감지 로그 확인

### 고급 통계 분석
1. "통계 분석" 메뉴 선택
2. **주요 지표 카드**: 감지 수, 고유 인원, 활성 카메라, 신뢰도 (+변화율)
3. **시각화 차트**: 
   - 시간대별 감지 현황 (라인 차트)
   - 카메라별 감지 분포 (도넛 차트)  
   - 주간 감지 추이 (바 차트)
   - 신뢰도 분포 (컬러 바 차트)
4. **실시간 로그**: identity_log 기반 데이터, 카메라별 필터링
5. **인원 추적**: 개별 인원 상태 및 활성도 모니터링

### 시스템 설정
1. "시스템 설정" 메뉴 선택
2. 영상 인식, 알림, 시스템 관리 옵션 설정
3. iOS 스타일 토글로 각 기능 활성화/비활성화

## 주요 특징

### 반응형 디자인
- 데스크톱, 태블릿, 모바일 완전 지원
- 1024px, 768px 브레이크포인트
- 터치 제스처 (스와이프로 카메라 전환)
- 키보드 단축키 (스페이스바: 재생/정지, 1-4: 카메라 선택)

### 실시간 업데이트
- 1초마다 시간 자동 업데이트
- 10초마다 통계 데이터 갱신
- 15초마다 새 로그 엔트리 확인
- 8초마다 감지 로그 업데이트
- 2초마다 재생 시뮬레이션

### WebSocket 실시간 통신
- 사용자 입장/퇴장 이벤트 처리
- WebRTC Offer/Answer/ICE Candidate 교환
- 자동 재연결 (3초 간격)
- JSON 기반 메시지 프로토콜

### 보안 및 안정성
- Django CSRF 보호
- 안전한 WebSocket 연결
- 에러 핸들링 및 사용자 피드백
- 브라우저 호환성 검사

## API 엔드포인트

### HTTP 엔드포인트
- `GET /` - 메인 대시보드
- `GET /monitoring/` - 모니터링 페이지
- `GET /detection/` - 탐색 페이지  
- `GET /statistics/` - 통계 페이지
- `GET /settings/` - 설정 페이지

### WebSocket 엔드포인트
- `ws://localhost:8000/ws/video_call/` - 화상통화 WebSocket

### WebSocket 메시지 프로토콜
```javascript
// Offer 전송
{
  "type": "offer",
  "offer": RTCSessionDescription,
  "to_user": "user_id"
}

// Answer 전송
{
  "type": "answer", 
  "answer": RTCSessionDescription,
  "to_user": "user_id"
}

// ICE Candidate 전송
{
  "type": "ice_candidate",
  "candidate": RTCIceCandidate,
  "to_user": "user_id"
}
```

## 개발 가이드

### 새로운 기능 추가
1. `monitoring/views.py`에 뷰 함수 추가
2. `monitoring/urls.py`에 URL 패턴 추가
3. `templates/dashboard.html`에 UI 요소 추가
4. `static/js/`에 JavaScript 모듈 추가 (권장)
5. `static/css/`에 스타일시트 추가 (권장)

### WebSocket 기능 확장
1. `monitoring/consumers.py`에 새 메시지 타입 처리 추가
2. 프론트엔드에서 해당 메시지 송수신 로직 구현
3. `handleWebSocketMessage()` 함수에 케이스 추가

### 스타일 커스터마이징
- **현재**: `dashboard.html`의 `<style>` 섹션에서 CSS 수정
- **권장**: `static/css/` 폴더에 별도 CSS 파일 생성 후 분리
- 색상 테마: `#1a237e` (메인), `#000000` (헤더), `#f8f8f8` (배경)
- 반응형 미디어 쿼리 활용

## 문제 해결

### 웹캠 접근 오류 (다른 PC에서)
Chrome에서 HTTP 연결 시 IP 주소로 접속하면 웹캠 접근이 차단됩니다.

**해결방법 1: Chrome 플래그 설정**
1. Chrome 주소창에 입력: `chrome://flags/#unsafely-treat-insecure-origin-as-secure`
2. `http://[서버IP]:8000` 입력 후 "Enabled" 선택
3. Chrome 재시작

**해결방법 2: HTTPS 서버 사용**
```bash
# SSL 인증서 생성
openssl req -x509 -newkey rsa:4096 -keyout key.pem -out cert.pem -days 365 -nodes

# HTTPS 서버 실행
daphne -e ssl:8000:privateKey=key.pem:certKey=cert.pem backend.asgi:application
```

**해결방법 3: 다른 브라우저 사용**
- Firefox: HTTP에서도 웹캠 접근 가능
- Edge: 비교적 관대한 정책

### WebSocket 연결 실패
- ASGI 서버(Daphne) 사용 필수 (Django runserver는 WebSocket 미지원)
- 방화벽 설정 확인
- 브라우저 콘솔에서 에러 메시지 확인

### 성능 최적화
- Redis를 통한 채널 레이어 교체 권장 (프로덕션)
- 영상 품질 설정 조정
- 차트 렌더링 최적화

## 데이터베이스 스키마

### identity_log 테이블 (준비 완료)
```sql
CREATE TABLE IF NOT EXISTS identity_log (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    person_id INTEGER NOT NULL,
    embedding TEXT NOT NULL,
    file_path TEXT,
    camera_id INTEGER,
    bb_x1 INTEGER,
    bb_y1 INTEGER,
    bb_x2 INTEGER,
    bb_y2 INTEGER
)
```

### 현재 하드코딩 데이터
- 10개 샘플 로그 엔트리
- 4개 카메라 (현관입구=1, 주차장=2, 복도=3, 비상구=4)
- 6명 고유 인원 (person_id: 1001-1006)
- 실시간 시뮬레이션 데이터

## 최근 변경사항 (2025.07.25)

### ✅ 완료된 개선사항
- **프로젝트 구조 정리**: 사용하지 않는 `dashboard` 앱 제거
- **static 폴더 구조 생성**: CSS/JS 분리를 위한 폴더 준비
- **보안 강화**: `.gitignore`에 보안 파일 추가 (*.pem, *.key, .env)
- **코드 정리**: 불필요한 기본 파일들 제거 (admin.py, models.py, tests.py)
- **settings.py 업데이트**: INSTALLED_APPS에서 dashboard 제거

### 📁 새로운 프로젝트 구조
- `static/css/` - CSS 파일 분리 준비 완료
- `static/js/` - JavaScript 모듈 분리 준비 완료  
- `static/images/` - 이미지 리소스 관리
- 핵심 기능만 `monitoring` 앱에 집중

## 향후 개발 계획

### 단기 목표 (우선순위 높음)
- **정적 파일 분리**: HTML에서 CSS/JS 분리
- **템플릿 상속**: base.html 구조 도입
- SQLite 연동을 통한 실제 데이터 저장
- YOLO 모델 통합을 통한 실제 객체 감지

### 중기 목표
- 영상 녹화 및 저장 기능
- 통계 데이터 실시간 업데이트
- 반응형 디자인 개선

### 장기 목표
- Redis 기반 확장 가능한 채널 레이어
- 머신러닝 기반 이상 행동 감지
- API 기반 외부 시스템 연동
- 클라우드 배포 및 스케일링

## 라이센스

이 대시보드 시스템은 학습 목적으로 개발되었습니다.