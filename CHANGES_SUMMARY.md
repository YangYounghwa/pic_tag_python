# 프로젝트 수정 사항 요약

## 개요
pic_tag_python 프로젝트에서 Person ID별 이미지 조회 기능과 실시간 탐색 기능을 추가하였습니다.

## 수정된 파일 및 추가된 기능

### 1. 백엔드 API 기능 추가

#### `backend/db_statistics/get_by_id.py`
**추가된 함수:**
```python
def get_person_images_by_id(db_path, person_id)
```
**기능:**
- DB에서 특정 person_id의 이미지 파일 경로들 조회
- 이미지 파일을 base64로 인코딩하여 반환
- 최대 10개 이미지 제한
- 타임스탬프, 카메라 ID, 파일명 포함
- 에러 처리로 파일 읽기 실패시 건너뛰기

**추가된 import:**
- `import os`
- `import base64`




### 2. 프론트엔드 기능 강화

#### `backend/monitoring/static/js/dashboard_script.js`
**추가된 함수들:**

**자동 업데이트 관련:**
```javascript
function startExploreAutoUpdate(intervalSeconds = 15)
function stopExploreAutoUpdate()
```
- 탐색 탭에서 15초마다 자동 새로고침
- 페이지 가시성 변화에 따른 제어

**API 통신 관련:**
```javascript
async function getPersonImages(personId)
async function findRecentPeople(startId = 1, maxCheck = 50, maxResults = 5)
```
- Person ID로 이미지 조회 API 호출
- 여러 Person ID를 순차적으로 조회하여 최근 감지된 사람들 검색

**UI 업데이트 관련:**
```javascript
async function displayRecentPeopleInExploreTab()
async function showPersonDetails(personId)
```
- 탐색 탭에 실제 감지된 사람들의 이미지 표시
- Person 클릭시 상세 정보를 팝업창으로 표시

**이벤트 리스너 추가:**
- `window.addEventListener('beforeunload', ...)` - 페이지 종료시 자동 업데이트 정리
- `document.addEventListener('visibilitychange', ...)` - 페이지 숨김/표시시 자동 업데이트 제어

**기존 함수 수정:**
```javascript
function showSection(sectionName)
```
- 탐색 탭 활성화시 자동 업데이트 시작
- 다른 탭 이동시 자동 업데이트 중지

### 3. 카메라 연결 안정성 개선

#### `pic_tag/camera_worker/cropper/cam_cropper.py`
**수정된 함수:** `capture_frames()`
**추가된 내용:**
- RTSP 연결 타임아웃 설정 (10초)
- 읽기 타임아웃 설정 (10초)
- 더 정확한 에러 메시지 출력

**변경 코드:**
```python
cap = cv2.VideoCapture(cam_num)
cap.set(cv2.CAP_PROP_OPEN_TIMEOUT_MSEC, 10000)  # 10초 타임아웃
cap.set(cv2.CAP_PROP_READ_TIMEOUT_MSEC, 10000)  # 읽기 타임아웃
```

#### `pic_tag/camera_worker/camera_manager.py`
**수정된 함수:** `start_all_cameras()`
**추가된 내용:**
- RTSP URL 연결 시도시 디버그 로그 출력

**변경 코드:**
```python
print(f"Attempting to connect to: {rtsp_url}")
```

### 4. 기타 수정 사항

#### `backend/db_statistics/views.py`
- 코드 포맷팅 정리 (기능 변경 없음)

#### `backend/requirements.txt`
- 새로운 패키지 의존성 추가

#### `backend/backend/settings.py`
- Django 설정 변경

#### `pic_tag/main.py`
- 비디오 처리 관련 인덱스 수정

## 새로 생성된 파일들

1. `backend/__init__.py` - Python 패키지 초기화 파일
2. `backend/db_statistics/identity_analytics.py` - 신원 분석 관련 모듈
3. `backend/run_server.py` - 서버 실행 스크립트
4. `test_person_images.html` - 이미지 테스트용 HTML 파일

## 주요 기능 요약

### 1. 실시간 Person 이미지 조회
- DB에서 실제 감지된 사람의 이미지를 실시간으로 표시
- Base64 인코딩을 통한 이미지 전송

### 2. 탐색 탭 자동 업데이트
- 15초마다 최근 감지된 사람들 자동 갱신
- DB 연결 상태 확인 및 에러 처리

### 3. 상세 이미지 팝업
- Person ID 클릭시 해당 사람의 모든 감지 이미지 표시
- 새 창으로 타임스탬프, 카메라 정보와 함께 표시

### 4. RTSP 연결 안정성
- 타임아웃 설정으로 빠른 연결 실패 감지
- 30초 대신 10초로 단축하여 사용자 경험 개선

### 5. 에러 처리 강화
- DB 미연결시 기본 UI 유지
- API 호출 실패시 적절한 대체 동작

## 기술적 개선사항

1. **비동기 처리**: JavaScript async/await 패턴 사용
2. **에러 핸들링**: try-catch 블록으로 안정성 향상
3. **성능 최적화**: API 호출 간격 조절 (100ms)
4. **메모리 관리**: 자동 업데이트 정리 로직 추가
5. **사용자 경험**: 로딩 상태 표시 및 연결 상태 피드백

## 테스트 권장 사항

1. DB 연결 상태에서의 탐색 탭 동작 확인
2. DB 미연결 상태에서의 UI 유지 확인
3. Person ID 클릭시 상세 팝업 동작 확인
4. 자동 업데이트 시작/중지 동작 확인
5. RTSP 카메라 연결 타임아웃 동작 확인
