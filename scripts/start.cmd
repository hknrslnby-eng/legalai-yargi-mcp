@echo off
setlocal
set "ROOT=%~dp0.."
"%ROOT%\runtime\uv.exe" run --directory "%ROOT%\app" socratlegal-mcp %*
exit /b %ERRORLEVEL%
