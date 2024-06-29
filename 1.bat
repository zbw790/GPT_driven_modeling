@echo off
SET BLENDER_PATH=D:\Blender\4.1\blender.exe
SET SCRIPT_PATH=D:\GPT_driven_modeling\main.py
SET UPDATE_SCRIPT_PATH=D:\GPT_driven_modeling\update_database.py

REM 首先运行更新数据库的脚本
python "%UPDATE_SCRIPT_PATH%"

REM 然后启动 Blender 和主脚本
"%BLENDER_PATH%" --python "%SCRIPT_PATH%"