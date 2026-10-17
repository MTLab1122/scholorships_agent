@echo off
schtasks /create /tn "ScholarshipIntelligenceAgent" /tr "\"%~dp0run_daily_agent.bat\"" /sc daily /st 07:00 /f
if %ERRORLEVEL% equ 0 (
    echo Task created successfully.
) else (
    echo Failed to create scheduled task.
)
