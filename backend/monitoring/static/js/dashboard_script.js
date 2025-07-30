// 전역 변수에 현재 위치 정보 저장
let currentLocation = '';
let locationName = '';
let userLocations = {}; // 사용자별 위치 정보 저장
let streamSocket = null;
let exploreAutoUpdateInterval = null;

const MAIN_CAMERA_INTERVAL = 100; // ms (2 FPS)
let lastMainFrameTime = 0;
// 사용자 위치 정보 관리 함수
function getUserLocationById(userId) {
    return userLocations[userId]?.location || 'unknown';
}

function getLocationNameById(userId) {
    return userLocations[userId]?.locationName || '알 수 없음';
}

function setUserLocation(userId, location, locationName) {
    userLocations[userId] = { location, locationName };
}

// 로그인 처리
document.getElementById('loginForm').addEventListener('submit', function (e) {
    e.preventDefault();

    const username = document.getElementById('username').value;
    const password = document.getElementById('password').value;
    const location = document.getElementById('location').value;

    // 통합 관리 계정 (모든 CCTV 볼 수 있음)
    if (username === 'admin' && password === 'admin123') {
        currentLocation = 'admin';
        locationName = '통합 관리자';
        showDashboard();
        return;
    }

    // 위치별 로그인 계정
    const validLogins = {
        'entrance': { username: 'entrance', password: 'entrance123', name: '현관 입구' },
        'parking': { username: 'parking', password: 'parking123', name: '주차장' },
        'hallway': { username: 'hallway', password: 'hallway123', name: '복도' },
        'emergency': { username: 'emergency', password: 'emergency123', name: '비상구' }
    };

    if (location && validLogins[location] &&
        username === validLogins[location].username &&
        password === validLogins[location].password) {

        currentLocation = location;
        locationName = validLogins[location].name;
        showDashboard();
    } else {
        alert('잘못된 로그인 정보이거나 위치가 선택되지 않았습니다.');
    }
});

// 로그아웃
function logout() {
    document.getElementById('loginPage').style.display = 'flex';
    document.getElementById('dashboardPage').style.display = 'none';
    document.getElementById('username').value = '';
    document.getElementById('password').value = '';
    document.getElementById('location').value = '';

    // 웹캠 중지
    closeAllCameraSockets() 
    // WebSocket 연결 종료
    if (socket) {
        socket.close();
    }
}

// 섹션 표시
function showSection(sectionName) {
    const sections = document.querySelectorAll('.section');
    sections.forEach(section => section.classList.add('hidden'));

    document.getElementById(sectionName).classList.remove('hidden');

    const menuItems = document.querySelectorAll('.menu-item');
    menuItems.forEach(item => item.classList.remove('active'));
    event.target.classList.add('active');

    // 통계 페이지 초기화
    if (sectionName === 'statistics') {
        stopExploreAutoUpdate(); // 다른 섹션으로 이동시 탐색 자동 업데이트 중지
        setTimeout(() => {
            initializeCharts();
            updateLogTable();
            updateTrackingGrid();
            refreshLogs();
        }, 100);
    }
    
    // 탐색 페이지 초기화 및 자동 업데이트 시작 (일시적으로 비활성화)
    if (sectionName === 'detection') {
        // setTimeout(() => {
        //     startExploreAutoUpdate(15); // 15초마다 자동 업데이트
        // }, 100);
    } else {
        stopExploreAutoUpdate(); // 탐색 탭이 아닌 경우 자동 업데이트 중지
    }
}

// 탐색 탭 자동 업데이트 시작
function startExploreAutoUpdate(intervalSeconds = 15) {
    // 기존 자동 업데이트가 있다면 중지
    stopExploreAutoUpdate();
    
    // 즉시 한 번 실행
    displayRecentPeopleInExploreTab();
    
    // 주기적 실행
    exploreAutoUpdateInterval = setInterval(() => {
        displayRecentPeopleInExploreTab();
    }, intervalSeconds * 1000);
}

// 탐색 탭 자동 업데이트 중지
function stopExploreAutoUpdate() {
    if (exploreAutoUpdateInterval) {
        clearInterval(exploreAutoUpdateInterval);
        exploreAutoUpdateInterval = null;
    }
}

// 영상 재생/일시정지
function playPause() {
    const btn = event.target;
    if (btn.textContent === '▶') {
        btn.textContent = '⏸';
    } else {
        btn.textContent = '▶';
    }
}

// 타임라인 시크
function seekVideo(event) {
    const timeline = event.currentTarget;
    const rect = timeline.getBoundingClientRect();
    const clickX = event.clientX - rect.left;
    const percentage = (clickX / rect.width) * 100;

    const progress = timeline.querySelector('.timeline-progress');
    const marker = timeline.querySelector('.timeline-marker');

    progress.style.width = percentage + '%';
    marker.style.left = percentage + '%';
}

// 로그 엔트리 강조
function highlightLogEntry(timestamp) {
    const logEntries = document.querySelectorAll('.log-entry');
    logEntries.forEach(entry => {
        const timeElement = entry.querySelector('.log-time');
        if (timeElement && timeElement.textContent === timestamp) {
            entry.style.background = '#f0f0ff';
            entry.style.borderLeft = '3px solid #1a237e';
        } else {
            entry.style.background = '';
            entry.style.borderLeft = '';
        }
    });
}

