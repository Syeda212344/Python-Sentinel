@echo off
setlocal
cd /d "%~dp0"
set SENTINEL_MODE=windows
where py >nul 2>&1
if %errorlevel%==0 (set PY=py) else (set PY=python)
%PY% -m pip install -r requirements.txt || goto :failed
%PY% manage.py migrate || goto :failed
echo.
echo WINDOWS EVENT MODE: needs access to supported local event logs.
echo If blocked on a campus laptop, use START_DEMO.bat instead.
echo Open http://127.0.0.1:8000/ in Chrome or Edge
%PY% manage.py runserver 127.0.0.1:8000 --noreload
goto :end
:failed
echo Setup failed. Read START_HERE_WINDOWS.md for help.
pause
:end
endlocal
