# PortKill

PortKill 是一个面向 Windows 开发者的轻量桌面工具：输入端口号，查询真实占用进程，安全结束进程，并再次扫描确认端口已经释放。

## 开发环境

- Windows 10 / 11 64 位
- Python 3.11+
- PySide6
- psutil
- pywin32
- PyInstaller

项目自带独立虚拟环境 `.venv`，不会修改系统 Python 环境。

## 运行

双击 `run.bat`，或在项目目录执行：

```powershell
py -3 -m venv .venv
.venv\Scripts\python.exe -m pip install -r requirements.txt
.venv\Scripts\python.exe main.py
```

也可以直接运行：

```powershell
python main.py
```

如果通过双击 `main.py` 启动，程序会自动切换到项目内的 `.venv`，避免使用系统 Python 或其他 Qt DLL。发布使用时建议直接打开 `dist\PortKill.exe`。

## 打包

执行 `build.bat`，生成单文件 `dist\PortKill.exe`。PyInstaller 使用 `--onefile --windowed`，发布版本不会弹出控制台窗口。

## 操作

- Enter：查询端口
- Ctrl + L：聚焦并选中端口输入框
- F5：重新查询
- Esc：清空当前结果
- 📌：窗口置顶

查询结果提供两个结束操作：优先使用“结束进程并释放端口”；如果进程无响应或用户明确需要立即释放，可确认后使用“强制释放端口”。两种操作都会重新扫描端口，不会直接假设释放成功。

PortKill 会优先展示 LISTEN 记录，并按 PID 去重。结束进程使用 `terminate()`，等待退出后重新扫描；只有用户明确确认后才使用强制结束。Windows 关键系统进程（如 PID 4、System、services.exe、lsass.exe）始终禁用结束操作。

当权限不足时，程序提供 UAC 管理员重启，并通过 `--port` 参数恢复当前端口、自动重新查询。

## 图标

界面使用 Lucide 的线性 SVG 图标，图标路径数据随程序本地打包，运行不依赖浏览器或网络。图标来源：[lucide.dev/icons](https://lucide.dev/icons/)，遵循 Lucide ISC License。
