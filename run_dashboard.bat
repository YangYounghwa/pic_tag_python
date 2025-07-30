@echo off

REM backend 폴더로 이동 (asgi.py가 있는 backend/backend 기준)
cd /d C:\Users\astro\pkb_test\pic_tag_python\backend

REM 전역 가상환경 활성화
call C:\pkb\venv\Scripts\activate

REM Daphne 실행 (ASGI 애플리케이션 경로 정확히 지정)
daphne -b 0.0.0.0 -p 8080 backend.asgi:application

pause
