@echo off
:loop
py -3.11 bot.py
timeout /t 10
goto loop
