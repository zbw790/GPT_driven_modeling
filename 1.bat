@echo off
SET BLENDER_PATH=D:\Blender\4.1\blender.exe
@REM SET SCRIPT_PATH=D:\GPT_driven_modeling\text_sender.py
SET SCRIPT_PATH=D:\GPT_driven_modeling\main.py

"%BLENDER_PATH%" --python "%SCRIPT_PATH%"