// iOS 스타일 토글
function toggleSetting(element) {
    element.classList.toggle('active');
}

// 테마 전환 함수
function switchTheme(theme) {
    window.location.href = `/?theme=${theme}`;
}


// WebRTC 관련 변수
let socket = null;
let peerConnections = {};
let remoteStreams = {};
let myUserId = null;

// STUN 서버 설정
const iceServers = {
    iceServers: [
        { urls: 'stun:stun.l.google.com:19302' },
        { urls: 'stun:stun1.l.google.com:19302' }
    ]
};





function closeAllCameraSockets() {
    for (const socket of Object.values(cameraSockets)) {
        socket.close();
    }
}



// 실시간 시간 업데이트
function updateTime() {
    const now = new Date();
    const timeString = now.toLocaleTimeString('ko-KR', { hour12: false });
    const timeDisplay = document.getElementById('timeDisplay');
    if (timeDisplay) {
        timeDisplay.textContent = timeString;
    }
}



// 새로운 로그 엔트리 추가
function addNewLogEntry() {
    const logTable = document.querySelector('.log-table tbody');
    if (logTable && Math.random() < 0.05) { // 5% 확률로 새 로그 추가
        const now = new Date();
        const timeString = now.toLocaleTimeString('ko-KR', { hour12: false });
        const types = ['입장', '퇴장'];
        const locations = ['현관 입구', '비상구', '주차장 입구'];
        const type = types[Math.floor(Math.random() * types.length)];
        const location = locations[Math.floor(Math.random() * locations.length)];

        const newRow = document.createElement('tr');
        newRow.innerHTML = `
                    <td>${timeString}</td>
                    <td>${type}</td>
                    <td>${location}</td>
                    <td>${type === '입장' ? '-' : Math.floor(Math.random() * 120) + '분'}</td>
                    <td>${type === '입장' ? '진행중' : '완료'}</td>
                `;

        logTable.insertBefore(newRow, logTable.firstChild);

        // 최대 10개 로그만 유지
        const rows = logTable.querySelectorAll('tr');
        if (rows.length > 10) {
            logTable.removeChild(rows[rows.length - 1]);
        }
    }
}

// 감지 로그 업데이트
function updateDetectionLog() {
    const detectionLog = document.querySelector('.detection-log');
    if (detectionLog && Math.random() < 0.1) { // 10% 확률로 새 감지 로그 추가
        const now = new Date();
        const timeString = now.toLocaleTimeString('ko-KR', { hour12: false });
        const actions = [
            '인원 감지 - 현관 입구 진입',
            '인원 감지 - 주차장 이동',
            '인원 감지 - 복도 통과',
            '인원 감지 - 비상구 접근',
            '인원 감지 - 대기 중'
        ];
        const action = actions[Math.floor(Math.random() * actions.length)];

        const newEntry = document.createElement('div');
        newEntry.className = 'log-entry';
        newEntry.innerHTML = `
                    <div class="log-time">${timeString}</div>
                    <div class="log-action">${action}</div>
                `;

        const logContainer = detectionLog.querySelector('h3').nextSibling;
        detectionLog.insertBefore(newEntry, logContainer.nextSibling);

        // 최대 15개 로그만 유지
        const entries = detectionLog.querySelectorAll('.log-entry');
        if (entries.length > 15) {
            detectionLog.removeChild(entries[entries.length - 1]);
        }
    }
}

// 자동 재생 시뮬레이션
function simulatePlayback() {
    const progress = document.querySelector('.timeline-progress');
    const marker = document.querySelector('.timeline-marker');

    if (progress && marker) {
        let currentWidth = parseInt(progress.style.width) || 30;
        if (currentWidth < 90) {
            currentWidth += 0.5;
            progress.style.width = currentWidth + '%';
            marker.style.left = currentWidth + '%';
        } else {
            progress.style.width = '0%';
            marker.style.left = '0%';
        }
    }
}

// 모든 업데이트 함수들을 정기적으로 실행
setInterval(updateTime, 1000);          // 1초마다 시간 업데이트

setInterval(addNewLogEntry, 15000);     // 15초마다 새 로그 확인
setInterval(updateDetectionLog, 8000);  // 8초마다 감지 로그 업데이트
setInterval(simulatePlayback, 2000);    // 2초마다 재생 시뮬레이션

// 초기 설정
document.addEventListener('DOMContentLoaded', function () {
    document.getElementById('loginPage').style.display = 'flex';
    document.getElementById('dashboardPage').style.display = 'none';
    updateTime();
});

