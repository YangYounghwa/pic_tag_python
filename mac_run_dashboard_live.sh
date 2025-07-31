#!/bin/bash
echo "Starting script..."

# Activate your environment
source /Users/hong/Projects/pic_tag_python/venv/bin/activate || { echo "Failed to activate virtualenv"; exit 1; }
echo "Virtualenv activated"

# Change to project directory
cd /Users/hong/Projects/pic_tag_python/pic_tag || { echo "Failed to cd to pic_tag"; exit 1; }
echo "Changed to pic_tag directory"

# Run main.py with live argument
python main.py live || { echo "Failed to run main.py with live argument"; exit 1; }
echo "Live command executed"

# Pause equivalent
read -p "Press Enter to continue..."