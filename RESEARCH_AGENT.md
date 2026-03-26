# Research Anything — 启动指南与仓库说明

合并内容：本地如何启动（Web / 终端）、Claude 配置、聊天指令、以及推送到 GitHub 的排错。

---

## 环境与依赖

1. Python 3.10+（建议）。
2. 在项目根目录安装智能体依赖：
   ```bash
   pip install -r research_agent/requirements.txt
   ```
3. **autoresearch** 子项目使用 `uv` 时：在 `autoresearch` 目录执行 `uv sync`（见 `autoresearch/README.md`）。训练/准备数据需要 GPU 等环境按原项目说明。

---

## 启动方式

在**工作区根目录**（包含 `research_agent/` 与 `cil_anything.py` 的那一层）操作。

### 方式 A：批处理（会安装依赖后启动）

- 双击或运行：`run_research_chat.bat`

### 方式 B：命令行（推荐）

```bash
python -m research_agent
```

首次会出现**交互菜单**：

| 选项 | 说明 |
|------|------|
| **1**（默认） | **Web 界面**：浏览器打开 `http://127.0.0.1:8765`，带 HTML/CSS 开屏动画。 |
| **2** | **终端模式**：不打开浏览器；终端内先播放 **ANSI 炫酷加载**（与网页开屏同主题），再进入 `RA>` 命令行，逻辑与 Web 相同。 |

跳过菜单、直接指定模式：

```bash
python -m research_agent --web
python -m research_agent --terminal
python -m research_agent -t
```

---

## Claude API（可选）

1. 将 `.env.example` 复制为根目录下的 `.env`。
2. 在 `.env` 中填写 `ANTHROPIC_API_KEY`（见 [Anthropic Console](https://console.anthropic.com/)）。
3. 可选：`CLAUDE_MODEL`、`ANTHROPIC_BASE_URL`、`CLAUDE_MAX_TOKENS`。

在聊天板或终端里使用：`claude <你的提示词>`。

代码内调用：`research_agent.claude_client.claude_complete()`、`claude_code_assist()`。

---

## 聊天规则（Web 与终端通用）

- 新消息**永远优先**于后台自动研究队列。
- 发送新消息会**中断**当前正在跑的子进程。
- `auto on`：空闲时循环跑 `train.py`；`auto off`：停止自动排队。

### 指令示例

- `train` — 运行 `autoresearch/train.py`（优先 `uv run`，否则 `python`）
- `prepare` — 运行 `autoresearch/prepare.py`
- `cil discover --window-title "..." --json`
- `cil auto --app "C:\path\app.exe" --name x --window-title "..." --json`
- `stop` — 取消当前任务
- `help`

---

## 推送到 GitHub

远程仓库： [ResearchAnythingAgent](https://github.com/Ar1haraNaN7mI/ResearchAnythingAgent)

推送前本地检查：`git status` 应为 **clean**（`.env` 已被忽略，不会提交）。

若 `git push` 出现 **Connection was reset** 或 **Failed to connect**：

1. **尝试 HTTP/1.1**（部分网络环境下更稳）：
   ```bash
   git config http.version HTTP/1.1
   git config http.postBuffer 524288000
   git push -u origin main
   ```

2. **改用 SSH**（需先在 GitHub 配置 [SSH 密钥](https://docs.github.com/en/authentication/connecting-to-github-with-ssh)）：
   ```bash
   git remote set-url origin git@github.com:Ar1haraNaN7mI/ResearchAnythingAgent.git
   git push -u origin main
   ```

3. **VPN / 代理 / 防火墙**：确保能访问 `github.com:443`（HTTPS）或 SSH 的 `22` 端口。

4. **公司代理**（如需要）：
   ```bash
   git config --global http.proxy http://user:pass@proxy:port
   ```

若远程已有提交而本地被拒绝，可先合并再推送：

```bash
git pull origin main --allow-unrelated-histories
git push -u origin main
```

---

## 目录结构（简要）

| 路径 | 说明 |
|------|------|
| `autoresearch/` | LLM 训练实验（nanochat 风格） |
| `cil_anything.py` | Windows 桌面 CIL / UI 自动化工具 |
| `research_agent/` | 聊天服务、优先级队列、Worker、终端 UI |
