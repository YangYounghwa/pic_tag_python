
모델은 전부 저장할 때에 외부 모듈(ultralytics, 등)을 저장하지 않고 .pth 파일만 불러와서 바로 사용할 수 있도록. 

지금은 대부분 placeholder입니다. 

가상환경은 python의 기본 venv를 추천합니다.

설치 컴퓨터에 docker혹은 conda를 일일이 설치하기에 어려움, 라이선스 문제 등이 있습니다.

main.py에서 cropper, dashboard, cleanup_cron, feature_extractor를 하나하나씩 호출하여 사용합니다.


