@echo off
setlocal

echo ============================================================
echo   Sovereign AI Workbench - Native C++ x64 Build System
echo ============================================================

set VCVARS="C:\Program Files (x86)\Microsoft Visual Studio\18\BuildTools\VC\Auxiliary\Build\vcvarsall.bat"

if not exist %VCVARS% (
    echo [ERROR] Visual Studio vcvarsall.bat not found
    exit /b 1
)

echo [*] Initializing 64-bit MSVC environment...
call %VCVARS% x64
if errorlevel 1 (
    echo [ERROR] Failed to initialize MSVC x64 environment.
    exit /b 1
)

set "ROOT_DIR=%~dp0"
set "BUILD_DIR=%ROOT_DIR%build"
set "SRC_DIR=%ROOT_DIR%src"
set "INC_DIR=%ROOT_DIR%include"

if not exist "%BUILD_DIR%" mkdir "%BUILD_DIR%"

echo [*] Compiling sovereign_core.dll with /O2 /arch:AVX2 /std:c++20...
cd /d "%BUILD_DIR%"

cl.exe /nologo /LD /MD /O2 /arch:AVX2 /std:c++20 /EHsc /W3 /I"%INC_DIR%" "%SRC_DIR%\Router.cpp" "%SRC_DIR%\MemoryManager.cpp" "%SRC_DIR%\PromptManager.cpp" "%SRC_DIR%\SecurityFirewall.cpp" "%SRC_DIR%\HardwareManager.cpp" "%SRC_DIR%\SandboxEnclave.cpp" "%SRC_DIR%\SimdVectorEngine.cpp" "%SRC_DIR%\FastScanner.cpp" "%SRC_DIR%\bindings.cpp" /link /OUT:"%BUILD_DIR%\sovereign_core.dll" dxgi.lib

if errorlevel 1 (
    echo [ERROR] Compilation failed!
    exit /b 1
)

echo [SUCCESS] sovereign_core.dll built successfully!
exit /b 0
