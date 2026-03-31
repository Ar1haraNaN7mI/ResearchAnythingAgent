# Research Anything — 项目文件详细说明

本文档描述仓库内**主要文件**的职责、依赖关系与运行时行为，便于维护与二次开发。  
（不含 `.git/objects` 等二进制对象；`.env` 不写入版本库。）

---

## 1. 项目由哪几部分组成

| 子系统 | 目录/入口 | 作用 |
|--------|-----------|------|
| **聊天智能体** | `research_agent/`、`run_research_chat.bat`、`python -m research_agent` | Web（FastAPI + WebSocket）或终端 REPL；统一调度训练、CIL、系统 shell、多后端 LLM。 |
| **CIL Anything** | 根目录 `cil_anything.py` | 面向 Windows 桌面应用的 UI 自动化（UIA + PowerShell）；可发现控件、生成 profile、执行 click/set_text 等。 |
| **Autoresearch** | `autoresearch/` | 独立 GPU 训练实验（nanochat 风格）：`prepare.py` 固定管线，`train.py` 为可迭代实验脚本。 |

三者在**配置层**通过根目录 `.env` 交汇（LLM 密钥等）；在**命令层**由 `dispatcher.py` 把自然语言/命令前缀路由到对应子进程或 API。

---

## 2. 运行时数据流（聊天智能体）

```
用户输入（WebSocket 或终端 stdin）
    → PriorityCommandBus.prepend_user()   # 用户消息永远插队优先
    → ResearchWorker 线程取出命令
    → dispatcher.parse_and_dispatch()
          ├─ web search / websearch → env_agent.run_websearch_display（ddgs）
          ├─ env setup <preset> → env_agent.run_env_setup（LLM 规划 + 执行 + 失败自修复）
          ├─ try_handle_os_command()      # shell / os / apt/winget… → 不调 LLM
          ├─ llm / claude → llm_client      # 按 LLM_PROVIDER 走 Claude/Ollama/Qwen
          ├─ cil … → executor.run_cil       # 仅 Windows
          ├─ uv … / train / prepare → executor
          └─ auto on|off → worker 内部状态
    → 日志经 broadcast 回 Web 或终端
```

- **取消当前任务**：新用户消息会调用 `ProcessRunner.cancel()`，终止正在跑的子进程。

---

## 3. 根目录 `research anything/`

### 3.1 配置与文档

| 文件 | 详细说明 |
|------|----------|
| **`.env`** | 本地唯一真相源：LLM（`LLM_PROVIDER`、各厂商 KEY）、Ollama 地址/模型、Qwen/DashScope 等。**已被 `.gitignore` 忽略**，勿提交。 |
| **`.env.example`** | 同上键名的**模板**（无密钥），供克隆仓库者复制为 `.env`。 |
| **`.gitignore`** | 忽略 `.env`、`__pycache__`、`dist/` 等，避免密钥与构建产物入库。 |
| **`RESEARCH_AGENT.md`** | 用户向文档：依赖安装、Web/终端启动、`LLM_PROVIDER` 与三家后端说明、聊天指令示例、GitHub 推送网络问题排查。 |
| **`CIL_ANYTHING.md`** | CIL 子命令说明（`discover`、`create-cil`、`auto`、`act` 等）与 profile 路径。 |
| **`FILES.md`** | 本索引（架构 + 文件级说明）。 |
| **`LICENSE`** | 仓库许可证文本（与上游 GitHub 合并时可能含 Apache 等）。 |

### 3.2 可执行入口与脚本

