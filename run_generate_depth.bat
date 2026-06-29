@echo off
setlocal enabledelayedexpansion

:: ── Config ────────────────────────────────────────────────────────────────────
set "TOOL_DIR=%~dp0"
set "TOOL_DIR=%TOOL_DIR:~0,-1%"
set "PYTHON=python"
set "DEPTH_PRO=depth-pro-run"
:: ─────────────────────────────────────────────────────────────────────────────

cd /d "%TOOL_DIR%"
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
    echo  Finished with !ERROR_COUNT! error(s). Check output above.
    echo Finished with !ERROR_COUNT! error(s). >> "%LOG%"
)
echo  Log: %LOG%
echo.
pause
exit /b 0


:process
set "INPUT=%~f1"
set "STEM=%~n1"
set "OUT_DIR=%~dp1depth"
set "NPZ=%OUT_DIR%\%STEM%.npz"
set "EXR=%OUT_DIR%\%STEM%.exr"

echo.
echo ----------------------------------------
echo  Input : %~nx1
echo  Output: %OUT_DIR%
echo ----------------------------------------
echo Input: %INPUT% >> "%LOG%"

echo [1/2] Estimating depth...
"%DEPTH_PRO%" -i "%INPUT%" -o "%OUT_DIR%" --skip-display >> "%LOG%" 2>&1
if errorlevel 1 (
    echo  ERROR: depth-pro-run failed.
    echo ERROR: depth-pro-run failed. >> "%LOG%"
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
"%PYTHON%" "%TOOL_DIR%\npz_to_exr.py" -i "%NPZ%" --no-png >> "%LOG%" 2>&1
if errorlevel 1 (
    echo  ERROR: npz_to_exr.py failed.
    echo ERROR: npz_to_exr.py failed. >> "%LOG%"
    set /a ERROR_COUNT+=1
    exit /b 1
)

echo  Done -- %EXR%
echo Done: %EXR% >> "%LOG%"
exit /b 0
