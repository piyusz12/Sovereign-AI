@echo off
setlocal enabledelayedexpansion

echo [*] Building Sovereign C++ Fast Core (sovereign_core.dll)...

set BUILD_DIR=%~dp0..\cpp-core\build
if not exist "%BUILD_DIR%" mkdir "%BUILD_DIR%"

set GXX=C:\MinGW\bin\g++.exe
if not exist "%GXX%" (
    where g++ >nul 2>nul
    if %ERRORLEVEL% equ 0 (
        set GXX=g++
    ) else (
        echo [!] MinGW g++ compiler not found.
        exit /b 1
    )
)

echo [*] Using compiler: %GXX%
%GXX% -O3 -shared -std=c++14 -I "%~dp0..\cpp-core\include" ^
    "%~dp0..\cpp-core\src\Router.cpp" ^
    "%~dp0..\cpp-core\src\MemoryManager.cpp" ^
    "%~dp0..\cpp-core\src\SecurityFirewall.cpp" ^
    "%~dp0..\cpp-core\src\PromptManager.cpp" ^
    "%~dp0..\cpp-core\src\bindings.cpp" ^
    -o "%BUILD_DIR%\sovereign_core.dll" -Wl,--out-implib,"%BUILD_DIR%\libsovereign_core.a"

if %ERRORLEVEL% equ 0 (
    echo [+] Successfully compiled sovereign_core.dll in %BUILD_DIR%
) else (
    echo [!] Build failed with exit code %ERRORLEVEL%
    exit /b %ERRORLEVEL%
)