| 文件 | 详细说明 |
|------|----------|
| **`cil_anything.py`** | **CLI**：`argparse` 子命令 `discover`、`create-cil`、`auto`、`act`。依赖 Windows UI Automation（经 PowerShell 注入 .NET）。Profile 存 `%USERPROFILE%\CILAnything\profiles\`。非 Windows 上 `dispatcher` 会拦截 `cil` 并提示。 |
| **`run_cil_anything.bat`** | `cd` 到脚本目录后执行 `python cil_anything.py`（无参数时行为以 `cil_anything.py` 为准）。 |
| **`build_cil_exe.bat`** | 安装 PyInstaller 并对 `cil_anything.py` 做 `onefile` 打包，生成 `dist\CILAnything.exe`（路径相对脚本目录）。 |
| **`run_research_chat.bat`** | `pip install -r research_agent\requirements.txt` 后执行 `python -m research_agent`，弹出交互菜单（Web / 终端）。 |

---

## 4. `research_agent/` 包结构

### 4.1 入口与路径

| 文件 | 详细说明 |
|------|----------|
| **`__init__.py`** | 标记为包；可为空。 |
| **`__main__.py`** | **主入口**：无参数时打印菜单（1=Web，2=终端）；`--web` 仅起 uvicorn；`--terminal` / `-t` 仅跑 `terminal_ui.run_terminal_session()`。 |
| **`paths.py`** | 定义 `ROOT`（`research_agent` 的父目录）、`AUTORESEARCH_DIR`、`CIL_SCRIPT`（绝对路径），供 `executor` / CIL 调用使用。 |

### 4.2 运行时与并发

| 文件 | 详细说明 |
|------|----------|
| **`runtime.py`** | 单例 **`PriorityCommandBus`** + 全局 **`ResearchWorker`**；`start_worker(broadcast)` 幂等启动后台线程；`get_bus()` / `get_worker()` 供 `chat_app` websocket 与终端共用**同一队列与同一 worker**，避免双实例。 |
| **`priority_queue.py`** | **`PriorityCommandBus`**：`prepend_user(text)` 从队头插入（用户最新指令优先）；`append_auto_research()` 在队尾追加自动研究任务；`clear_auto_pending()` 清除仅自动任务。使用 `threading.Condition` 与 `deque` 保证线程安全。 |
| **`worker.py`** | **`ResearchWorker`** 线程：循环 `pop_next`；解析 `auto on/off`；其余交给 **`parse_and_dispatch`**；自动研究在每次 `train` 类任务结束后若仍 `auto` 且队列为空则再次 `append_auto_research`。`on_user_command_submitted()` 调用 **`executor.cancel()`** 打断当前子进程。 |

### 4.3 网络服务（Web UI）

| 文件 | 详细说明 |
|------|----------|
| **`chat_app.py`** | **FastAPI**：`startup` 时 `runtime.start_worker(_broadcast_threadsafe)`，将 worker 日志投递到 **asyncio** 事件循环，再向所有**已连接 WebSocket** 广播。路由：`GET /` → `static/index.html`；`GET /api/system` → JSON：`text`（`format_startup_paragraph`）、`llm`（`llm_config_summary`）。**WebSocket** `/ws`：首条消息为系统段落 + 连接提示；之后每条用户消息先回显 `[you]`，再 `prepend_user` + `cancel`。 |
| **`static/index.html`** | 单页：全屏 CSS 开屏（`#boot`）、主界面 `#app`、日志 `#log`、输入框；**WebSocket** 与后端同主机；**fetch `/api/system`** 在页头 `#os-runtime` 展示系统摘要前若干行；**`<details>`** 内嵌 Linux/Ubuntu/Windows 命令对照表；连接状态 **pill**（Live/Offline）。 |

### 4.4 终端 UI

| 文件 | 详细说明 |
|------|----------|
| **`terminal_ui.py`** | **`enable_terminal_colors()`**：Windows 下启用 VT 转义。**`run_boot_animation()`**：全屏 ANSI 进度条 + 边框（与网页开屏同主题）。**`run_terminal_session()`**：先动画 → **`format_startup_paragraph()`** → `runtime.start_worker` → `input("RA> ")` 循环；与 Web 共用同一 `runtime`。 |

### 4.5 命令解析与执行

| 文件 | 详细说明 |
|------|----------|
| **`dispatcher.py`** | 核心 **`parse_and_dispatch(text, runner)`** 返回 `(message, exit_code)`。顺序大致为：`stop` / `help` → **`web search`/`websearch`** → **`env setup`/`env_setup`** → **`try_handle_os_command`**（不经 LLM）→ **`llm`/`claude`**（`llm_code_assist`）→ **`cil`**（非 Windows 直接报错）→ **`uv`** → 关键词 **`prepare`/`train`** → 以 `--` 开头的 CIL 参数 → 否则未知命令。另有 **`parse_auto_toggle`** 供 worker 识别 `auto on/off`。**`_help_text()`** 为内嵌帮助字符串。 |
| **`executor.py`** | **`ProcessRunner`**：维护当前 **`Popen`**，支持 **`cancel()`**（terminate → kill）。**`run_uv` / `run_python` / `run_cil`**：`shell=False` 列表参数；**`run_uv_fallback_python`** 优先 `uv run`，失败则 `python`。**`run_shell` / `run_shell_capture`**：可选 **`cwd`**；捕获模式返回 **`(exit_code, full_output)`** 供 env 自修复循环；流式 stdout 到 broadcast。 |
| **`web_search.py`** | **`search_web` / `format_search_for_llm`**：依赖 **`ddgs`**（无需 API Key），为 **`env_agent`** 与聊天侧提供文档/报错关键词检索摘要。 |
| **`env_agent.py`** | **`run_env_setup`**：按预设 **`autoresearch` / `research_agent` / `all`** 读取清单文件，联网摘要 + **`llm_complete`** 生成 JSON shell 步骤，经 **`ProcessRunner.run_shell_capture`** 执行；失败时 **`_repair_command`**（含二次 **`format_search_for_llm`**）改写命令重试，直至成功或达 **`ENV_SETUP_STEP_ATTEMPTS`**。**`run_websearch_display`**：向用户返回检索列表。 |
| **`os_info.py`** | **`format_startup_paragraph()`**：Python 版本、`sys.platform`、Windows/Linux/macOS 发行版（读 `/etc/os-release`）、**`current_os_family()`**、**`llm_config_summary()`**；供 Web 首包与终端打印。 |
| **`os_shell.py`** | **`try_handle_os_command`**：若匹配则返回 `(str, int)`，否则返回 `None`。支持：`shell <cmd>`；`os win|linux|ubuntu <cmd>` + **`translate_for_current_os`**；**`infer_linux_windows_from_line`** 识别 `apt`/`winget`/`brew`/`ls` 等；本机与推断源一致时直接 **`run_shell`**。 |
| **`os_translate.py`** | 轻量 **跨 OS 字符串映射**（如 apt install → winget、winget → apt），非完备包管理器；无法映射时原样执行并可能失败。 |

