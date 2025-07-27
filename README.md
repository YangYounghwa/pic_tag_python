


# 개요

# 목적

# 실행 방법

## libjpeg-turbo 설치 



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



# 사용 방법

# 학습 라이센스
