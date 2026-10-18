@echo off
setlocal
set "PACK=%~1"
if not defined PACK if exist "%~dp0generation-plan.json" set "PACK=%~dp0."
if not defined PACK set /p "PACK=Paste the V3 pack folder path: "
if not defined PACK exit /b 1
set "PACK=%PACK:"=%"
set "ROOT=%~dp0."
:findroot
if exist "%ROOT%\scripts\avbrief.py" goto run
for %%I in ("%ROOT%\..") do set "PARENT=%%~fI"
if "%PARENT%"=="%ROOT%" goto missing
set "ROOT=%PARENT%"
goto findroot
:run
set "PYTHONIOENCODING=utf-8"
"%ROOT%\.venv\Scripts\python.exe" "%ROOT%\scripts\avbrief.py" prepare-v3-images --folder "%PACK%"
set "RESULT=%ERRORLEVEL%"
echo.
if "%RESULT%"=="0" echo Posting copies are in the pack's posting-ready folder. Originals are preserved.
if not "%RESULT%"=="0" echo Export incomplete. Review the errors above and export-report.json if present.
pause
exit /b %RESULT%
:missing
echo Could not locate Arabic Brief. Keep this launcher inside the project.
pause
exit /b 1
