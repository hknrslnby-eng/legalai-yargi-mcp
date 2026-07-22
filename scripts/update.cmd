@echo off
setlocal
set "HERE=%~dp0"
if exist "%HERE%app" (
  set "ROOT=%HERE%"
) else (
  set "ROOT=%HERE%.."
)
set "SOCRATLEGAL_ENV_FILE=%ROOT%config\.env"
"%ROOT%\runtime\uv.exe" run --directory "%ROOT%\app" socratlegal update install --active-app "%ROOT%\app" --platform-tag windows-x64
set "EXIT_CODE=%ERRORLEVEL%"
echo.
if not "%EXIT_CODE%"=="0" pause
exit /b %EXIT_CODE%
