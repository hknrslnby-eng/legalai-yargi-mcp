@echo off
setlocal
set "HERE=%~dp0"
if exist "%HERE%app" (
  set "ROOT=%HERE%"
) else (
  set "ROOT=%HERE%.."
)
set "SOCRATLEGAL_ENV_FILE=%ROOT%config\.env"
"%ROOT%\runtime\uv.exe" run --directory "%ROOT%\app" socratlegal-mcp %*
exit /b %ERRORLEVEL%
