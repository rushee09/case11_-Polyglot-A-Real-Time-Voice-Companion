@echo off
setlocal

set ROOT=%~dp0
set BACKEND=%ROOT%backend
set FRONTEND=%ROOT%frontend

echo Starting Polyglot Voice Companion...
echo.

:: Start backend (no --reload to avoid watchfiles scanning the whole drive)
start "Polyglot Backend" cmd /k "cd /d "%BACKEND%" && venv\Scripts\uvicorn.exe app.main:app --port 8001 --log-level info --access-log"

:: Small delay so backend gets a head start
timeout /t 2 /nobreak >nul

:: Start frontend
start "Polyglot Frontend" cmd /k "cd /d "%FRONTEND%" && npm run dev"

echo.
echo Backend : http://localhost:8001
echo API Docs: http://localhost:8001/docs
echo Frontend: http://localhost:5173
echo.
echo Both servers are starting in separate windows.
pause
