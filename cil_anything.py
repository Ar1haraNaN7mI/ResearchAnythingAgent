#!/usr/bin/env python3
"""
CIL Anything for AI agents (Windows desktop apps).

Core flow:
1) discover unknown app UI
2) save CIL profile
3) execute actions to control the app
4) auto mode runs the full pipeline
"""

from __future__ import annotations

import argparse
import json
import subprocess
import time
from dataclasses import asdict, dataclass
from pathlib import Path


PROFILE_DIR = Path.home() / "CILAnything" / "profiles"


@dataclass
class CILProfile:
    name: str
    app_path: str
    window_title_hint: str
    generated_at_epoch: int
    elements: list[dict]


def sanitize_name(name: str) -> str:
    safe = "".join(ch for ch in name if ch.isalnum() or ch in ("-", "_", " "))
    safe = safe.strip().replace(" ", "_")
    return safe or "cil_app"


def print_out(payload: dict, as_json: bool) -> None:
    if as_json:
        print(json.dumps(payload, ensure_ascii=True))
        return
    for key, value in payload.items():
        print(f"{key}: {value}")


def run_powershell(script: str) -> subprocess.CompletedProcess:
    return subprocess.run(
        ["powershell", "-NoProfile", "-ExecutionPolicy", "Bypass", "-Command", script],
        capture_output=True,
        text=True,
        check=False,
    )


def discover_elements(window_title_hint: str, max_nodes: int = 200) -> list[dict]:
    ps_script = rf"""
Add-Type -AssemblyName UIAutomationClient
Add-Type -AssemblyName UIAutomationTypes

$hint = "{window_title_hint.replace('"', '""')}"
$root = [System.Windows.Automation.AutomationElement]::RootElement
$wins = $root.FindAll([System.Windows.Automation.TreeScope]::Children,
    [System.Windows.Automation.Condition]::TrueCondition)
$target = $null
foreach ($w in $wins) {{
    if ($w.Current.Name -like "*$hint*") {{ $target = $w; break }}
}}
if ($null -eq $target) {{
    Write-Output "[]"
    exit 0
}}

$desc = $target.FindAll([System.Windows.Automation.TreeScope]::Descendants,
    [System.Windows.Automation.Condition]::TrueCondition)
$items = @()
$count = [Math]::Min($desc.Count, {max_nodes})
for ($i = 0; $i -lt $count; $i++) {{
    $el = $desc.Item($i)
    $obj = [PSCustomObject]@{{
        name = $el.Current.Name
        automation_id = $el.Current.AutomationId
        class_name = $el.Current.ClassName
        control_type = $el.Current.ControlType.ProgrammaticName
    }}
    $items += $obj
}}
$items | ConvertTo-Json -Depth 4 -Compress
"""
    result = run_powershell(ps_script)
    if result.returncode != 0:
        raise RuntimeError(result.stderr.strip() or "discover failed")
    raw = result.stdout.strip() or "[]"
    data = json.loads(raw)
    if isinstance(data, dict):
        return [data]
    return data if isinstance(data, list) else []


def run_action(window_title_hint: str, action: str, selector_name: str, value: str = "") -> bool:
    ps_script = rf"""
Add-Type -AssemblyName UIAutomationClient
Add-Type -AssemblyName UIAutomationTypes

$hint = "{window_title_hint.replace('"', '""')}"
$selector = "{selector_name.replace('"', '""')}"
$value = "{value.replace('"', '""')}"
$root = [System.Windows.Automation.AutomationElement]::RootElement
$wins = $root.FindAll([System.Windows.Automation.TreeScope]::Children,
    [System.Windows.Automation.Condition]::TrueCondition)
$targetWindow = $null
foreach ($w in $wins) {{
    if ($w.Current.Name -like "*$hint*") {{ $targetWindow = $w; break }}
}}
if ($null -eq $targetWindow) {{ Write-Output "false"; exit 0 }}

$desc = $targetWindow.FindAll([System.Windows.Automation.TreeScope]::Descendants,
    [System.Windows.Automation.Condition]::TrueCondition)
$target = $null
foreach ($el in $desc) {{
    if ($el.Current.Name -eq $selector -or $el.Current.AutomationId -eq $selector) {{
        $target = $el
        break
    }}
}}
if ($null -eq $target) {{ Write-Output "false"; exit 0 }}

$ok = $false
if ("{action}" -eq "click") {{
    if ($target.TryGetCurrentPattern([System.Windows.Automation.InvokePattern]::Pattern, [ref]$p)) {{
        ([System.Windows.Automation.InvokePattern]$p).Invoke()
        $ok = $true
    }}
}} elseif ("{action}" -eq "set_text") {{
    if ($target.TryGetCurrentPattern([System.Windows.Automation.ValuePattern]::Pattern, [ref]$p2)) {{
        ([System.Windows.Automation.ValuePattern]$p2).SetValue($value)
        $ok = $true
    }}
}}
if ($ok) {{ Write-Output "true" }} else {{ Write-Output "false" }}
"""
    result = run_powershell(ps_script)
    if result.returncode != 0:
        raise RuntimeError(result.stderr.strip() or "action failed")
    return result.stdout.strip().lower() == "true"


