@echo off
echo 🧪 LYNX Quick Test Suite
echo ========================

echo.
echo 1. Testing Node.js setup...
cd /d "%~dp0.."
call npm run build >nul 2>&1
if %errorlevel% neq 0 (
    echo ❌ Frontend build failed
    echo Run: npm install
    pause
    exit /b 1
)
echo ✅ Frontend builds successfully

echo.
echo 2. Testing database connection...
call npm run docker:up >nul 2>&1
timeout /t 10 /nobreak >nul
cd apps\web
call npx drizzle-kit push:pg --config=drizzle.config.ts >nul 2>&1
if %errorlevel% neq 0 (
    echo ❌ Database connection failed
    echo Check: DATABASE_URL in .env
    pause
    exit /b 1
)
echo ✅ Database connected
cd ..\..

echo.
echo 3. Testing Python dependencies...
cd scripts\ingestion
python -c "import sentence_transformers; import torch; print('✅ Python dependencies OK')" 2>nul
if %errorlevel% neq 0 (
    echo ❌ Python dependencies missing
    echo Run: pip install -r requirements.txt
    pause
    exit /b 1
)
cd ..\..

echo.
echo 4. Starting development server...
echo ✅ All tests passed!
echo.
echo Opening LYNX in your browser...
start http://localhost:3000
call npm run dev
