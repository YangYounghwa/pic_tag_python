


# 개요

AI 기반 사람 탐지 및 자동 태깅 시스템

# 목적

낮은 컴퓨팅으로 사람을 재식별하여 동일인물이 어느 동선, 어느 시간대에 등장했는지 파악할 수 있다.
IP카메라를 RTSP를 사용하여 연결할 수 있습니다.



# 실행 방법
## 저장소 복제
```
git clone https://github.com/yangyounghwa/pic_tag_python.git
cd pic_tag_ptyhon
```


## python 버전 및 라이브러리
python==3.12 환경.

다음 명령어로 필요한 라이브러리를 받으시면 됩니다.
```
pip install -r requirements.txt
```

인텔 cpu의 경우 자동으로 OpenVINO로 최적화된 모델이 구동됩니다.


## 서버 실행

```
cd backend
daphne -b 0.0.0.0 -p 8080 backend.asgi:application
```

##
```
cd pic_tag
python main.py live
```

RTSP가 아닌 일반 비디오 실행.

```
cd pic_tag
python main.py video 2 path_to_video1 path_to_video2
```




# 라이센스

 - 사람 재식별 학습에 사용한 데이터는 [AI hub](https://aihub.or.kr/)에서 제공받았으며 해당 데이터는 한국지능정보사회진흥원의 사업결과입니다.
 - YOLOv8n 및 YOLOv11n 의 사용에 따라 pic_tag는 AGPL3.0의 라이선스가 부여됩니다.
