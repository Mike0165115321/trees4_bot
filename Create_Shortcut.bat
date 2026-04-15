@echo off
setlocal
:: ตั้งค่าตัวแปร
set "TARGET_NAME=TreesBot_Dashboard.exe"
set "SHORTCUT_NAME=TreesBot Dashboard.lnk"
set "SCRIPT_DIR=%~dp0"
set "EXE_PATH=%SCRIPT_DIR%%TARGET_NAME%"
set "DESKTOP_DIR=%USERPROFILE%\Desktop"

echo Creating Desktop Shortcut...

:: สร้าง VBScript ชั่วคราวเพื่อสร้าง Shortcut
set "VBS_FILE=%temp%\create_shortcut.vbs"
(
echo Set oWS = WScript.CreateObject^("WScript.Shell"^)
echo sLinkFile = "%DESKTOP_DIR%\%SHORTCUT_NAME%"
echo Set oLink = oWS.CreateShortcut^(sLinkFile^)
echo oLink.TargetPath = "%EXE_PATH%"
echo oLink.WorkingDirectory = "%SCRIPT_DIR%"
echo oLink.IconLocation = "%EXE_PATH%,0"
echo oLink.Save
) > "%VBS_FILE%"

:: รัน VBScript
cscript //nologo "%VBS_FILE%"
del "%VBS_FILE%"

echo.
echo ======================================================
echo  ✨ Shortcut created on your Desktop!
echo ======================================================
echo.
pause