function initWebSocket(cameraId = "camera1") {
    const protocol = window.location.protocol === 'https:' ? 'wss:' : 'ws:';
    const wsUrl = `${protocol}//${window.location.host}/ws/camera/${cameraId}/`;

    if (socket) {
        socket.close();  // 이전 소켓 정리
    }

    socket = new WebSocket(wsUrl);

    socket.onopen = function () {
        console.log(`📡 WebSocket 연결됨: ${cameraId}`);
        // 위치 정보를 서버에 보낼 필요가 없는 경우 생략 가능
    };

    socket.onmessage = function (event) {
        const base64 = event.data;
        const mainVideo = document.getElementById("mainCameraImage");
        const placeholder = document.getElementById("mainVideoPlaceholder");

        const img = new Image();
        img.onload = function () {
            const canvas = document.createElement("canvas");
            canvas.width = img.width;
            canvas.height = img.height;
            const ctx = canvas.getContext("2d");
            ctx.drawImage(img, 0, 0);
            const dataURL = canvas.toDataURL("image/jpeg");

            mainVideo.src = dataURL;
            mainVideo.style.display = "block";
            if (placeholder) placeholder.style.display = "none";
        };
        img.src = "data:image/jpeg;base64," + base64;
    };

    socket.onclose = function () {
        console.log(`⚠️ WebSocket 종료됨: ${cameraId}`);
        setTimeout(() => {
            if (document.getElementById('dashboardPage').style.display !== 'none') {
                initWebSocket(cameraId);  // 자동 재연결
            }
        }, 3000);
    };

    socket.onerror = function (error) {
        console.error(`❌ WebSocket 오류 (${cameraId}):`, error);
    };
}




// Offer 처리
async function handleOffer(data) {
    try {
        console.log('Offer 받음:', data.from_user);
        const peerConnection = new RTCPeerConnection(iceServers);
        peerConnections[data.from_user] = peerConnection;

        // ICE Candidate 이벤트
        peerConnection.onicecandidate = function (event) {
            if (event.candidate) {
                socket.send(JSON.stringify({
                    type: 'ice_candidate',
                    candidate: event.candidate,
                    to_user: data.from_user
                }));
            }
        };

        // Remote Stream 이벤트
        peerConnection.ontrack = function (event) {
            console.log('Remote stream 받음 (Offer 응답):', data.from_user);
            remoteStreams[data.from_user] = event.streams[0];
            // 위치 정보는 별도로 관리되어야 함
            const userLocation = getUserLocationById(data.from_user);
            const locationName = getLocationNameById(data.from_user);
            displayRemoteStream(data.from_user, event.streams[0], userLocation, locationName);
        };

        // 내 스트림 추가 (위치 기반 사용자만)


        // Offer 설정 및 Answer 생성
        await peerConnection.setRemoteDescription(data.offer);
        const answer = await peerConnection.createAnswer();
        await peerConnection.setLocalDescription(answer);

        socket.send(JSON.stringify({
            type: 'answer',
            answer: answer,
            to_user: data.from_user
        }));

    } catch (error) {
        console.error('Offer 처리 오류:', error);
    }
}

// Answer 처리
async function handleAnswer(data) {
    try {
        const peerConnection = peerConnections[data.from_user];
        if (peerConnection) {
            await peerConnection.setRemoteDescription(data.answer);
        }
    } catch (error) {
        console.error('Answer 처리 오류:', error);
    }
}

// ICE Candidate 처리
async function handleIceCandidate(data) {
    try {
        const peerConnection = peerConnections[data.from_user];
        if (peerConnection) {
            await peerConnection.addIceCandidate(data.candidate);
        }
    } catch (error) {
        console.error('ICE Candidate 처리 오류:', error);
    }
}



function showDashboard() {
    document.getElementById('loginPage').style.display = 'none';
    document.getElementById('dashboardPage').style.display = 'block';



    // 사용자 정보 업데이트
    const userInfo = document.querySelector('.user-info span');
    if (userInfo) {
        userInfo.textContent = locationName || '관리자';
    }


}

// === 통계 데이터 및 차트 ===

