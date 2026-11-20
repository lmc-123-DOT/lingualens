@echo off
chcp 65001 >nul
title 语镜 LinguaLens
cd /d "%~dp0"

set "PY="
if exist ".venv\Scripts\python.exe" set "PY=.venv\Scripts\python.exe"
if not defined PY (
  where py >nul 2>nul && set "PY=py -3"
)
if not defined PY (
  where python >nul 2>nul && set "PY=python"
)
if not defined PY (
  echo.
  echo 没有找到 Python。请先安装 Python 3.10+，或恢复项目里的 .venv。
  echo.
  pause
  exit /b 1
)

echo.
echo   语镜 LinguaLens 正在启动...
echo   浏览器会自动打开；关闭这个窗口即停止服务。
echo.
%PY% server.py --open
echo.
echo 服务已停止。
pause
