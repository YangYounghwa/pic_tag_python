#!/bin/bash

# Activate your environment
source /Users/hong/Projects/pic_tag_python/venv/bin/activate

# Change to your project directory
cd /Users/hong/Projects/pic_tag_python/backend

# Run Daphne server
daphne -b 0.0.0.0 -p 8080 backend.asgi:application

# Pause equivalent (wait for user input)
read -p "Press Enter to continue..."