// identity_log 테이블 구조를 기반으로 한 하드코딩 데이터
const identityLogs = [
    { id: 1, timestamp: '2025-01-25 14:32:15', person_id: 1001, embedding: '[0.1,0.2,...]', file_path: '/captures/img_001.jpg', camera_id: 1, bb_x1: 120, bb_y1: 80, bb_x2: 220, bb_y2: 280 },
    { id: 2, timestamp: '2025-01-25 14:31:45', person_id: 1002, embedding: '[0.3,0.4,...]', file_path: '/captures/img_002.jpg', camera_id: 2, bb_x1: 150, bb_y1: 90, bb_x2: 250, bb_y2: 290 },
    { id: 3, timestamp: '2025-01-25 14:30:20', person_id: 1001, embedding: '[0.1,0.2,...]', file_path: '/captures/img_003.jpg', camera_id: 3, bb_x1: 110, bb_y1: 75, bb_x2: 210, bb_y2: 275 },
    { id: 4, timestamp: '2025-01-25 14:29:55', person_id: 1003, embedding: '[0.5,0.6,...]', file_path: '/captures/img_004.jpg', camera_id: 1, bb_x1: 130, bb_y1: 85, bb_x2: 230, bb_y2: 285 },
    { id: 5, timestamp: '2025-01-25 14:28:30', person_id: 1004, embedding: '[0.7,0.8,...]', file_path: '/captures/img_005.jpg', camera_id: 4, bb_x1: 140, bb_y1: 95, bb_x2: 240, bb_y2: 295 },
    { id: 6, timestamp: '2025-01-25 14:27:10', person_id: 1002, embedding: '[0.3,0.4,...]', file_path: '/captures/img_006.jpg', camera_id: 2, bb_x1: 155, bb_y1: 92, bb_x2: 255, bb_y2: 292 },
    { id: 7, timestamp: '2025-01-25 14:25:45', person_id: 1005, embedding: '[0.9,1.0,...]', file_path: '/captures/img_007.jpg', camera_id: 1, bb_x1: 125, bb_y1: 82, bb_x2: 225, bb_y2: 282 },
    { id: 8, timestamp: '2025-01-25 14:24:20', person_id: 1001, embedding: '[0.1,0.2,...]', file_path: '/captures/img_008.jpg', camera_id: 3, bb_x1: 115, bb_y1: 78, bb_x2: 215, bb_y2: 278 },
    { id: 9, timestamp: '2025-01-25 14:22:55', person_id: 1006, embedding: '[1.1,1.2,...]', file_path: '/captures/img_009.jpg', camera_id: 2, bb_x1: 160, bb_y1: 88, bb_x2: 260, bb_y2: 288 },
    { id: 10, timestamp: '2025-01-25 14:21:30', person_id: 1003, embedding: '[0.5,0.6,...]', file_path: '/captures/img_010.jpg', camera_id: 4, bb_x1: 135, bb_y1: 87, bb_x2: 235, bb_y2: 287 }
];

const cameraNames = {
    1: '현관 입구',
    2: '주차장',
    3: '복도',
    4: '비상구'
};


const cameraMap = {
    entrance: "camera1",
    parking: "camera2",
    hallway: "camera3",
    emergency: "camera4"
};

const cameraSockets = {};

let charts = {};

// 차트 초기화
function initializeCharts() {
    // 기존 차트가 있으면 제거
    Object.keys(charts).forEach(key => {
        if (charts[key]) {
            charts[key].destroy();
        }
    });
    charts = {};

    // 시간대별 감지 현황 차트
    const hourlyCtx = document.getElementById('hourlyChart');
    if (hourlyCtx) {
        charts.hourly = new Chart(hourlyCtx.getContext('2d'), {
            type: 'line',
            data: {
                labels: ['00:00', '04:00', '08:00', '12:00', '16:00', '20:00'],
                datasets: [{
                    label: '감지 수',
                    data: [2, 1, 15, 32, 28, 12],
                    borderColor: '#1a237e',
                    backgroundColor: 'rgba(26, 35, 126, 0.1)',
                    fill: true,
                    tension: 0.4
                }]
            },
            options: {
                responsive: true,
                maintainAspectRatio: false,
                scales: {
                    y: {
                        beginAtZero: true
                    }
                }
            }
        });
    }

    // 카메라별 감지 분포 차트
    const cameraCtx = document.getElementById('cameraChart');
    if (cameraCtx) {
        const cameraData = getCameraDistribution();
        charts.camera = new Chart(cameraCtx.getContext('2d'), {
            type: 'doughnut',
            data: {
                labels: Object.values(cameraNames),
                datasets: [{
                    data: cameraData,
                    backgroundColor: ['#1a237e', '#3f51b5', '#7986cb', '#c5cae9']
                }]
            },
            options: {
                responsive: true,
                maintainAspectRatio: false
            }
        });
    }

    // 주간 감지 추이 차트
    const weeklyCtx = document.getElementById('weeklyChart');
    if (weeklyCtx) {
        charts.weekly = new Chart(weeklyCtx.getContext('2d'), {
            type: 'bar',
            data: {
                labels: ['월', '화', '수', '목', '금', '토', '일'],
                datasets: [{
                    label: '일별 감지 수',
                    data: [45, 52, 38, 67, 73, 28, 15],
                    backgroundColor: '#1a237e'
                }]
            },
            options: {
                responsive: true,
                maintainAspectRatio: false,
                scales: {
                    y: {
                        beginAtZero: true
                    }
                }
            }
        });
    }

    // 신뢰도 분포 차트
    const confidenceCtx = document.getElementById('confidenceChart');
    if (confidenceCtx) {
        charts.confidence = new Chart(confidenceCtx.getContext('2d'), {
            type: 'bar',
            data: {
                labels: ['90-95%', '95-98%', '98-99%', '99-100%'],
                datasets: [{
                    label: '감지 건수',
                    data: [12, 35, 67, 28],
                    backgroundColor: ['#ff6b6b', '#feca57', '#48dbfb', '#0abde3']
                }]
            },
            options: {
                responsive: true,
                maintainAspectRatio: false,
                scales: {
                    y: {
                        beginAtZero: true
                    }
                }
            }
        });
    }
}

// 카메라별 감지 분포 계산
function getCameraDistribution() {
    const distribution = [0, 0, 0, 0];
    identityLogs.forEach(log => {
        if (log.camera_id >= 1 && log.camera_id <= 4) {
            distribution[log.camera_id - 1]++;
        }
    });
    return distribution;
}

