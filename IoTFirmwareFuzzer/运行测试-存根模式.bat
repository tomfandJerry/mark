@echo off
chcp 65001 >nul
cd /d "%~dp0"
echo 使用已下载的固件进行存根模式测试（不启动 QEMU）...
echo 固件: test_data\openwrt-sample.bin
echo.
python main.py fuzz --no-qemu --protocol mqtt --timeout 30
pause
