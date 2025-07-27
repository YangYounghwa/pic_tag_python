


# 개요

# 목적

# 실행 방법


## python 버전 및 라이브러리
python==3.12 환경에서 제작되었지만 다른 환경에서도 (아마도) 실행 가능합니다.

다음 명령어로 필요한 라이브러리를 받으시면 됩니다.
```
pip install -r requirements.txt
```

## 서버 실행

```
cd backend
daphne -b 0.0.0.0 -p 8080 backend.asgi:application
```




# 라이센스

 - 사람 재식별 학습에 사용한 데이터는 [AI hub](https://aihub.or.kr/)에서 제공받았으며 해당 데이터는 한국지능정보사회진흥원의 사업결과입니다.
 - YOLOv8n 및 YOLOv11n 의 사용에 따라 pic_tag는 AGPL3.0의 라이선스가 부여됩니다.