def save_profile(profile: CILProfile) -> Path:
    PROFILE_DIR.mkdir(parents=True, exist_ok=True)
    path = PROFILE_DIR / f"{sanitize_name(profile.name)}.json"
    path.write_text(json.dumps(asdict(profile), indent=2), encoding="utf-8")
    return path


def load_profile(name_or_path: str) -> dict:
    p = Path(name_or_path)
    if p.exists():
        return json.loads(p.read_text(encoding="utf-8"))
    by_name = PROFILE_DIR / f"{sanitize_name(name_or_path)}.json"
    if not by_name.exists():
        raise FileNotFoundError(f"Profile not found: {name_or_path}")
    return json.loads(by_name.read_text(encoding="utf-8"))


def discover_with_retry(window_title: str, max_nodes: int, retries: int, interval_seconds: int) -> list[dict]:
    for _ in range(max(1, retries)):
        items = discover_elements(window_title, max_nodes=max_nodes)
        if items:
            return items
        time.sleep(max(1, interval_seconds))
    return []


def auto_plan(elements: list[dict], goal: str, text_value: str, max_actions: int) -> list[dict]:
    goal_l = goal.lower().strip()
    priority_keywords = []
    if "open" in goal_l or "import" in goal_l or "load" in goal_l:
        priority_keywords.extend(["open", "import", "load", "file"])
    if "save" in goal_l or "export" in goal_l:
        priority_keywords.extend(["save", "export"])
    if "run" in goal_l or "execute" in goal_l:
        priority_keywords.extend(["run", "execute", "start", "ok"])
    if not priority_keywords:
        priority_keywords = ["ok", "apply", "run", "open"]

    plan: list[dict] = []
    if text_value:
        for el in elements:
            ctype = str(el.get("control_type", "")).lower()
            if "edit" in ctype:
                selector = str(el.get("automation_id") or el.get("name") or "").strip()
                if selector:
                    plan.append({"action": "set_text", "selector": selector, "value": text_value})
                    break

    used = set()
    for kw in priority_keywords:
        for el in elements:
            name = str(el.get("name", "")).strip()
            auto_id = str(el.get("automation_id", "")).strip()
            ctype = str(el.get("control_type", "")).lower()
            text = f"{name} {auto_id}".lower()
            if kw in text and ("button" in ctype or "menuitem" in ctype or "hyperlink" in ctype):
                selector = auto_id or name
                if selector and selector not in used:
                    used.add(selector)
                    plan.append({"action": "click", "selector": selector, "value": ""})
                    if len(plan) >= max(1, max_actions):
                        return plan
    if not plan:
        for el in elements:
            name = str(el.get("name", "")).strip()
            auto_id = str(el.get("automation_id", "")).strip()
            ctype = str(el.get("control_type", "")).lower()
            if "button" in ctype:
                selector = auto_id or name
                if selector:
                    plan.append({"action": "click", "selector": selector, "value": ""})
                    break
    return plan[: max(1, max_actions)]


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="CIL Anything for AI agents")
    sub = parser.add_subparsers(dest="command")

    discover = sub.add_parser("discover", help="Discover UI elements")
    discover.add_argument("--window-title", required=True)
    discover.add_argument("--max-nodes", type=int, default=200)
    discover.add_argument("--json", action="store_true")

    create_cil = sub.add_parser("create-cil", help="Launch app and create CIL profile")
    create_cil.add_argument("--app", required=True)
    create_cil.add_argument("--name", required=True)
    create_cil.add_argument("--window-title", required=True)
    create_cil.add_argument("--wait-seconds", type=int, default=6)
    create_cil.add_argument("--retries", type=int, default=5)
    create_cil.add_argument("--interval-seconds", type=int, default=2)
    create_cil.add_argument("--max-nodes", type=int, default=200)
    create_cil.add_argument("--json", action="store_true")

    act = sub.add_parser("act", help="Execute one action on app window")
    act.add_argument("--profile", required=True)
    act.add_argument("--action", required=True, choices=["click", "set_text"])
    act.add_argument("--selector", required=True)
    act.add_argument("--value", default="")
    act.add_argument("--json", action="store_true")

    auto = sub.add_parser("auto", help="Fully automatic CIL pipeline")
    auto.add_argument("--app", required=True)
    auto.add_argument("--name", required=True)
    auto.add_argument("--window-title", required=True)
    auto.add_argument("--goal", default="open and run")
    auto.add_argument("--text", default="")
    auto.add_argument("--wait-seconds", type=int, default=6)
    auto.add_argument("--retries", type=int, default=6)
    auto.add_argument("--interval-seconds", type=int, default=2)
    auto.add_argument("--max-nodes", type=int, default=220)
    auto.add_argument("--max-actions", type=int, default=3)
    auto.add_argument("--json", action="store_true")

    return parser


