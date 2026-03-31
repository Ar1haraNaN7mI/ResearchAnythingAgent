# 知识库使用手册 · Knowledge base handbook

## 能做什么

- 把 **PDF / Markdown / 纯文本 / HTML** 加入本地索引，聊天走 LLM 时自动按当前问题做 **FTS 检索** 并注入上下文（可用 `KB_RETRIEVE_DISABLE=1` 关闭）。
- PDF 通过 **OpenDataLoader** 转 Markdown 再分块；需要本机 **Java 11+**。
- 网页上传的文件会落在 **`knowledge_base/github_sync/`**，便于你用 **`?sync` / `kb sync`** 提交到 GitHub（需显式开启环境变量，见下文）。

---

## 固定指令（聊天里输入）

| 指令 | 作用 |
|------|------|
| **`?upload`** | 显示上传说明；在 **本仓库自带的网页聊天** 里会 **自动打开文件选择框**（并提示 REST / CLI 方式）。 |
| **`?delete <n>`** | 删除列表中第 `n` 条来源的索引（与 `kb remove <n>` 相同；`n` 来自 `kb list`）。 |
| **`?sync`** | 将 `knowledge_base/github_sync/` **git add → commit → push**（需 `KNOWLEDGE_GIT_SYNC_ALLOW=1`）。 |

全角问号 **`？`** 与半角 **`?`** 等价（例如 `？upload`）。

---

## 网页上传（推荐）

1. 启动聊天应用后，在输入框上方使用 **「上传到知识库」** 按钮选择文件；或发送 **`?upload`** 触发同一文件选择。
2. 上传成功后，日志里会显示 `source_key` 与分块数量。
3. 支持类型与 `kb add` 一致：`.pdf` `.md` `.txt` `.html` `.htm` `.markdown`。

**REST（脚本 / 其他客户端）**

- `POST /api/knowledge/upload`
- `Content-Type: multipart/form-data`
- 字段名：**`file`**（二进制）
- 成功：`200` JSON `{"ok":true,"source_key":"files/...","chunks":123}`
- 失败：`4xx/5xx` JSON `{"detail":"..."}`

单文件大小默认上限 **50MB**（`KNOWLEDGE_UPLOAD_MAX_BYTES`）。

---

## 命令行（已有路径时）

```text
kb add D:\docs\paper.pdf
kb list
kb remove 1
kb search 关键词
kb clear
kb status
kb manual          ← 本手册
kb sync            ← 同 ?sync
```

---

## 同步到 GitHub

1. 网页上传的文件保存在 **`knowledge_base/github_sync/`**（仓库已配置为可跟踪该目录）。
2. 在 **仓库根目录 .env** 中设置：`KNOWLEDGE_GIT_SYNC_ALLOW=1`（仅在可信环境开启）。
3. 在聊天中发送 **`?sync`** 或 **`kb sync`**：会执行  
   `git add knowledge_base/github_sync/` → `git commit` → `git push`。  
4. 需已配置 `git remote` 与登录凭证（SSH 或 credential helper）。

**注意**：`kb sync` **不会**自动 `git add` `knowledge_base/files/`（该目录仍为仅本地副本）；若只用 CLI `kb add`，默认文件只在 `files/` 下，要用 Git 备份请自行复制到 `github_sync` 或使用网页上传。

---

## 环境变量摘要

| 变量 | 含义 |
|------|------|
| `KNOWLEDGE_BASE_DIR` | 知识库根目录（默认仓库下 `knowledge_base/`） |
| `KB_RETRIEVE_MAX_CHARS` | 每次 LLM 调用注入的最大字符数 |
| `KB_RETRIEVE_DISABLE=1` | 关闭检索注入 |
| `KNOWLEDGE_UPLOAD_MAX_BYTES` | 上传单文件最大字节 |
| `KNOWLEDGE_GIT_SYNC_ALLOW=1` | 允许 `?sync` / `kb sync` 执行 git 提交与推送 |

---

## 故障排除

- **PDF 失败**：检查 `java -version`，并确认已 `pip install opendataloader-pdf`。
- **上传 413 / too large**：调大 `KNOWLEDGE_UPLOAD_MAX_BYTES` 或换小文件。
- **sync 拒绝**：未设置 `KNOWLEDGE_GIT_SYNC_ALLOW=1`。
- **push 失败**：检查网络、`git remote -v`、分支名与权限。

更简技术说明见同目录 **`SKILL.md`**（`kb guide`）。
