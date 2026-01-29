param(
    [switch]$FrontendBuild,
    [switch]$BackendBuild
)

$ErrorActionPreference = "Stop"

$root = Split-Path -Parent $MyInvocation.MyCommand.Path

# Optional: set paths if not in PATH
# $env:CADDY_PATH="C:\Tools\caddy\caddy.exe"
# $env:NGROK_PATH="C:\Tools\ngrok\ngrok.exe"
# Optional: enable build steps
# $env:FRONTEND_BUILD="1"
# $env:BACKEND_BUILD="1"

$backendPort  = $env:BACKEND_PORT  ; if (-not $backendPort)  { $backendPort  = "8000" }
$frontendPort = $env:FRONTEND_PORT ; if (-not $frontendPort) { $frontendPort = "3000" }
$proxyPort    = $env:PROXY_PORT    ; if (-not $proxyPort)    { $proxyPort    = "4444" }

$caddyFile = $env:CADDYFILE_PATH
if (-not $caddyFile) { $caddyFile = Join-Path $root "Caddyfile" }

if (-not $env:CADDY_PATH) {
    $defaultCaddyPath = "C:\Tools\caddy\caddy.exe"
    if (Test-Path $defaultCaddyPath) {
        $env:CADDY_PATH = $defaultCaddyPath
    }
}

function Resolve-Boolean([string]$value) {
    if (-not $value) { return $false }
    switch ($value.ToLower()) {
        "1" { return $true }
        "true" { return $true }
        "yes" { return $true }
        "y" { return $true }
        default { return $false }
    }
}

$backendBuildEnabled = $BackendBuild.IsPresent -or (Resolve-Boolean $env:BACKEND_BUILD)
$frontendBuildEnabled = $FrontendBuild.IsPresent -or (Resolve-Boolean $env:FRONTEND_BUILD)

$backendReq = Join-Path $root "electronics_server_python\requirements.txt"
$backendStartCmd = "py -m uvicorn electronics_server_python.main:app --host 0.0.0.0 --port $backendPort"
$frontendStartCmd = "pnpm exec serve -s ./assets -p $frontendPort --cors"
$backendTitle = "sdk-electronics backend"
$frontendTitle = "sdk-electronics frontend"
$caddyTitle = "sdk-electronics caddy"
$ngrokTitle = "sdk-electronics ngrok"

function Wait-Port([int]$port, [string]$label, [int]$timeoutSeconds = 60) {
    $deadline = (Get-Date).AddSeconds($timeoutSeconds)
    while ((Get-Date) -lt $deadline) {
        if (Test-NetConnection -ComputerName "127.0.0.1" -Port $port -InformationLevel Quiet) {
            return $true
        }
        Start-Sleep -Seconds 1
    }
    Write-Host "Timeout waiting for $label on port $port." -ForegroundColor Yellow
    return $false
}

#$backendCmd = "cd `"$root`"; `$host.UI.RawUI.WindowTitle=`"$backendTitle`"; `$env:motherduck_token=`"eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJlbWFpbCI6ImhyQHhlZWwudGVjaCIsIm1kUmVnaW9uIjoiYXdzLXVzLWVhc3QtMSIsInNlc3Npb24iOiJoci54ZWVsLnRlY2giLCJwYXQiOiJnSUVKOUVPcHA4RnExOUx1NktKZUhwYk44Zk9aN0N1WV9VR0Y4djgteDFRIiwidXNlcklkIjoiODA3MDM5ZDMtMzA3Ny00ZGY1LWEyZTMtMTk4ZGYzMTMzMTNkIiwiaXNzIjoibWRfcGF0IiwiaHJlYWRPbmx5IjpmYWxzZSwiYXR0b2tlblR5cGUiOiJyZWFkX3dyaXRlIiwiaWF0IjoxNzY3NjEzMTUwfQ.Y4_OIRpyrcSelw3_XH0mVip71Ram7czigIrzK7pa9tQ`"; py -m pip install -r `"$backendReq`"; $backendStartCmd"

if ($frontendBuildEnabled) {
    $frontendCmd = "cd `"$root`"; `$host.UI.RawUI.WindowTitle=`"$frontendTitle`"; pnpm build; $frontendStartCmd"
} else {
    $frontendCmd = "cd `"$root`"; `$host.UI.RawUI.WindowTitle=`"$frontendTitle`"; $frontendStartCmd"
}

$caddyCmd    = "cd `"$root`"; `$host.UI.RawUI.WindowTitle=`"$caddyTitle`"; `"$env:CADDY_PATH`" run --config `"$caddyFile`""
$ngrokCmd    = "cd `"$root`"; `$host.UI.RawUI.WindowTitle=`"$ngrokTitle`"; `"$env:NGROK_PATH`" http http://localhost:$proxyPort"

# If CADDY_PATH / NGROK_PATH not set, use default commands.
if (-not $env:CADDY_PATH) { $caddyCmd = "cd `"$root`"; `$host.UI.RawUI.WindowTitle=`"$caddyTitle`"; caddy run --config `"$caddyFile`"" }
if (-not $env:NGROK_PATH) { $ngrokCmd = "cd `"$root`"; `$host.UI.RawUI.WindowTitle=`"$ngrokTitle`"; ngrok http http://localhost:$proxyPort" }

Start-Process powershell -ArgumentList "-NoExit","-Command",$backendCmd
Wait-Port -port $backendPort -label "backend"
Start-Process powershell -ArgumentList "-NoExit","-Command",$frontendCmd
Wait-Port -port $frontendPort -label "frontend"
Start-Process powershell -ArgumentList "-NoExit","-Command",$caddyCmd
Wait-Port -port $proxyPort -label "caddy"
Start-Process powershell -ArgumentList "-NoExit","-Command",$ngrokCmd

Write-Host "Aperte 4 finestre: backend, frontend, caddy, ngrok."