// 로그 테이블 업데이트
function updateLogTable(filterCamera = 'all') {
    const tbody = document.getElementById('logTableBody');
    tbody.innerHTML = '';

    let filteredLogs = identityLogs;
    if (filterCamera !== 'all') {
        const cameraId = getCameraIdByLocation(filterCamera);
        filteredLogs = identityLogs.filter(log => log.camera_id === cameraId);
    }

    filteredLogs.slice(0, 20).forEach(log => {
        const row = document.createElement('tr');
        const confidence = (Math.random() * 10 + 90).toFixed(1); // 90-100% 랜덤 신뢰도
        const status = Math.random() > 0.8 ? 'error' : 'success';

        row.innerHTML = `
                    <td>${formatTimestamp(log.timestamp)}</td>
                    <td>Person-${log.person_id}</td>
                    <td>CAM-${log.camera_id}</td>
                    <td>${cameraNames[log.camera_id]}</td>
                    <td>${confidence}%</td>
                    <td><span class="status ${status}">${status === 'success' ? '정상' : '오류'}</span></td>
                `;
        tbody.appendChild(row);
    });
}

// 인원 추적 현황 업데이트
function updateTrackingGrid() {
    const grid = document.getElementById('trackingGrid');
    grid.innerHTML = '';

    const uniquePersons = [...new Set(identityLogs.map(log => log.person_id))];

    uniquePersons.forEach(personId => {
        const personLogs = identityLogs.filter(log => log.person_id === personId);
        const latestLog = personLogs[0];
        const isActive = Math.random() > 0.5;

        const card = document.createElement('div');
        card.className = 'person-card';
        card.innerHTML = `
                    <div class="person-id">Person-${personId}</div>
                    <div class="person-info">마지막 감지: ${formatTimestamp(latestLog.timestamp)}</div>
                    <div class="person-info">위치: ${cameraNames[latestLog.camera_id]}</div>
                    <div class="person-info">감지 횟수: ${personLogs.length}회</div>
                    <div class="person-status ${isActive ? 'active' : 'inactive'}">
                        ${isActive ? '활성' : '비활성'}
                    </div>
                `;
        grid.appendChild(card);
    });
}

// 유틸리티 함수들
function formatTimestamp(timestamp) {
    return new Date(timestamp).toLocaleTimeString('ko-KR');
}

function getCameraIdByLocation(location) {
    const locationMap = {
        'entrance': 1,
        'parking': 2,
        'hallway': 3,
        'emergency': 4
    };
    return locationMap[location] || 1;
}

// 로그 새로고침
function refreshLogs() {
    const filter = document.getElementById('logFilter').value;
    updateLogTable(filter);
    updateTrackingGrid();

    // 통계 카드 업데이트
    document.getElementById('todayDetections').textContent = identityLogs.length;
    document.getElementById('uniquePersons').textContent = [...new Set(identityLogs.map(log => log.person_id))].length;
    document.getElementById('activeCameras').textContent = [...new Set(identityLogs.map(log => log.camera_id))].length;
    document.getElementById('avgConfidence').textContent = '94.2%';
}

// 로그 필터 이벤트
document.addEventListener('DOMContentLoaded', function () {
    const logFilter = document.getElementById('logFilter');
    if (logFilter) {
        logFilter.addEventListener('change', function () {
            updateLogTable(this.value);
        });
    }
});




// CAMERA STREAM

let mainSocket = null;
let thumbSockets = {};
let currentMainCamera = null;


// Connect thumb previews for all cameras
function connectThumbCameras() {
    const cameraIds = ['camera1', 'camera2', 'camera3', 'camera4'];

    cameraIds.forEach((cameraId) => {
        const protocol = window.location.protocol === 'https:' ? 'wss:' : 'ws:';
        const wsUrl = `${protocol}//${window.location.host}/ws/camera/${cameraId}/?thumb=1`;

        const socket = new WebSocket(wsUrl);
        thumbSockets[cameraId] = socket;

        socket.onmessage = (event) => {
            const thumbId = `thumb-${cameraId}`;
            const thumbEl = document.getElementById(thumbId);
            if (thumbEl && event.data.startsWith("/9j")) {  // Base64 JPEG
                thumbEl.innerHTML = `<img src="data:image/jpeg;base64,${event.data}" style="width: 100%; height: 100%; object-fit: cover;">`;
            }
        };
    });
}



function stopMainCamera() {
    if (mainSocket) {
        mainSocket.close();
        mainSocket = null;
    }
    const videoEl = document.getElementById("mainCamera");
    videoEl.src = "";
    videoEl.style.display = "none";
    document.getElementById("mainVideoPlaceholder").style.display = "block";
}

