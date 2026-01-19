#!/bin/bash
if [ ! -d "venv" ]; then
    echo "Creating virtual environment..."
    python3 -m venv venv
    if [ $? -eq 0 ]; then
        echo "Virtual environment created."
    else
        echo "Error creating virtual environment. Please check your Python installation."
        exit 1
    fi
fi

echo "Activating virtual environment..."
source venv/bin/activate

echo "Installing dependencies from requirements.txt..."
pip install -r requirements.txt

echo "Running the application..."
python main.py "$@"