### 4.6 大语言模型（多后端）

| 文件 | 详细说明 |
|------|----------|
| **`llm_settings.py`** | 从 `ROOT/.env` 加载（`dotenv`）。**`llm_provider()`**：显式 `LLM_PROVIDER` 或按「Anthropic 密钥 → Ollama 模型名 → Qwen 密钥」启发式默认。**`anthropic_*` / `ollama_*` / `qwen_*`** / **`max_output_tokens`** / **`llm_config_summary()`** / **`env_setup_step_attempts()`**（`ENV_SETUP_STEP_ATTEMPTS`）。 |
| **`llm_client.py`** | **`llm_complete` / `llm_code_assist`**：按 provider 分流到 Anthropic Messages、Ollama `POST /api/chat`（httpx）、DashScope **OpenAI 兼容**（`openai` SDK）。 |
| **`claude_client.py`** | 薄封装：**`claude_complete`** → **`llm_complete`**；保留旧导入路径。 |
| **`claude_settings.py`** | **`from research_agent.llm_settings import *`**，兼容旧代码 `import claude_settings`。 |

### 4.7 依赖清单

| 文件 | 详细说明 |
|------|----------|
| **`requirements.txt`** | 运行时：`fastapi`、`uvicorn`、`anthropic`、`python-dotenv`、`openai`、`httpx`、`ddgs` 等；与 `autoresearch` 的 PyTorch 环境**相互独立**（聊天智能体不强制 GPU）。 |

---

## 5. `autoresearch/` 训练子项目

| 文件 | 详细说明 |
|------|----------|
| **`README.md`** | 上游项目哲学：单文件 `train.py` 迭代、固定 5 分钟预算、`val_bpb` 指标、`uv` 工作流。 |
| **`program.md`** | 给 **AI 代理** 的分支、实验记录、results.tsv 约定等（人类可改）。 |
| **`prepare.py`** | 下载/缓存数据、BPE、**`evaluate_bpb`** 等；**训练脚本不应修改评测契约**（设计为代理只改 `train.py`）。 |
| **`train.py`** | **模型 + 优化器 + 训练循环**；实验迭代的主战场；由 `dispatcher` 通过 `uv run train.py` 或 `python train.py` 启动。 |
| **`pyproject.toml`** | 依赖与 `torch` 的 CUDA 源（`tool.uv`）；Python 版本下限。 |
| **`uv.lock`** | uv 锁定依赖版本。 |
| **`.python-version`** | 建议本地 pyenv/uv 使用的 Python 小版本。 |
| **`.gitignore`** | 子项目忽略规则（缓存、产物等）。 |
| **`analysis.ipynb`** | 离线分析 notebook。 |

若仓库中曾包含 **`progress.png`**（宣传图），属资源文件；若未跟踪则不出现在 Git 树中。

---

## 6. 与「官网」同步

远程仓库一般为 **GitHub**（见 `RESEARCH_AGENT.md` 内链接）。推送前请确认 `.env` 未被 `git add`；`FILES.md` 是否入库由团队策略决定。

---

## 7. 安全提示

- **`.env`** 含 API 密钥，勿截图、勿提交。
- **`shell` / `os`** 会执行本机命令，仅在可信环境使用。
- **CIL** 会启动外部进程并模拟 UI 操作，注意权限与隐私。

---

## 8. 文件依赖简图（逻辑）

```
__main__.py
  ├─ chat_app (uvicorn) ── runtime ── worker ── dispatcher ── executor / llm_client / os_shell
  └─ terminal_ui ──────────────────── runtime ──（同上）

dispatcher
  ├─ env_agent → web_search, llm_client, executor
  ├─ executor → paths (ROOT, AUTORESEARCH, CIL_SCRIPT)
  ├─ os_shell → os_translate, os_info(间接)
  └─ llm_client → llm_settings

cil_anything.py（独立 CLI，可被 executor 以子进程调用）
autoresearch/train.py / prepare.py（独立 uv 项目，由 executor 在 autoresearch 目录下启动）
```

---

*文档版本：与当前仓库结构一致；若增删模块请同步更新本文件。*
