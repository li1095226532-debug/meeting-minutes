@echo off
chcp 65001 >nul
echo ========================================
echo   会议纪要助手 - 环境安装
echo ========================================
echo.

:: 检查 Python
python --version >nul 2>&1
if %errorlevel% neq 0 (
    echo [错误] 未找到 Python，请先安装 Python 3.8+
    pause
    exit /b 1
)

:: 检查 Python 版本
python -c "import sys; sys.exit(0 if sys.version_info >= (3,8) else 1)" 2>nul
if %errorlevel% neq 0 (
    echo [错误] Python 版本过低，需要 3.8 以上
    pause
    exit /b 1
)

echo [1/3] 安装基础依赖...
python -m pip install --upgrade pip
python -m pip install fastapi uvicorn python-multipart python-dotenv anthropic
if %errorlevel% neq 0 (
    echo [警告] 部分依赖安装失败，请检查网络
)

echo.
echo [2/3] 安装语音转文字后端...
echo 请选择：
echo   1 - faster-whisper (推荐，需 Python 3.9+，GPU加速)
echo   2 - openai-whisper  (备选，支持 Python 3.8，CPU运行)
echo   3 - 跳过（使用 OpenAI API 云端转写）
set /p choice="请输入选项 (1/2/3): "

if "%choice%"=="1" (
    echo 正在安装 faster-whisper...
    python -m pip install faster-whisper
) else if "%choice%"=="2" (
    echo 正在安装 openai-whisper...
    python -m pip install openai-whisper
) else (
    echo 跳过本地模型安装，将使用 OpenAI Whisper API
    python -m pip install openai
)

echo.
echo [3/3] 配置环境变量...
if not exist ".env" (
    copy .env.example .env >nul
    echo 已创建 .env 文件，请编辑填入你的 API Key
) else (
    echo .env 文件已存在，跳过
)

echo.
echo ========================================
echo   安装完成！
echo   1. 编辑 .env 文件，填入 ANTHROPIC_API_KEY
echo   2. 运行: python server.py
echo   3. 打开浏览器访问: http://localhost:8866
echo ========================================
pause
