# Pic-tag 대시보드 시스템

## 개요

Pic-tag 대시보드는 실시간 영상 스트리밍과 모니터링 기능을 제공하는 웹 기반 관리 인터페이스입니다. Django와 WebSocket을 기반으로 구축되어 다중 사용자 간 실시간 화상통화와 영상 분석 기능을 지원합니다.

## 주요 기능

### 🎥 실시간 영상 모니터링
- 웹캠을 통한 실시간 영상 스트리밍
- 다중 카메라 뷰 지원 (일반/미러/흑백 모드)
- WebRTC 기반 P2P 화상통화
- 실시간 영상 제어 (재생/일시정지/시크)

### 🔍 객체 감지 및 탐색
- AI 모델을 통한 실시간 객체 감지 (준비 중)
- 감지된 객체의 크롭 이미지 표시
- 시간별 감지 로그 추적
- 감지 이벤트 타임라인

### 📊 통계 분석
- 일일 입장자/퇴장자 통계
- 현재 체류 인원 표시
- 평균 체류시간 계산
- 실시간 입출 로그 테이블

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
├── dashboard/                  # 기본 대시보드 앱
├── monitoring/                 # 실시간 모니터링 앱
│   ├── views.py              # 웹 뷰 핸들러
│   ├── consumers.py          # WebSocket 컨슈머
│   ├── routing.py            # WebSocket 라우팅
│   └── urls.py               # URL 패턴
├── templates/
│   └── dashboard.html        # 메인 대시보드 템플릿
└── requirements              # Python 의존성 목록
```

## 기술 스택

- **백엔드**: Django 5.2.4, Django Channels 4.0.0
- **프론트엔드**: HTML5, CSS3, JavaScript (ES6+)
- **실시간 통신**: WebSocket, WebRTC
- **데이터베이스**: SQLite (개발용)
- **채널 레이어**: InMemoryChannelLayer (개발용)

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

### 3. 개발 서버 실행
```bash
python manage.py runserver
```

### 4. 접속
브라우저에서 `http://localhost:8000/` 접속
- **로그인 정보**: ID: `admin`, PW: `admin123`

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

### 통계 분석
1. "통계 분석" 메뉴 선택
2. 상단 카드에서 실시간 통계 확인
3. 하단 테이블에서 상세 입출 로그 확인
4. 데이터는 자동으로 실시간 업데이트

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
4. JavaScript 함수로 프론트엔드 로직 구현

### WebSocket 기능 확장
1. `monitoring/consumers.py`에 새 메시지 타입 처리 추가
2. 프론트엔드에서 해당 메시지 송수신 로직 구현
3. `handleWebSocketMessage()` 함수에 케이스 추가

### 스타일 커스터마이징
- `dashboard.html`의 `<style>` 섹션에서 CSS 수정
- 색상 테마: `#1a237e` (메인), `#000000` (헤더), `#f8f8f8` (배경)
- 반응형 미디어 쿼리 활용

## 문제 해결

### 웹캠 접근 오류
- HTTPS 환경에서 실행 (Chrome 보안 정책)
- 브라우저 카메라 권한 설정 확인
- 다른 프로그램의 카메라 사용 여부 확인

### WebSocket 연결 실패
- 방화벽 설정 확인
- 개발 서버 정상 실행 상태 확인
- 브라우저 콘솔에서 에러 메시지 확인

### 성능 최적화
- Redis를 통한 채널 레이어 교체 권장 (프로덕션)
- 영상 품질 설정 조정
- 불필요한 실시간 업데이트 주기 조정

## 향후 개발 계획

### 단기 목표
- YOLO 모델 통합을 통한 실제 객체 감지
- 사용자 인증 시스템 강화
- 영상 녹화 및 저장 기능

### 장기 목표
- Redis 기반 확장 가능한 채널 레이어
- 관리자 대시보드 분리
- API 기반 외부 시스템 연동
- 클라우드 배포 및 스케일링

## 라이센스

이 대시보드 시스템은 학습 목적으로 개발되었습니다.