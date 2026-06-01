# AI Auto Window Switcher / AI 自动窗口切换工具

An automatic window switcher for multiple AI assistants: switches to a target app while AI is generating, then switches back to the corresponding AI window when user attention is required.

一个支持多个 AI 会话（如 Claude、Codex）的自动窗口切换工具：当 AI 开始生成时自动切到目标应用，遇到需要用户处理的事件时自动切回对应 AI 窗口。

## English Summary

This project supports multiple concurrent sessions and automatically switches from each AI window to a configured target app while that AI is generating, then switches back when generation finishes, user review is needed, permission is requested, an API error occurs, or a hotkey is pressed.

## 功能

- 监听 AI 请求状态（开始/完成）
- 监听用户审核、权限请求、错误事件
- 触发事件后自动切回对应 AI 窗口
- 快捷键手动切回（全局默认 `Ctrl+Alt+C`，会话快捷键 `Ctrl+Alt+1..9`）
- 支持多个会话、每个会话独立目标应用配置

## 文件结构

- `main.py`：主程序入口和多会话事件循环
- `ai_session.py`：单个会话的监控+窗口处理
- `session_manager.py`：多个会话生命周期管理
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

`config.json` 使用 `sessions` 数组配置多个 AI 会话，每个会话可独立设置窗口关键词、API 端点和目标应用。

示例（单会话旧格式仍兼容）：

```json
{
  "sessions": [
    {
      "name": "Claude",
      "enabled": true,
      "ai_window_keywords": ["Claude"],
      "api_endpoints": {
        "status": "http://127.0.0.1:8765/claude/status",
        "events": "http://127.0.0.1:8765/claude/events"
      },
      "target_apps": [
        {"name": "Browser", "window_keyword": "Chrome"}
      ]
    }
  ]
}
```

## 事件触发回到 AI 窗口

- AI 响应生成完毕
- 需要用户确认/审核代码
- 出现权限请求对话框
- API 调用错误
- 快捷键触发

## 兼容性

- Python 3.8+
- Windows / macOS / Linux（依赖窗口系统环境）
