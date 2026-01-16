@echo off
IF NOT EXIST "venv" (
    echo "Creating virtual environment..."
    python -m venv venv
    IF ERRORLEVEL 1 (
        echo "Error creating virtual environment. Please check your Python installation."
        exit /b 1
    )
    echo "Virtual environment created."
)

echo "Activating virtual environment..."
call "venv\Scripts\activate.bat"

echo "Installing dependencies from requirements.txt..."
pip install -r requirements.txt

echo "Running the application..."
python main.py %*

call "venv\Scripts\deactivate.bat"
echo "Process finished. You can close this window."
pause