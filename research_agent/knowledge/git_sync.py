from __future__ import annotations

import os
import subprocess

from research_agent.paths import ROOT, knowledge_base_dir


def knowledge_git_sync_allowed() -> bool:
    return os.environ.get("KNOWLEDGE_GIT_SYNC_ALLOW", "").strip().lower() in (
        "1",
        "true",
        "yes",
    )


def _run_git(args: list[str]) -> tuple[int, str]:
    r = subprocess.run(
        args,
        cwd=str(ROOT),
        capture_output=True,
        text=True,
        encoding="utf-8",
        errors="replace",
    )
    out = (r.stdout or "") + (r.stderr or "")
    return r.returncode, out


def run_knowledge_github_sync() -> tuple[str, int]:
    """
    git add knowledge_base/github_sync/, commit if needed, push.
    Requires KNOWLEDGE_GIT_SYNC_ALLOW=1 and a git repo with remote configured.
    """
    if not knowledge_git_sync_allowed():
        return (
            "Git sync disabled. Set KNOWLEDGE_GIT_SYNC_ALLOW=1 in .env after you understand "
            "that this will commit and push files under knowledge_base/github_sync/.\n"
            "Uploads from the web UI land there so they can be versioned.",
            1,
        )

    sync = knowledge_base_dir() / "github_sync"
    if not sync.is_dir():
        return ("knowledge_base/github_sync/ does not exist yet. Upload a file first.", 1)

    lines: list[str] = []
    rc, out = _run_git(["git", "add", "knowledge_base/github_sync/"])
    lines.append(f"git add → rc={rc}\n{out.strip()}")

    rc2, _ = _run_git(["git", "diff", "--cached", "--quiet"])
    if rc2 == 0:
        msg = "\n".join(lines) + "\nNothing staged to commit (no new or changed uploads)."
        return (msg, 0)

    rc3, out3 = _run_git(
        ["git", "commit", "-m", "chore: sync knowledge base uploads (github_sync)"]
    )
    lines.append(f"git commit → rc={rc3}\n{out3.strip()}")
    if rc3 != 0:
        return ("\n".join(lines), 1)

    rc4, out4 = _run_git(["git", "push"])
    lines.append(f"git push → rc={rc4}\n{out4.strip()}")
    return ("\n".join(lines), 0 if rc4 == 0 else 1)
