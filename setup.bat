@echo off
REM Medical-RAG Setup Script for Windows
REM This script automates the setup process for Medical-RAG

echo ========================================
echo    Medical-RAG Setup Script
echo ========================================
echo.

REM Step 1: Check Python
echo Step 1: Checking Python installation...
python --version >nul 2>&1
if %errorlevel% neq 0 (
    echo [ERROR] Python not found. Please install Python 3.8 or higher.
    pause
    exit /b 1
)
for /f "tokens=*" %%i in ('python --version') do set PYTHON_VERSION=%%i
echo [SUCCESS] Python found: %PYTHON_VERSION%

REM Step 2: Check Ollama
echo.
echo Step 2: Checking Ollama installation...
ollama --version >nul 2>&1
if %errorlevel% neq 0 (
    echo [WARNING] Ollama not found!
    echo Please install Ollama from: https://ollama.ai/
    echo.
    set /p CONTINUE="Do you want to continue anyway? (y/n): "
    if /i not "%CONTINUE%"=="y" exit /b 1
) else (
    for /f "tokens=*" %%i in ('ollama --version 2^>^&1') do set OLLAMA_VERSION=%%i
    echo [SUCCESS] Ollama found: %OLLAMA_VERSION%
)

REM Step 3: Create virtual environment
echo.
echo Step 3: Creating virtual environment...
if not exist "venv" (
    python -m venv venv
    echo [SUCCESS] Virtual environment created
) else (
    echo [INFO] Virtual environment already exists
)

REM Step 4: Activate and install dependencies
echo.
echo Step 4: Installing Python dependencies...
call venv\Scripts\activate.bat
python -m pip install --upgrade pip >nul 2>&1
pip install -r requirements.txt
echo [SUCCESS] Dependencies installed

REM Step 5: Pull Ollama models
echo.
echo Step 5: Pulling required Ollama models...
echo [INFO] This may take a few minutes depending on your internet connection

ollama --version >nul 2>&1
if %errorlevel% equ 0 (
    echo.
    echo Pulling nomic-embed-text (embedding model)...
    ollama pull nomic-embed-text
    echo [SUCCESS] Embedding model ready
    
    echo.
    echo Which LLM model would you like to use?
    echo 1) gemma3:1b (Recommended - Fast, ~1GB)
    echo 2) llama3.2 (Balanced - ~2GB)
    echo 3) mistral (Best quality - ~4GB)
    echo 4) phi3 (Medical focused - ~2GB)
    echo 5) Skip (I'll do this later)
    set /p MODEL_CHOICE="Enter choice (1-5): "
    
    if "%MODEL_CHOICE%"=="1" (
        echo Pulling gemma3:1b...
        ollama pull gemma3:1b
        echo [SUCCESS] gemma3:1b ready
    ) else if "%MODEL_CHOICE%"=="2" (
        echo Pulling llama3.2...
        ollama pull llama3.2
        echo [SUCCESS] llama3.2 ready
    ) else if "%MODEL_CHOICE%"=="3" (
        echo Pulling mistral...
        ollama pull mistral
        echo [SUCCESS] mistral ready
    ) else if "%MODEL_CHOICE%"=="4" (
        echo Pulling phi3...
        ollama pull phi3
        echo [SUCCESS] phi3 ready
    ) else if "%MODEL_CHOICE%"=="5" (
        echo [INFO] Skipping model download. Remember to pull a model later!
    ) else (
        echo [ERROR] Invalid choice. Skipping model download.
    )
) else (
    echo [INFO] Skipping Ollama model download (Ollama not installed)
)

REM Step 6: Create .env file
echo.
echo Step 6: Creating environment configuration...
if not exist ".env" (
    copy .env.example .env >nul
    echo [SUCCESS] Created .env file from template
    echo [INFO] You can edit .env to customize settings
) else (
    echo [INFO] .env file already exists
)

REM Step 7: Summary
echo.
echo ========================================
echo    Setup Complete!
echo ========================================
echo.
echo [SUCCESS] Medical-RAG is ready to use!
echo.
echo Next steps:
echo.
echo 1. Build the knowledge base (required - first time only):
echo    python ingestion.py
echo    (This will take 5-10 minutes)
echo.
echo 2. Launch the application:
echo    venv\Scripts\activate
echo    streamlit run main2.py
echo.

set /p RUN_INGESTION="Would you like to run the ingestion now? (y/n): "
if /i "%RUN_INGESTION%"=="y" (
    echo.
    echo [INFO] Starting ingestion process...
    echo [INFO] This will crawl MedlinePlus and build the vector database
    echo [INFO] Expected time: 5-10 minutes
    echo.
    python ingestion.py
    
    if %errorlevel% equ 0 (
        echo.
        echo [SUCCESS] Knowledge base built successfully!
        echo.
        echo You can now launch the app:
        echo    streamlit run main2.py
    ) else (
        echo [ERROR] Ingestion failed. Please check the error messages above.
        pause
        exit /b 1
    )
) else (
    echo.
    echo [INFO] Skipping ingestion. Run 'python ingestion.py' when ready.
)

echo.
echo ========================================
echo    Useful Commands
echo ========================================
echo.
echo Start the app:
echo   streamlit run main2.py
echo.
echo Rebuild knowledge base:
echo   python ingestion.py
echo.
echo Check Ollama models:
echo   ollama list
echo.
echo Pull more models:
echo   ollama pull model-name
echo.
echo ========================================
echo.
echo [SUCCESS] Happy querying!
echo.

pause
