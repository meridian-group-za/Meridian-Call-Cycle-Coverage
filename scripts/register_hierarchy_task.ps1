# One-time setup: registers the weekly hierarchy.json refresh as a Windows
# Scheduled Task. Run this once from an elevated or normal PowerShell prompt
# on Carin's machine (the task runs under her account, using her existing
# git credentials for the push).
#
# Runs every Monday at 06:30 -- ahead of the working week, after any weekend
# roster edits to the Call Cycle Master.

$repoRoot = "C:\tmp\Meridian-Call-Cycle-Coverage"
$scriptPath = Join-Path $repoRoot "scripts\refresh_hierarchy.ps1"

$action = New-ScheduledTaskAction -Execute "powershell.exe" `
    -Argument "-NoProfile -ExecutionPolicy Bypass -File `"$scriptPath`""

$trigger = New-ScheduledTaskTrigger -Weekly -DaysOfWeek Monday -At 6:30am

$settings = New-ScheduledTaskSettingsSet -StartWhenAvailable -DontStopOnIdleEnd

Register-ScheduledTask -TaskName "MeridianCallCycleCoverage-HierarchyRefresh" `
    -Action $action -Trigger $trigger -Settings $settings `
    -Description "Weekly refresh of hierarchy.json for the Call Cycle Coverage dashboard (auto-commits and pushes to main)." `
    -Force

Write-Output "Scheduled task 'MeridianCallCycleCoverage-HierarchyRefresh' registered -- runs Mondays at 06:30."
