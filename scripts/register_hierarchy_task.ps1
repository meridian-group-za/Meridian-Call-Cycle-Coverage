# One-time setup: registers the hierarchy.json refresh as a Windows
# Scheduled Task. Run this once from an elevated or normal PowerShell prompt
# on Carin's machine (the task runs under her account, using her existing
# git credentials for the push).
#
# Runs every 15 minutes, all day (Carin, 2026-08-29: "can we not refresh as
# soon as any changes have been made" -- there's no real push notification
# for an OneDrive Excel edit, so frequent polling is the practical
# approximation). refresh_hierarchy.ps1 is a safe no-op -- no commit, no
# push -- whenever the Organogram/roster haven't actually changed, so
# running it this often costs nothing beyond one Excel read + one git fetch
# every 15 minutes.

$repoRoot = "C:\tmp\Meridian-Call-Cycle-Coverage"
$scriptPath = Join-Path $repoRoot "scripts\refresh_hierarchy.ps1"

$action = New-ScheduledTaskAction -Execute "powershell.exe" `
    -Argument "-NoProfile -ExecutionPolicy Bypass -File `"$scriptPath`""

$trigger = New-ScheduledTaskTrigger -Once -At (Get-Date) -RepetitionInterval (New-TimeSpan -Minutes 15) -RepetitionDuration (New-TimeSpan -Days 3650)

$settings = New-ScheduledTaskSettingsSet -StartWhenAvailable -DontStopOnIdleEnd

Register-ScheduledTask -TaskName "MeridianCallCycleCoverage-HierarchyRefresh" `
    -Action $action -Trigger $trigger -Settings $settings `
    -Description "Refreshes hierarchy.json for the Call Cycle Coverage dashboard every 15 minutes (auto-commits and pushes to main; no-ops if nothing changed)." `
    -Force

Write-Output "Scheduled task 'MeridianCallCycleCoverage-HierarchyRefresh' re-registered -- runs every 15 minutes."
