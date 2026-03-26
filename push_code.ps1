# Commit (optional) and push the full repo to origin main.
# Usage:
#   .\push_code.ps1                    # commit all with auto message if dirty, then push
#   .\push_code.ps1 -Message "msg"     # commit with message if dirty, then push
#   .\push_code.ps1 -SkipCommit        # push only (no add/commit)

param(
    [string]$Message = "",
    [switch]$SkipCommit
)

$ErrorActionPreference = "Stop"
Set-Location $PSScriptRoot

git config http.version HTTP/1.1 2>$null
git config http.postBuffer 524288000 2>$null

if (-not $SkipCommit) {
    git add -A
    $dirty = git status --porcelain
    if ($dirty) {
        $commitMsg = if ($Message) { $Message } else { "chore: sync $(Get-Date -Format 'yyyy-MM-dd HH:mm:ss')" }
        git commit -m $commitMsg
        if ($LASTEXITCODE -ne 0) {
            Write-Error "git commit failed."
            exit 1
        }
    }
}

Write-Host "Pushing to origin main ..."
git push -u origin main
if ($LASTEXITCODE -ne 0) {
    Write-Host ""
    Write-Host "Push failed. If remote has other commits, run:"
    Write-Host "  git pull origin main --allow-unrelated-histories"
    Write-Host "  git push -u origin main"
    exit $LASTEXITCODE
}

Write-Host "Done."
exit 0
