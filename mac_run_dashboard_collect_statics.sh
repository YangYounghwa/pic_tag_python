#!/bin/bash

# Activate your environment
source /Users/hong/Projects/pic_tag_python/venv/bin/activate

# Change to project directory
cd /Users/hong/Projects/pic_tag_python/pic_tag

# Run collectstatic
python manage.py collectstatic

# Pause equivalent (wait for user input)
read -p "Press Enter to continue..."