def cli_mode(argv: list[str]) -> int:
    parser = build_parser()
    args = parser.parse_args(argv[1:])
    as_json = bool(getattr(args, "json", False))

    if not args.command:
        print_out({"ok": False, "error": "Missing command"}, as_json)
        return 2

    try:
        if args.command == "discover":
            items = discover_elements(args.window_title, max_nodes=max(1, args.max_nodes))
            print_out({"ok": True, "action": "discover", "count": len(items), "items": items}, as_json)
            return 0

        if args.command == "create-cil":
            app_path = Path(args.app).expanduser()
            if not app_path.exists():
                print_out({"ok": False, "error": "App path does not exist"}, as_json)
                return 1
            subprocess.Popen([str(app_path)], shell=True)
            time.sleep(max(1, args.wait_seconds))
            items = discover_with_retry(
                args.window_title,
                max_nodes=max(1, args.max_nodes),
                retries=max(1, args.retries),
                interval_seconds=max(1, args.interval_seconds),
            )
            profile = CILProfile(
                name=sanitize_name(args.name),
                app_path=str(app_path),
                window_title_hint=args.window_title,
                generated_at_epoch=int(time.time()),
                elements=items,
            )
            profile_path = save_profile(profile)
            print_out(
                {
                    "ok": True,
                    "action": "create-cil",
                    "profile_name": profile.name,
                    "profile_path": str(profile_path),
                    "elements_count": len(items),
                },
                as_json,
            )
            return 0

        if args.command == "act":
            profile = load_profile(args.profile)
            window_hint = str(profile.get("window_title_hint", "")).strip()
            if not window_hint:
                print_out({"ok": False, "error": "Profile missing window_title_hint"}, as_json)
                return 1
            ok = run_action(window_hint, args.action, args.selector, args.value)
            print_out(
                {"ok": ok, "action": "act", "requested_action": args.action, "selector": args.selector},
                as_json,
            )
            return 0 if ok else 1

        if args.command == "auto":
            app_path = Path(args.app).expanduser()
            if not app_path.exists():
                print_out({"ok": False, "error": "App path does not exist"}, as_json)
                return 1

            subprocess.Popen([str(app_path)], shell=True)
            time.sleep(max(1, args.wait_seconds))

            items = discover_with_retry(
                args.window_title,
                max_nodes=max(1, args.max_nodes),
                retries=max(1, args.retries),
                interval_seconds=max(1, args.interval_seconds),
            )
            profile = CILProfile(
                name=sanitize_name(args.name),
                app_path=str(app_path),
                window_title_hint=args.window_title,
                generated_at_epoch=int(time.time()),
                elements=items,
            )
            profile_path = save_profile(profile)

            plan = auto_plan(items, args.goal, args.text, max_actions=max(1, args.max_actions))
            executed = []
            for step in plan:
                ok = run_action(args.window_title, step["action"], step["selector"], step.get("value", ""))
                executed.append({**step, "ok": ok})

            print_out(
                {
                    "ok": True,
                    "action": "auto",
                    "profile_path": str(profile_path),
                    "elements_count": len(items),
                    "goal": args.goal,
                    "plan": plan,
                    "executed": executed,
                },
                as_json,
            )
            return 0

        print_out({"ok": False, "error": "Unknown command"}, as_json)
        return 2
    except Exception as exc:
        print_out({"ok": False, "error": f"{exc}"}, as_json)
        return 3


def main() -> int:
    return cli_mode(__import__("sys").argv)


if __name__ == "__main__":
    raise SystemExit(main())
