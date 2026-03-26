# CIL Anything (Root + Auto)

This tool is now in project root and designed for AI agent automation on unknown desktop apps.

## Main command

```bash
python cil_anything.py auto --app "C:\Program Files\IBM\SPSS\stats.exe" --name spss --window-title "IBM SPSS" --goal "open dataset and run" --json
```

Auto flow:
- launch app
- wait + retry window discovery
- snapshot UI elements
- save CIL profile
- generate action plan from goal
- execute plan

## Other commands

```bash
python cil_anything.py create-cil --app "C:\Program Files\IBM\SPSS\stats.exe" --name spss --window-title "IBM SPSS" --json
python cil_anything.py discover --window-title "IBM SPSS" --json
python cil_anything.py act --profile spss --action click --selector "OK" --json
python cil_anything.py act --profile spss --action set_text --selector "FileNameEdit" --value "C:\data\a.sav" --json
```

## Output for AI agent

- use `--json`
- profile path: `%USERPROFILE%\CILAnything\profiles\<name>.json`
- all commands return machine-readable JSON
