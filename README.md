# Codex AI 自动窗口切换工具

一个用于 Codex 的自动窗口切换工具：当 AI 开始生成时自动切到目标应用，遇到需要用户处理的事件时自动切回 Codex。

## 功能

- 监听 AI 请求状态（开始/完成）
- 监听用户审核、权限请求、错误事件
- 触发事件后自动切回 Codex
- 快捷键手动切回（默认 `Ctrl+Alt+C`）
- 支持多个目标应用配置

## 文件结构

- `main.py`：主程序入口和事件循环
- `window_manager.py`：窗口查找、切换、恢复
- `ai_monitor.py`：AI 状态轮询与事件分发
- `config_manager.py`：配置加载与管理
- `system_tray.py`：系统托盘（可选）
- `config.json`：示例配置
- `requirements.txt`：依赖

## 安装

```bash
python -m venv .venv
source .venv/bin/activate  # Windows 使用 .venv\Scripts\activate
pip install -r requirements.txt
```

## 运行

```bash
python main.py --config config.json
```

## 配置说明

以下位置可修改目标软件，均已使用 `# TARGET_APP_CONFIG` 标记：

- `config.json` 中 `target_apps`
- `config_manager.py` 中 `DEFAULT_CONFIG["target_apps"]`
- `main.py` 中目标应用选择逻辑

示例：

```json
"target_apps": [
  {"name": "Browser", "window_keyword": "Chrome"},
  {"name": "IDE", "window_keyword": "Code"}
]
```

## 事件触发回到 Codex

- AI 响应生成完毕
- 需要用户确认/审核代码
- 出现权限请求对话框
- API 调用错误
- 快捷键触发

## 兼容性

- Python 3.8+
- Windows / macOS / Linux（依赖窗口系统环境）