function selectCamera(element, location, camId) {
    const thumbs = document.querySelectorAll('.camera-thumb');
    thumbs.forEach(thumb => thumb.classList.remove('active'));
    element.classList.add('active');

    const videoInfo = document.querySelector('.video-info');
    videoInfo.textContent = `${location} - ${camId}`;

    const mainVideo = document.getElementById('mainCamera');
    const placeholder = document.getElementById('mainVideoPlaceholder');

    // Close previous WebSocket if any
    if (mainSocket) {
        mainSocket.close();
        mainSocket = null;
    }

    const protocol = window.location.protocol === 'https:' ? 'wss:' : 'ws:';
    const wsUrl = `${protocol}//${window.location.host}/ws/camera/${camId}/`;  // No thumb=1 → high-res

    mainSocket = new WebSocket(wsUrl);

    mainSocket.onmessage = (event) => {
        const img = new Image();
        img.onload = function () {
            const canvas = document.createElement("canvas");
            canvas.width = img.width;
            canvas.height = img.height;
            const ctx = canvas.getContext("2d");
            ctx.drawImage(img, 0, 0);
            mainVideo.src = canvas.toDataURL("image/jpeg");
            mainVideo.style.display = "block";
            placeholder.style.display = "none";
        };
        img.src = "data:image/jpeg;base64," + event.data;
    };

    mainSocket.onopen = () => {
        console.log(`✅ WebSocket opened for main camera: ${camId}`);
    };

    mainSocket.onerror = (err) => {
        console.error("❌ Main WebSocket error:", err);
        placeholder.innerText = "WebSocket error";
        placeholder.style.display = "block";
    };

    mainSocket.onclose = () => {
        console.log(`⚠️ WebSocket closed for main camera: ${camId}`);
        placeholder.style.display = "block";
        mainVideo.style.display = "none";
    };
}

mainCamera.onload = () => {
    console.log("Image size:",mainCamera.naturalWidth,mainCamera.naturalHeight);
}




// DOM 로딩이 끝나면 실행되는 코드. 처음 시작되는 코드.

window.addEventListener('DOMContentLoaded', () => {
    connectThumbCameras();

        // 👇 Auto-select default camera (e.g., 'camera1')
    const defaultCameraId = 'camera1';
    const defaultLocation = '현관 입구';  // Or actual location if known
    const defaultElement = document.getElementById(`thumb-${defaultCameraId}`);

    if (defaultElement) {
        selectCamera(defaultElement, defaultLocation, defaultCameraId);
    }
});

// function startStreamSocket(camId) {
//     if (streamSocket) {
//         streamSocket.close();
//     }

//     const protocol = window.location.protocol === 'https:' ? 'wss:' : 'ws:';
//     const url = `${protocol}//${window.location.host}/ws/camera/${camId}/`;
//     streamSocket = new WebSocket(url);

//     const mainVideo = document.getElementById("mainCamera");
//     const placeholder = document.getElementById("mainVideoPlaceholder");

//     streamSocket.onopen = () => {
//         console.log("✅ RTSP WebSocket connected:", camId);
//         mainVideo.style.display = "block";
//         placeholder.style.display = "none";
//     };

//     streamSocket.onmessage = (event) => {
//         const img = new Image();
//         img.onload = function () {
//             const canvas = document.createElement("canvas");
//             canvas.width = img.width;
//             canvas.height = img.height;
//             const ctx = canvas.getContext("2d");
//             ctx.drawImage(img, 0, 0);
//             mainVideo.src = canvas.toDataURL("image/jpeg");
//         };
//         img.src = "data:image/jpeg;base64," + event.data;
//     };

//     streamSocket.onerror = (err) => {
//         console.error("❌ WebSocket error:", err);
//     };

//     streamSocket.onclose = () => {
//         console.log("⚠️ WebSocket closed");
//         placeholder.style.display = "block";
//         placeholder.innerHTML = "카메라 연결 종료";
//     };
// }

// 예시: 전체 동영상 목록 (실제 데이터는 서버에서 받아올 수도 있음)
const allVideos = [
    {
        file: 'video1.mp4',
        thumbnail: '/static/images/video1_thumbnail.jpg',
        title: '현관 입구 - 2023-10-01'
    },
    {
        file: 'video2.mp4',
        thumbnail: '/static/images/video2_thumbnail.jpg',
        title: '주차장 - 2023-10-01'
    },
    {
        file: 'video3.mp4',
        thumbnail: '/static/images/video3_thumbnail.jpg',
        title: '복도 - 2023-10-01'
    },
    {
        file: 'video4.mp4',
        thumbnail: '/static/images/video4_thumbnail.jpg',
        title: '복도 - 2023-10-01'
    }
];

// 동영상 목록 렌더링 함수
function renderVideoList(videos) {
    const videoList = document.getElementById('videoList');
    videoList.innerHTML = '';
    if (videos.length === 0) {
        videoList.innerHTML = '<div style="padding:20px;text-align:center;">검색 결과가 없습니다.</div>';
        return;
    }
    videos.forEach(video => {
        const item = document.createElement('div');
        item.className = 'video-item';
        item.onclick = () => playVideo(video.file);
        item.innerHTML = `
            <div class="video-thumbnail" style="background-image: url('${video.thumbnail}');"></div>
            <div class="video-title">${video.title}</div>
        `;
        videoList.appendChild(item);
    });
}

// 검색 함수
function searchVideos() {
    const keyword = document.getElementById('videoSearchInput').value.trim();
    const filtered = allVideos.filter(v =>
        v.title.includes(keyword) || v.title.replace(/-/g, '').includes(keyword)
    );
    renderVideoList(filtered);
}

