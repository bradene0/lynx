@echo off
echo 🌌 Setting up LYNX - Linked Knowledge Network Explorer
echo ==================================================

REM Check if Node.js is installed
node --version >nul 2>&1
if %errorlevel% neq 0 (
    echo ❌ Node.js is not installed. Please install Node.js 20+ first.
    pause
    exit /b 1
)
echo ✅ Node.js is available

REM Check if Docker is installed
docker --version >nul 2>&1
if %errorlevel% neq 0 (
    echo ❌ Docker is not installed. Please install Docker Desktop first.
    pause
    exit /b 1
)
echo ✅ Docker is available

REM Check if Python is installed
python --version >nul 2>&1
if %errorlevel% neq 0 (
    echo ❌ Python is not installed. Please install Python 3.11+ first.
    pause
    exit /b 1
)
echo ✅ Python is available

echo.
echo Installing dependencies...
call npm install

echo.
echo Setting up environment files...

if not exist .env (
    copy .env.example .env
    echo ✅ Created .env file from template
    echo ⚠️  Please edit .env and add your OpenAI API key
) else (
    echo ✅ .env file already exists
)

if not exist scripts\ingestion\.env (
    copy scripts\ingestion\.env.example scripts\ingestion\.env
    echo ✅ Created ingestion .env file from template
)

echo.
echo Starting Docker services...
docker-compose up -d

echo.
echo Waiting for database to be ready...
timeout /t 10 /nobreak >nul

echo.
echo Running database migrations...
cd apps\web
call npm run db:migrate
cd ..\..

echo.
echo 🎉 LYNX setup complete!
echo.
echo Next steps:
echo 1. Edit .env and add your OpenAI API key
echo 2. Run 'npm run dev' to start the development server
echo 3. Run 'npm run ingest' to populate the database with initial data
echo.
echo Happy exploring! 🌌
pause
