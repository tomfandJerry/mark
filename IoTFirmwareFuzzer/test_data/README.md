# 测试数据目录

## 已下载的固件

- **openwrt-sample.bin**  
  OpenWrt 22.03.5（ramips/mt76x8，约 5.7MB），用于固件解包与模糊测试演示。

## 如何用本固件做一次测试

### 1. 存根模式（不依赖 QEMU/Binwalk）

在项目根目录执行：

```cmd
cd /d "f:\学习\学校\毕业设计\代码\IoTFirmwareFuzzer"
python main.py fuzz --no-qemu --protocol mqtt --timeout 30
```

或在 Web UI 中：勾选「存根模式」，协议选 MQTT，超时填 30，点击「开始测试」。

### 2. 使用固件文件（需 Binwalk 解包）

- **固件路径**：`test_data\openwrt-sample.bin`（或填写绝对路径）。
- 若本机已安装 **Binwalk**（如 WSL 中 `apt install binwalk`），可在配置中设置 `firmware.binwalk_path` 指向 `binwalk`，程序会自动解包并尝试定位目标程序。
- Windows 下若未装 Binwalk，可仍用**存根模式**测试流程，或先在 WSL/Linux 下解包，再在配置里指定「目标二进制」路径。

### 3. 使用 QEMU（需先安装并配置）

- 若已用 **winget** 安装 QEMU，安装完成后**重新打开** CMD/PowerShell，使 PATH 生效。
- 在 CMD 中执行：`"C:\Program Files\qemu\qemu-arm.exe" --version`（若路径不同，请改成你本机路径）。
- 在 `config/default_config.yaml` 中可设置：
  ```yaml
  emulation:
    qemu_user_path: "C:\\Program Files\\qemu\\qemu-arm.exe"
    architecture: "arm"
  ```
  这样无需把 QEMU 加入 PATH 也能用。

## 小结

| 项目       | 说明 |
|------------|------|
| 固件文件   | 已就绪：`test_data\openwrt-sample.bin` |
| 存根测试   | 可直接运行，无需 QEMU/Binwalk |
| Binwalk    | Windows 建议用 WSL 安装；或仅用存根/已解包目录 |
| QEMU       | winget 安装后需新开终端或配置上述路径 |
