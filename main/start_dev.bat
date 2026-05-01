@echo off
setlocal

REM Controlled dev stack launcher:
REM - Starts backend on 5174 and frontend on 5173
REM - Keeps this terminal attached
REM - Ctrl+C stops both and releases ports

powershell -ExecutionPolicy Bypass -File "%~dp0scripts\dev_stack.ps1" -BackendPort 5174 -FrontendPort 5173
