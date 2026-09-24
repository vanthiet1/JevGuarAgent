# =============================================================================
# guar.ps1 - Trình khởi chạy nhanh JevGuarAgent trên Windows PowerShell
# =============================================================================
$ScriptDir = Split-Path -Parent $MyInvocation.MyCommand.Definition

$PythonCmd = if (Get-Command python -ErrorAction SilentlyContinue) {
    "python"
} elseif (Get-Command py -ErrorAction SilentlyContinue) {
    "py"
} elseif (Get-Command python3 -ErrorAction SilentlyContinue) {
    "python3"
} else {
    $null
}

if (-not $PythonCmd) {
    Write-Host "❌ [LỖI] Không tìm thấy Python trên hệ thống! Vui lòng cài đặt Python 3 và thêm vào PATH." -ForegroundColor Red
    exit 1
}

& $PythonCmd "$ScriptDir\guar.py" $args
exit $LASTEXITCODE
