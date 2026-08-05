@echo off
set HF_HOME=%~dp0.hf_cache
set MODEL=large-v3

rem 解析 --model / -m 参数（其余参数原样传给 main.py）
call :parse_model %*

rem 检测 Whisper 模型缓存，缺失则自动下载
python ensure_model.py %MODEL%

python main.py %*
exit /b

:parse_model
if "%~1"=="" goto :eof
if "%~1"=="-m" set MODEL=%~2
if "%~1"=="--model" set MODEL=%~2
set "T=%~1"
if "%T:~0,9%"=="--model=" set MODEL=%T:~9%
shift
goto :parse_model