// 페이지 진입 시 전체 목록 표시
document.addEventListener('DOMContentLoaded', function() {
    renderVideoList(allVideos);
});

function playVideo(file) {
    const videoPlayer = document.getElementById('videoPlayer');
    const videoSource = document.getElementById('videoSource');
    const placeholder = document.getElementById('videoPlaceholder');
    if (!videoPlayer || !videoSource) return;

    // 파일 경로 지정 (실제 환경에 맞게 경로 수정)
    videoSource.src = '/static/videos/' + file;
    videoPlayer.load();
    videoPlayer.style.display = 'block';
    if (placeholder) placeholder.style.display = 'none';
}



// fetch stat data every 1 second.
async function fetchStatsAndUpdate() {
    try {
        const response = await fetch('/sync/page/');
        if (!response.ok) throw new Error("API error");

        const data = await response.json();

        // --- Numerical stats ---
        const currentOnCCTV = data.current_on_CCTV || 0;
        const last24People = data.last_24_people || 0;
        const stayCount = data.current_people?.stay_count || 0;
        const goneCount = data.current_people?.gone_count || 0;

        const currentTotal = stayCount + goneCount;
        const percentage = currentTotal > 0 ? ((currentOnCCTV / currentTotal) * 100).toFixed(1) + "%" : "0%";

        const elLast24 = document.getElementById('last_24_hrs_people');
        const elStay = document.getElementById('people_stay_count');
        const elGone = document.getElementById('people_gone_count');
        const elCurrentPct = document.getElementById('current_people_on_camera');

        if (elLast24) elLast24.textContent = last24People;
        if (elStay) elStay.textContent = stayCount;
        if (elGone) elGone.textContent = goneCount;
        if (elCurrentPct) elCurrentPct.textContent = percentage;

        // --- Recent 5 person list ---
        const cropGrid = document.querySelector('.crop-grid');
        if (cropGrid) {
            cropGrid.innerHTML = ''; // Clear previous list

            const recentList = data.recent_5_list || [];
            recentList.forEach(personIdRaw => {
                const personId = parseInt(personIdRaw);
                if (isNaN(personId)) return;

                const cropItem = document.createElement('div');
                cropItem.className = 'crop-item';
                cropItem.textContent = `Person ${personId}`;
                cropItem.dataset.personId = personId;
                cropItem.onclick = () => selectCrop(cropItem, personId);

                cropGrid.appendChild(cropItem);
            });
        }

    } catch (error) {
        console.error("❌ Failed to fetch stats:", error);
    }
}
// Initial call
fetchStatsAndUpdate();
setInterval(fetchStatsAndUpdate, 10000);




//Select crop will change logs on the right.
function selectCrop(elem, personId) {
    fetch(`/sync/get_by_id/${personId}/`)
        .then(response => {
            if (!response.ok) throw new Error("Failed to fetch person detail");
            return response.json();
        })
        .then(data => {
            const logContainer = document.querySelector('.detection-log');

            // Clear old logs except the title
            logContainer.innerHTML = '<h3 style="margin-bottom: 15px;">감지 로그</h3>';

            const actions = data.recent_actions || [];

            actions.forEach(entry => {
                const time = entry.timestamp || '';
                const cam = camNumberToLabel(entry.cam_num);
                const bbox = entry.bounding_box || [];

                const logEntry = document.createElement('div');
                logEntry.className = 'log-entry';

                const timeDiv = document.createElement('div');
                timeDiv.className = 'log-time';
                timeDiv.textContent = formatTime(time);

                const actionDiv = document.createElement('div');
                actionDiv.className = 'log-action';
                actionDiv.textContent = `인원 감지 - ${cam}`;

                logEntry.appendChild(timeDiv);
                logEntry.appendChild(actionDiv);

                logContainer.appendChild(logEntry);
            });
        })
        .catch(error => {
            console.error("Error in selectCrop:", error);
        });
}



function formatTime(timestamp) {
    try {
        const date = new Date(timestamp);
        return date.toTimeString().slice(0, 8);
    } catch (e) {
        return timestamp;
    }
}

// Translate camera number to description (customize these as needed)
function camNumberToLabel(camNum) {
    switch (camNum) {
        case 1: return '현관 입구 진입';
        case 2: return '현관 입구 대기';
        case 3: return '현관 입구 접근';
        case 4: return '주차장에서 이동';
        case 5: return '주차장 진입';
        default: return `CAM${camNum}`;
    }
}

// Person ID로 이미지 조회하는 함수
async function getPersonImages(personId) {
    try {
        const response = await fetch(`/sync/get_by_id/${personId}/`);
        const data = await response.json();
        
        if (data.status === 'success' && data.images && data.images.length > 0) {
            return data.images;
        } else {
            return [];
        }
        
    } catch (error) {
        console.error('이미지 조회 실패:', error);
        return null;
    }
}

