@echo off
echo 🧪 Testing LYNX Setup
echo ==================

echo.
echo 1. Testing Node.js dependencies...
call npm install
if %errorlevel% neq 0 (
    echo ❌ npm install failed
    pause
    exit /b 1
)
echo ✅ Dependencies installed

echo.
echo 2. Testing TypeScript compilation...
cd apps\web
call npx tsc --noEmit
if %errorlevel% neq 0 (
    echo ❌ TypeScript compilation failed
    pause
    exit /b 1
)
echo ✅ TypeScript compiles successfully
cd ..\..

echo.
echo 3. Testing Docker services...
docker-compose up -d
if %errorlevel% neq 0 (
    echo ❌ Docker services failed to start
    pause
    exit /b 1
)
echo ✅ Docker services started

echo.
echo 4. Waiting for database to be ready...
timeout /t 15 /nobreak >nul

echo.
echo 5. Testing database connection...
cd apps\web
call npx drizzle-kit push:pg --config=drizzle.config.ts
if %errorlevel% neq 0 (
    echo ❌ Database connection failed
    echo Make sure DATABASE_URL is set in .env
    pause
    exit /b 1
)
echo ✅ Database connection successful
cd ..\..

echo.
echo 6. Testing Next.js build...
cd apps\web
call npm run build
if %errorlevel% neq 0 (
    echo ❌ Next.js build failed
    pause
    exit /b 1
)
echo ✅ Next.js builds successfully
cd ..\..

echo.
echo 🎉 All tests passed! LYNX foundation is working.
echo.
echo Next steps:
echo 1. Add your OpenAI API key to .env
echo 2. Run 'npm run dev' to start development server
echo 3. Run 'npm run ingest' to test data pipeline
pause
