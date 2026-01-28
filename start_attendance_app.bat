@echo off
setlocal

set "APP_DIR=%~dp0"
if not exist "%APP_DIR%\app.py" (
    echo Could not find app.py in "%APP_DIR%".
    exit /b 1
)

pushd "%APP_DIR%" >nul
if errorlevel 1 (
    echo Failed to enter "%APP_DIR%".
    exit /b 1
)

echo Starting Attendance App from "%APP_DIR%" ...
py -3 app.py
set "RC=%errorlevel%"

popd >nul
exit /b %RC%
