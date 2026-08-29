# Weekly refresh of hierarchy.json -- keeps the Regional Manager / General
# Manager / Head of Syndicated filters in sync as the roster changes (new
# reps/merchandisers added, people reassigned, or the Organogram itself
# updated -- e.g. Sanele Pato getting added after Carin flagged him missing,
# 2026-08-29). Rebuilds the rep-level base from National Reporting
# Hierarchy.xlsx (build_hierarchy_from_organogram.py), then reapplies the
# merchandiser -> rep walk on top (build_hierarchy.py); if that produced a
# real change, commits and pushes straight to main so the live GitHub Pages
# dashboard picks it up on its next load.
#
# Registered as a weekly Windows Scheduled Task (Carin, 2026-08-26) -- see
# scripts/register_hierarchy_task.ps1 for the one-time setup command.
#
# Run manually any time with: powershell -File scripts/refresh_hierarchy.ps1

$ErrorActionPreference = "Stop"
$repoRoot = Split-Path -Parent $PSScriptRoot
Set-Location $repoRoot

$logDir = Join-Path $repoRoot "logs"
if (-not (Test-Path $logDir)) { New-Item -ItemType Directory -Path $logDir | Out-Null }
$logFile = Join-Path $logDir "hierarchy_refresh.log"

function Log($msg) {
    $line = "$(Get-Date -Format 'yyyy-MM-dd HH:mm:ss')  $msg"
    Add-Content -Path $logFile -Value $line
    Write-Output $line
}

try {
    Log "=== hierarchy refresh starting ==="

    git fetch origin
    git rebase origin/main
    if (-not $?) { throw "git rebase failed -- resolve manually, refresh skipped" }

    $python = "C:\Users\CarinPillay\AppData\Local\Python\bin\python.exe"
    & $python scripts\build_hierarchy_from_organogram.py | Tee-Object -Variable organogramOutput
    $organogramOutput | ForEach-Object { Log $_ }
    & $python scripts\build_hierarchy.py | Tee-Object -Variable buildOutput
    $buildOutput | ForEach-Object { Log $_ }

    $diff = git status --porcelain hierarchy.json scripts\hierarchy_unmatched_reps.csv
    if (-not $diff) {
        Log "No change to hierarchy.json -- nothing to commit."
        exit 0
    }

    git add hierarchy.json scripts\hierarchy_unmatched_reps.csv
    git commit -m "Weekly hierarchy.json refresh (automated)

Rebuilt the rep-level base from National Reporting Hierarchy.xlsx and
re-derived merchandiser -> regional/general manager mappings from the
current Call Cycle Master roster via scripts/build_hierarchy_from_organogram.py
and scripts/build_hierarchy.py.

Co-Authored-By: Claude Sonnet 5 <noreply@anthropic.com>"

    git push origin main
    Log "hierarchy.json updated and pushed."
}
catch {
    Log "ERROR: $_"
    exit 1
}
