@echo off
echo ==============================================================================
echo Disabling Local Windows Task Scheduler Dependency
echo ==============================================================================
echo Scheduled automated execution has migrated to GitHub Actions in the cloud.
echo Removing local task 'ScholarshipIntelligenceAgent' to prevent duplicate emails...

schtasks /delete /tn "ScholarshipIntelligenceAgent" /f >nul 2>&1
if %ERRORLEVEL% equ 0 (
    echo [SUCCESS] Local scheduled task successfully deleted.
) else (
    echo [INFO] No active local scheduled task found (already deleted).
)
echo.
echo Daily pipeline is executed automatically in the cloud via GitHub Actions at 07:00 AM PKT.

