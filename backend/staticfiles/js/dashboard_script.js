// 전역 변수에 현재 위치 정보 저장
let currentLocation = '';
let locationName = '';
let userLocations = {}; // 사용자별 위치 정보 저장
let streamSocket = null;


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

// 카메라 선택
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


function startStreamSocket(camId) {
    if (streamSocket) {
        streamSocket.close();
    }

    const protocol = window.location.protocol === 'https:' ? 'wss:' : 'ws:';
    const url = `${protocol}//${window.location.host}/ws/camera/${camId}/`;
    streamSocket = new WebSocket(url);

    const mainVideo = document.getElementById("mainCamera");
    const placeholder = document.getElementById("mainVideoPlaceholder");

    streamSocket.onopen = () => {
        console.log("✅ RTSP WebSocket connected:", camId);
        mainVideo.style.display = "block";
        placeholder.style.display = "none";
    };

    streamSocket.onmessage = (event) => {
        const img = new Image();
        img.onload = function () {
            const canvas = document.createElement("canvas");
            canvas.width = img.width;
            canvas.height = img.height;
            const ctx = canvas.getContext("2d");
            ctx.drawImage(img, 0, 0);
            mainVideo.src = canvas.toDataURL("image/jpeg");
        };
        img.src = "data:image/jpeg;base64," + event.data;
    };

    streamSocket.onerror = (err) => {
        console.error("❌ WebSocket error:", err);
    };

    streamSocket.onclose = () => {
        console.log("⚠️ WebSocket closed");
        placeholder.style.display = "block";
        placeholder.innerHTML = "카메라 연결 종료";
    };
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

// 크롭 이미지 선택
function selectCrop(element, timestamp) {
    // 기존 선택 해제
    const crops = document.querySelectorAll('.crop-item');
    crops.forEach(crop => crop.classList.remove('selected'));

    // 현재 항목 선택
    element.classList.add('selected');

    // 타임라인에 마커 표시
    const marker = document.querySelector('.timeline-marker');
    if (marker) {
        // 시간에 따른 위치 계산 (예시)
        const timeValue = parseInt(timestamp.split(':')[2]);
        const position = (timeValue / 60) * 100; // 분 단위로 계산
        marker.style.left = Math.min(position, 90) + '%';
    }

    // 로그에 해당 시간 강조
    highlightLogEntry(timestamp);
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

// 통계 데이터 업데이트
function updateStats() {
    const statValues = document.querySelectorAll('.stat-value');
    if (statValues.length >= 4) {
        // 실시간으로 변하는 데이터 시뮬레이션
        const currentEntry = parseInt(statValues[0].textContent) || 142;
        const currentExit = parseInt(statValues[1].textContent) || 98;

        // 간헐적으로 입장자 증가
        if (Math.random() < 0.1) {
            statValues[0].textContent = currentEntry + 1;
            statValues[2].textContent = (currentEntry + 1) - currentExit; // 현재 체류 인원
        }

        // 간헐적으로 퇴장자 증가
        if (Math.random() < 0.08) {
            statValues[1].textContent = currentExit + 1;
            statValues[2].textContent = currentEntry - (currentExit + 1); // 현재 체류 인원
        }

        // 평균 체류시간 변동
        const avgTimes = ['23분', '25분', '27분', '24분', '26분'];
        statValues[3].textContent = avgTimes[Math.floor(Math.random() * avgTimes.length)];
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
setInterval(updateStats, 10000);        // 10초마다 통계 업데이트
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
        const mainVideo = document.getElementById("mainCamera");
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

// WebSocket 메시지 처리
async function handleWebSocketMessage(data) {
    console.log('WebSocket 메시지 받음:', data);

    switch (data.type) {
        case 'user_joined':
            console.log('새 사용자 입장:', data.user_id, '위치:', data.location_name);
            if (data.location && data.location !== currentLocation) {
                setUserLocation(data.user_id, data.location, data.location_name);
                await createPeerConnection(data.user_id, data.location, data.location_name);
            }
            break;

        case 'location_updated':
            console.log('사용자 위치 업데이트:', data.user_id, '위치:', data.location_name);
            if (data.location && data.location !== currentLocation) {
                setUserLocation(data.user_id, data.location, data.location_name);
                await createPeerConnection(data.user_id, data.location, data.location_name);
            }
            break;

        case 'user_left':
            console.log('사용자 퇴장:', data.user_id);
            closePeerConnection(data.user_id);
            break;

        case 'offer':
            await handleOffer(data);
            break;

        case 'answer':
            await handleAnswer(data);
            break;

        case 'ice_candidate':
            await handleIceCandidate(data);
            break;
    }
}

// Peer Connection 생성
async function createPeerConnection(userId, userLocation, locationName) {
    try {
        console.log(`Peer Connection 생성: ${userId} (${locationName})`);
        const peerConnection = new RTCPeerConnection(iceServers);
        peerConnections[userId] = peerConnection;

        // 사용자 위치 정보 저장
        peerConnections[userId].userLocation = userLocation;
        peerConnections[userId].locationName = locationName;

        // ICE Candidate 이벤트
        peerConnection.onicecandidate = function (event) {
            if (event.candidate) {
                socket.send(JSON.stringify({
                    type: 'ice_candidate',
                    candidate: event.candidate,
                    to_user: userId
                }));
            }
        };

        // Remote Stream 이벤트
        peerConnection.ontrack = function (event) {
            console.log('Remote stream 받음:', userId, locationName);
            remoteStreams[userId] = event.streams[0];
            displayRemoteStream(userId, event.streams[0], userLocation, locationName);
        };



        // Offer 생성 및 전송
        const offer = await peerConnection.createOffer();
        await peerConnection.setLocalDescription(offer);

        socket.send(JSON.stringify({
            type: 'offer',
            offer: offer,
            to_user: userId
        }));

    } catch (error) {
        console.error('Peer Connection 생성 오류:', error);
    }
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

// Remote Stream 표시
function displayRemoteStream(userId, stream, userLocation, locationName) {
    console.log(`원격 스트림 표시: ${userId}, 위치: ${locationName}`);

    // 해당 위치의 썸네일 찾기
    const thumbElement = document.getElementById(`thumb-${userLocation}`);
    if (thumbElement) {
        // 기존 내용 제거하고 비디오 요소 생성
        thumbElement.innerHTML = '';
        const video = document.createElement('video');
        video.autoplay = true;
        video.muted = true;
        video.srcObject = stream;
        video.style.width = '100%';
        video.style.height = '100%';
        video.style.objectFit = 'cover';

        thumbElement.appendChild(video);

        // 썸네일 활성화 표시
        const thumbContainer = thumbElement.parentElement;
        thumbContainer.classList.add('active');

        console.log(`${locationName} 카메라 스트림 연결됨`);
    }
}




function showDashboard() {
    document.getElementById('loginPage').style.display = 'none';
    document.getElementById('dashboardPage').style.display = 'block';

    Object.entries(cameraMap).forEach(([domId, cameraId]) => {
        startCameraTileStream(domId, cameraId);
    });


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

// 키보드 단축키
document.addEventListener('keydown', function (e) {
    // 스페이스바로 재생/일시정지
    if (e.code === 'Space' && document.getElementById('monitoring').style.display !== 'none') {
        e.preventDefault();
        const playBtn = document.querySelector('.video-controls button');
        if (playBtn) playBtn.click();
    }

    // 숫자 키로 카메라 선택
    if (e.code >= 'Digit1' && e.code <= 'Digit4') {
        const cameraIndex = parseInt(e.code.charAt(5)) - 1;
        const cameras = document.querySelectorAll('.camera-thumb');
        if (cameras[cameraIndex]) {
            cameras[cameraIndex].click();
        }
    }
});

// 터치 지원 (모바일)
let touchStartX = 0;
document.addEventListener('touchstart', function (e) {
    touchStartX = e.touches[0].clientX;
});

document.addEventListener('touchend', function (e) {
    const touchEndX = e.changedTouches[0].clientX;
    const diff = touchStartX - touchEndX;

    // 스와이프로 카메라 전환
    if (Math.abs(diff) > 50) {
        const activeCamera = document.querySelector('.camera-thumb.active');
        const cameras = Array.from(document.querySelectorAll('.camera-thumb'));
        const currentIndex = cameras.indexOf(activeCamera);

        if (diff > 0 && currentIndex < cameras.length - 1) {
            cameras[currentIndex + 1].click();
        } else if (diff < 0 && currentIndex > 0) {
            cameras[currentIndex - 1].click();
        }
    }
});


function startCameraTileStream(domId, cameraId) {
    const protocol = window.location.protocol === 'https:' ? 'wss:' : 'ws:';
    const wsUrl = `${protocol}//${window.location.host}/ws/camera/${cameraId}/`;

    const container = document.getElementById(`thumb-${domId}`);
    if (!container) return;

    const socket = new WebSocket(wsUrl);
    cameraSockets[domId] = socket;

    socket.onopen = () => {
        console.log(`🟢 ${domId} 연결됨: ${cameraId}`);
        container.innerHTML = ""; // Clear placeholder
        const img = document.createElement("img");
        img.style.width = "100%";
        img.style.height = "100%";
        img.style.objectFit = "cover";
        img.id = `img-${domId}`;
        container.appendChild(img);
    };

    socket.onmessage = (event) => {
        const imgEl = document.getElementById(`img-${domId}`);
        if (imgEl) {
            imgEl.src = "data:image/jpeg;base64," + event.data;
        }
    };

    socket.onerror = (err) => {
        console.error(`❌ ${domId} 소켓 오류`, err);
    };

    socket.onclose = () => {
        console.log(`⚠️ ${domId} 연결 종료됨`);
        container.innerHTML = "연결 종료됨";
    };
}

