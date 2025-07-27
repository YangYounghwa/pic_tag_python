
https://github.com/libjpeg-turbo/libjpeg-turbo/releases

daphne backend.asgi:application

# 개요

# 목적

# 실행 방법

## libjpeg-turbo 설치 
다음 링크 [libjpeg-turbo|https://github.com/libjpeg-turbo/libjpeg-turbo/releases]에서 받으시고 환경변수 등록을 해야 합니다.

## python 버전 및 라이브러리
python==3.12 환경에서 제작되었지만 다른 환경에서도 (아마도) 실행 가능합니다.

다음 명령어로 필요한 라이브러리를 받으시면 됩니다.
```
pip install -r requirements.txt
```

## 서버 실행

```
cd backend
daphne -b 192.168.0.0 -p 8080 backend.asgi:application
```



# 사용 방법

# 학습 라이센스