// 여러 Person ID를 순차적으로 조회하여 최근 감지된 사람들 찾기
async function findRecentPeople(startId = 1, maxCheck = 50, maxResults = 5) {
    const foundPeople = [];
    
    for (let personId = startId; personId <= startId + maxCheck - 1; personId++) {
        const images = await getPersonImages(personId);
        
        if (images && images.length > 0) {
            foundPeople.push({
                person_id: personId,
                images: images,
                image_count: images.length
            });
            
            if (foundPeople.length >= maxResults) {
                break;
            }
        }
        
        // API 부하 방지
        await new Promise(resolve => setTimeout(resolve, 100));
    }
    
    return foundPeople;
}

// 탐색 탭에 최근 감지된 사람들 표시
async function displayRecentPeopleInExploreTab() {
    // 원본 구조의 crop-item 클래스 사용
    const cropItems = document.querySelectorAll('.crop-grid .crop-item');
    
    // DB 연결 여부를 먼저 확인
    try {
        // 간단한 API 연결 테스트
        const testResponse = await fetch('/sync/page/');
        if (!testResponse.ok) {
            throw new Error('DB 연결 안됨');
        }
        
        // DB 연결 성공시에만 박스들을 초기화
        cropItems.forEach((item, index) => {
            item.innerHTML = '조회 중...';
        });
        
    } catch (error) {
        console.log('DB 미연결 상태 - 탐색 탭 기본 박스 유지:', error);
        // DB가 연결되지 않은 경우 원본 HTML 구조 유지하고 함수 종료
        return;
    }
    
    try {
        const recentPeople = await findRecentPeople(1, 50, 5);
        
        // 각 crop-item div에 이미지 설정
        cropItems.forEach((item, index) => {
            if (index < recentPeople.length) {
                const person = recentPeople[index];
                const firstImage = person.images[0];
                // 실제 감지된 시간 사용
                const detectedTime = firstImage.timestamp ? 
                    new Date(firstImage.timestamp).toLocaleTimeString('ko-KR', { hour12: false }) : 
                    `14:30:${15 + index * 7}`;
                
                item.innerHTML = `
                    <div style="text-align: center; height: 100%;">
                        <img src="data:${firstImage.type};base64,${firstImage.data}" 
                             style="width: 100%; height: 60px; object-fit: cover; border-radius: 3px; margin-bottom: 3px;"
                             onclick="showPersonDetails(${person.person_id})">
                        <div style="font-size: 11px; margin-bottom: 2px;">ID: ${person.person_id}</div>
                        <div style="font-size: 10px; color: #666;">${detectedTime}</div>
                    </div>
                `;
                // 기존 onclick 이벤트 제거하고 실제 시간으로 새로 설정
                item.removeAttribute('onclick');
                item.setAttribute('onclick', `selectCrop(this, '${detectedTime}')`);
            } else {
                item.innerHTML = 'Person ' + (index + 1);
                // onclick 이벤트 복원
                item.setAttribute('onclick', `selectCrop(this, '14:30:${15 + index * 7}')`);
            }
        });
        
    } catch (error) {
        console.log('데이터 조회 실패, 기본 박스 표시:', error);
        // 에러 시 원본 텍스트로 복원
        cropItems.forEach((item, index) => {
            item.innerHTML = 'Person ' + (index + 1);
            // onclick 이벤트 복원
            item.setAttribute('onclick', `selectCrop(this, '14:30:${15 + index * 7}')`);
        });
    }
}

// Person 상세 정보 표시
async function showPersonDetails(personId) {
    const images = await getPersonImages(personId);
    
    if (images && images.length > 0) {
        const newWindow = window.open('', '_blank', 'width=800,height=600,scrollbars=yes');
        let html = `
            <html>
            <head><title>Person ${personId} 상세 정보</title></head>
            <body style="font-family: Arial, sans-serif; padding: 20px;">
                <h2>Person ID: ${personId} (총 ${images.length}개 이미지)</h2>
                <div style="display: grid; grid-template-columns: repeat(auto-fill, minmax(200px, 1fr)); gap: 15px;">
        `;
        
        images.forEach(image => {
            html += `
                <div style="border: 1px solid #ddd; padding: 10px; border-radius: 5px;">
                    <img src="data:${image.type};base64,${image.data}" 
                         style="width: 100%; height: 150px; object-fit: cover;">
                    <p style="font-size: 12px; margin: 5px 0;">
                        <strong>파일:</strong> ${image.filename}<br>
                        <strong>시간:</strong> ${image.timestamp}<br>
                        <strong>카메라:</strong> ${image.camera_id}
                    </p>
                </div>
            `;
        });
        
        html += `
                </div>
            </body>
            </html>
        `;
        
        newWindow.document.write(html);
    }
}

// 페이지 종료시 자동 업데이트 정리
window.addEventListener('beforeunload', function() {
    stopExploreAutoUpdate();
});

// 페이지 숨김시 자동 업데이트 중지, 다시 보일때 재시작
document.addEventListener('visibilitychange', function() {
    if (document.hidden) {
        stopExploreAutoUpdate();
    } else {
        // 탐색 탭이 활성화되어 있을 때만 재시작
        const detectionSection = document.getElementById('detection');
        if (detectionSection && !detectionSection.classList.contains('hidden')) {
            startExploreAutoUpdate(15);
        }
    }
});

