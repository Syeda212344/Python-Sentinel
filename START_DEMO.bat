@echo off
setlocal
cd /d "%~dp0"
set SENTINEL_MODE=demo
where py >nul 2>&1
if %errorlevel%==0 (set PY=py) else (set PY=python)
%PY% --version || goto :failed
%PY% -m pip install -r requirements.txt || goto :failed
%PY% manage.py migrate || goto :failed
%PY% manage.py seed_demo || goto :failed
echo.
echo =========================================================
echo PYTHON SENTINEL DJANGO DEMO
 echo Open http://127.0.0.1:8000/ in Chrome or Edge
 echo Stop server by pressing Ctrl+C
 echo =========================================================
%PY% manage.py runserver 127.0.0.1:8000 --noreload
goto :end
:failed
echo.
echo Setup failed. Read START_HERE_WINDOWS.md for help.
pause
:end
endlocal
