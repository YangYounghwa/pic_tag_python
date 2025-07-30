:: @echo off

:: 1. Open Anaconda Prompt is implicit — this will run in its shell
:: 2. Activate conda environment
CALL conda activate dashboard_v1

:: 3. Change to your project directory
cd /d c:\Users\astro\pkb_test\pic_tag_python

:: 4. Run Python script
python manage.py collectstatic
pause