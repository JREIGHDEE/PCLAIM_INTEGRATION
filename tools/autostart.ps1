# Start PClaimAssist by itself every time you sign in to Windows, so the
# system is always running on http://127.0.0.1:5000/ and sign-in never
# fails because the backend wasn't started.
#
#   powershell -ExecutionPolicy Bypass -File tools\autostart.ps1          turn on
#   powershell -ExecutionPolicy Bypass -File tools\autostart.ps1 -Remove  turn off
#
# It puts a shortcut to "PClaimAssist.bat /background" in your Startup
# folder (shell:startup). That starts the database and the application,
# minimised, without opening the browser. Nothing else is changed; -Remove
# (or deleting the shortcut) undoes it.
param([switch]$Remove)

$startup = [Environment]::GetFolderPath('Startup')
$shortcut = Join-Path $startup 'PClaimAssist.lnk'
$launcher = Join-Path (Split-Path $PSScriptRoot -Parent) 'PClaimAssist.bat'

if ($Remove) {
    if (Test-Path $shortcut) {
        Remove-Item $shortcut
        Write-Host 'PClaimAssist will no longer start by itself when you sign in.'
    } else {
        Write-Host 'PClaimAssist was not set to start by itself.'
    }
    return
}

if (-not (Test-Path $launcher)) {
    Write-Error "PClaimAssist.bat not found at $launcher"
    exit 1
}

$shell = New-Object -ComObject WScript.Shell
$link = $shell.CreateShortcut($shortcut)
$link.TargetPath = $launcher
$link.Arguments = '/background'
$link.WorkingDirectory = Split-Path $launcher -Parent
$link.WindowStyle = 7  # minimised
$link.Description = 'Start PClaimAssist (database and application) at sign-in'
$link.Save()
Write-Host "PClaimAssist will now start by itself when you sign in ($shortcut)."
Write-Host 'Open it any time at http://127.0.0.1:5000/'
