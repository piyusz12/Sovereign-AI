@echo off
setlocal enabledelayedexpansion

echo ============================================================
echo   Sovereign AI Workbench - Native C++ x64 Build System
echo ============================================================

set "ROOT_DIR=%~dp0"
set "BUILD_DIR=%ROOT_DIR%build"
set "SRC_DIR=%ROOT_DIR%src"
set "INC_DIR=%ROOT_DIR%include"

if not exist "%BUILD_DIR%" mkdir "%BUILD_DIR%"

:: 1. Check if cl.exe is already on PATH
where cl.exe >nul 2>&1
if not errorlevel 1 (
    echo [*] Found MSVC cl.exe on PATH.
    goto :compile_msvc
)

:: 2. Search for vcvarsall.bat via vswhere.exe
set "VSWHERE=%ProgramFiles(x86)%\Microsoft Visual Studio\Installer\vswhere.exe"
if exist "%VSWHERE%" (
    for /f "usebackq tokens=*" %%i in (`"%VSWHERE%" -latest -products * -requires Microsoft.VisualStudio.Component.VC.Tools.x86.x64 -property installationPath`) do (
        set "VS_PATH=%%i"
    )
    if defined VS_PATH (
        if exist "!VS_PATH!\VC\Auxiliary\Build\vcvarsall.bat" (
            set "VCVARS=!VS_PATH!\VC\Auxiliary\Build\vcvarsall.bat"
            goto :setup_msvc
        )
    )
)

:: 3. Probe common VS installation paths
for %%v in (2022 2019) do (
    for %%e in (BuildTools Community Professional Enterprise) do (
        for %%p in ("%ProgramFiles%\Microsoft Visual Studio\%%v\%%e" "%ProgramFiles(x86)%\Microsoft Visual Studio\%%v\%%e") do (
            if exist "%%~p\VC\Auxiliary\Build\vcvarsall.bat" (
                set "VCVARS=%%~p\VC\Auxiliary\Build\vcvarsall.bat"
                goto :setup_msvc
            )
        )
    )
)

:: 4. Check for clang++
where clang++.exe >nul 2>&1
if not errorlevel 1 (
    echo [*] Found Clang compiler. Compiling with clang++...
    cd /d "%BUILD_DIR%"
    clang++ -O3 -mavx2 -mfma -std=c++20 -shared -I"%INC_DIR%" "%SRC_DIR%\Router.cpp" "%SRC_DIR%\MemoryManager.cpp" "%SRC_DIR%\PromptManager.cpp" "%SRC_DIR%\SecurityFirewall.cpp" "%SRC_DIR%\HardwareManager.cpp" "%SRC_DIR%\SandboxEnclave.cpp" "%SRC_DIR%\SimdVectorEngine.cpp" "%SRC_DIR%\FastScanner.cpp" "%SRC_DIR%\bindings.cpp" -ldxgi -o "%BUILD_DIR%\sovereign_core.dll"
    if not errorlevel 1 (
        echo [SUCCESS] sovereign_core.dll built successfully with Clang!
        exit /b 0
    )
)

:: 5. Check for g++ (MinGW)
where g++.exe >nul 2>&1
if not errorlevel 1 (
    echo [*] Found MinGW g++ compiler. Compiling with g++...
    cd /d "%BUILD_DIR%"
    g++ -O3 -mavx2 -mfma -std=c++20 -shared -I"%INC_DIR%" "%SRC_DIR%\Router.cpp" "%SRC_DIR%\MemoryManager.cpp" "%SRC_DIR%\PromptManager.cpp" "%SRC_DIR%\SecurityFirewall.cpp" "%SRC_DIR%\HardwareManager.cpp" "%SRC_DIR%\SandboxEnclave.cpp" "%SRC_DIR%\SimdVectorEngine.cpp" "%SRC_DIR%\FastScanner.cpp" "%SRC_DIR%\bindings.cpp" -ldxgi -o "%BUILD_DIR%\sovereign_core.dll"
    if not errorlevel 1 (
        echo [SUCCESS] sovereign_core.dll built successfully with MinGW!
        exit /b 0
    )
)

echo [INFO] No C++ compiler (MSVC / Clang / MinGW) found on PATH or standard locations.
echo [INFO] The Python C-bridge automatically operates in native Windows ctypes mode:
echo        - Hardware: Direct DXGI GPU VRAM query via dxgi.dll
echo        - Sandboxing: Direct Win32 Job Object containment via kernel32.dll
echo        - Math/SIMD: Python vector engine
echo [INFO] To build sovereign_core.dll, install Visual Studio 2022 C++ Build Tools or Clang.
exit /b 0

:setup_msvc
echo [*] Initializing 64-bit MSVC environment from !VCVARS!...
call "!VCVARS!" x64
if errorlevel 1 (
    echo [ERROR] Failed to initialize MSVC x64 environment.
    exit /b 1
)

:compile_msvc
echo [*] Compiling sovereign_core.dll with /O2 /arch:AVX2 /std:c++20...
cd /d "%BUILD_DIR%"
cl.exe /nologo /LD /MD /O2 /arch:AVX2 /std:c++20 /EHsc /W3 /I"%INC_DIR%" "%SRC_DIR%\Router.cpp" "%SRC_DIR%\MemoryManager.cpp" "%SRC_DIR%\PromptManager.cpp" "%SRC_DIR%\SecurityFirewall.cpp" "%SRC_DIR%\HardwareManager.cpp" "%SRC_DIR%\SandboxEnclave.cpp" "%SRC_DIR%\SimdVectorEngine.cpp" "%SRC_DIR%\FastScanner.cpp" "%SRC_DIR%\bindings.cpp" /link /OUT:"%BUILD_DIR%\sovereign_core.dll" dxgi.lib

if errorlevel 1 (
    echo [ERROR] Compilation failed!
    exit /b 1
)

echo [SUCCESS] sovereign_core.dll built successfully with MSVC!
exit /b 0
