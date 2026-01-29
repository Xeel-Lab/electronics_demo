$ErrorActionPreference = "Stop"

$windowTitles = @(
    "sdk-electronics backend",
    "sdk-electronics frontend",
    "sdk-electronics caddy",
    "sdk-electronics ngrok"
)

$processes = @(
    "node.exe",
    "python.exe",
    "uvicorn.exe",
    "caddy.exe",
    "ngrok.exe"
)

foreach ($title in $windowTitles) {
    try {
        $windows = Get-Process | Where-Object { $_.MainWindowTitle -eq $title }
        foreach ($win in $windows) {
            $null = $win.CloseMainWindow()
        }
    } catch {
        # Ignore if window is not running.
    }
}

Start-Sleep -Milliseconds 500

foreach ($title in $windowTitles) {
    try {
        taskkill /FI "WINDOWTITLE eq $title" /F | Out-Null
    } catch {
        # Ignore if window is not running.
    }
}

foreach ($proc in $processes) {
    try {
        taskkill /IM $proc /F | Out-Null
    } catch {
        # Ignore if process is not running.
    }
}

Write-Host "Terminati: $($processes -join ', ')"
