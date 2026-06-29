@echo off
setlocal enabledelayedexpansion

:: ── Config ────────────────────────────────────────────────────────────────────
set "TOOL_DIR=%~dp0"
set "TOOL_DIR=%TOOL_DIR:~0,-1%"
set "PYTHON=python"
:: ─────────────────────────────────────────────────────────────────────────────

cd /d "%TOOL_DIR%"

where %PYTHON% >nul 2>&1
if errorlevel 1 (
    echo.
    echo  ERROR: Python not found. Install Python and add it to PATH, then re-run.
    echo  https://www.python.org/downloads/
    echo.
    pause
    exit /b 1
)

%PYTHON% -c "import depth_pro, imageio" >nul 2>&1
if errorlevel 1 (
    echo.
    echo  depth_pro is not installed.
    echo  Command: pip install -e "%TOOL_DIR%"
    echo.
    choice /c yn /n /m "  Run it now? [Y=yes / N=quit] "
    if errorlevel 2 ( echo. & pause & exit /b 1 )
    echo.
    %PYTHON% -m pip install -e "%TOOL_DIR%"
    if errorlevel 1 (
        echo.
        echo  Install failed. See output above.
        pause
        exit /b 1
    )
    echo.
    echo  Installed. Continuing...
    echo.
)

set "ERROR_COUNT=0"
if not exist "%TOOL_DIR%\logs" mkdir "%TOOL_DIR%\logs"
for /f "usebackq delims=" %%T in (`powershell -NoProfile -Command "Get-Date -Format 'yyyy-MM-dd_HH-mm-ss'"`) do set "TS=%%T"
set "LOG=%TOOL_DIR%\logs\depth_pro_%TS%.log"
echo ======================================== > "%LOG%"
echo  Run: %TS% >> "%LOG%"
echo ======================================== >> "%LOG%"

if "%~1"=="" (
    echo.
    echo  Drag image files onto this script, or paste an absolute path below.
    echo.
    set /p "ARG=  Image path: "
    if "!ARG!"=="" ( pause & exit /b 0 )
    set "ARG=!ARG:"=!"
    call :process "!ARG!"
    goto :done
)

:loop
if "%~1"=="" goto :done
call :process "%~1"
shift
goto :loop

:done
echo.
if "!ERROR_COUNT!"=="0" (
    echo  All files processed successfully.
    echo All files processed successfully. >> "%LOG%"
) else (
    echo  Finished with !ERROR_COUNT! errors. Check output above.
    echo Finished with !ERROR_COUNT! errors. >> "%LOG%"
)
echo  Log: %LOG%
echo.
pause
exit /b 0


:process
set "INPUT=%~f1"
set "STEM=%~n1"
set "OUT_DIR=%~dp1%~n1"
set "NPZ=%OUT_DIR%\%STEM%.npz"
set "EXR=%OUT_DIR%\%STEM%.exr"
set "PNG=%OUT_DIR%\%STEM%.png"

echo.
echo ----------------------------------------
echo  Input : %~nx1
echo  Output: %OUT_DIR%
echo ----------------------------------------
echo Input: %INPUT% >> "%LOG%"

echo [1/2] Estimating depth...
%PYTHON% -m depth_pro.cli.run -i "%INPUT%" -o "%OUT_DIR%" --skip-display >> "%LOG%" 2>&1
if errorlevel 1 (
    echo  ERROR: depth inference failed. See log for details.
    echo ERROR: depth inference failed. >> "%LOG%"
    set /a ERROR_COUNT+=1
    exit /b 1
)

if not exist "%NPZ%" (
    echo  ERROR: NPZ not found at %NPZ%
    echo ERROR: NPZ not found: %NPZ% >> "%LOG%"
    set /a ERROR_COUNT+=1
    exit /b 1
)

echo [2/2] Converting NPZ to EXR...
%PYTHON% "%TOOL_DIR%\npz_to_exr.py" -i "%NPZ%" >> "%LOG%" 2>&1
if errorlevel 1 (
    echo  ERROR: npz_to_exr.py failed. See log for details.
    echo ERROR: npz_to_exr.py failed. >> "%LOG%"
    set /a ERROR_COUNT+=1
    exit /b 1
)

echo  Done -- %EXR%
echo  Done -- %PNG%
echo Done: %EXR% >> "%LOG%"
echo Done: %PNG% >> "%LOG%"
exit /b 0
