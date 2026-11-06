@echo off
setlocal
chcp 65001 >nul
cd /d "%~dp0"
echo Installing official narrative skills from the repositories...
where py >nul 2>nul
if %errorlevel%==0 (
  py -3 "Tools\install_real_narrative_skills.py"
) else (
  where python >nul 2>nul
  if %errorlevel%==0 (
    python "Tools\install_real_narrative_skills.py"
  ) else (
    echo Python 3 is required. Install Python from https://www.python.org/downloads/
    echo Or use: python Tools\install_real_narrative_skills.py
    pause
    exit /b 1
  )
)
if errorlevel 1 (
  echo.
  echo Installation was not completed. Check the message above.
  pause
  exit /b 1
)
echo.
echo Installation complete. Restart Claude Code.
pause
