// 전역 변수에 현재 위치 정보 저장
let currentLocation = '';
let locationName = '';
let userLocations = {}; // 사용자별 위치 정보 저장
let streamSocket = null;

const MAIN_CAMERA_INTERVAL = 50; 
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
        setTimeout(() => {
            initializeCharts();
            updateLogTable();
            updateTrackingGrid();
            refreshLogs();
        }, 100);
    }
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







// CAMERA STREAM

let mainSocket = null;
let thumbSockets = {};
let currentMainCamera = null;


// Connect thumb previews for all cameras
function connectThumbCameras() {
    const cameraIds = ['camera1', 'camera2', 'camera3', 'camera4'];

    cameraIds.forEach((cameraId) => {
        const protocol = window.location.protocol === 'https:' ? 'wss:' : 'ws:';
        const wsUrl = `${protocol}//${window.location.host}/ws/camera/${cameraId}/`;

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

// Connect main camera
function startMainCamera(cameraId, locationLabel) {
    stopMainCamera();

    currentMainCamera = cameraId;
    document.getElementById("mainVideoPlaceholder").style.display = "none";
    document.getElementById("mainCamera").style.display = "block";

    const protocol = window.location.protocol === 'https:' ? 'wss:' : 'ws:';
    const wsUrl = `${protocol}//${window.location.host}/ws/camera/${cameraId}/`;

    mainSocket = new WebSocket(wsUrl);
    const videoEl = document.getElementById("mainCamera");

    mainSocket.onmessage = (event) => {
        const now = Date.now();
        if (now - lastMainFrameTime < MAIN_CAMERA_INTERVAL) return;
        lastMainFrameTime = now;

        videoEl.src = `data:image/jpeg;base64,${event.data}`;
    };

    document.getElementById("mainVideoInfo").textContent = locationLabel;
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

// When user selects camera
function selectCamera(element, location, camId) {
    const thumbs = document.querySelectorAll('.camera-thumb');
    thumbs.forEach(thumb => thumb.classList.remove('active'));
    element.classList.add('active');

    const videoInfo = document.querySelector('.video-info');
    videoInfo.textContent = `${location} - ${camId}`;

    const mainVideo = document.getElementById('mainCamera');

    if (mainVideo) {
        mainVideo.srcObject = null;
        mainVideo.style.transform = '';
        mainVideo.style.filter = '';
        startStreamSocket(camId);  // <== new function to connect and stream RTSP via WebSocket
    }
}
// Call after login
window.addEventListener('DOMContentLoaded', () => {
    connectThumbCameras();
});

function startStreamSocket(camId) {
    const mainVideo = document.getElementById("mainCamera");
    const placeholder = document.getElementById("mainVideoPlaceholder");

    // Stop previous MJPEG stream
    if (mainVideo.src) {
        mainVideo.src = "";
    }

    const protocol = window.location.protocol === 'https:' ? 'https:' : 'http:';
    const url = `${protocol}//${window.location.host}/mjpeg/stream/${camId}/`;

    // Update the src of <img> tag to MJPEG stream
    mainVideo.src = url;
    mainVideo.style.display = "block";
    placeholder.style.display = "none";

    document.getElementById("mainVideoInfo").textContent = `카메라: ${camId}`;
}