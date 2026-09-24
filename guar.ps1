$ScriptDir = Split-Path -Parent $MyInvocation.MyCommand.Definition

function Find-Python {
    if (Get-Command python -ErrorAction SilentlyContinue) { return "python" }
    if (Get-Command py -ErrorAction SilentlyContinue) { return "py" }
    if (Get-Command python3 -ErrorAction SilentlyContinue) { return "python3" }
    return $null
}

$PythonCmd = Find-Python

if (-not $PythonCmd) {
    Write-Host "⚠️  [JOG] Máy tính chưa có Python. Đang tự động cài đặt Python 3..." -ForegroundColor Yellow
    if (Get-Command winget -ErrorAction SilentlyContinue) {
        Write-Host "👉 Đang cài đặt qua winget..." -ForegroundColor Cyan
        winget install Python.Python.3.12 --silent --accept-package-agreements --accept-source-agreements
    } else {
        Write-Host "👉 Đang tải bộ cài Python từ python.org..." -ForegroundColor Cyan
        $setupPath = "$env:TEMP\python_setup.exe"
        Invoke-WebRequest -Uri "https://www.python.org/ftp/python/3.12.3/python-3.12.3-amd64.exe" -OutFile $setupPath
        Start-Process $setupPath -ArgumentList "/quiet InstallAllUsers=0 PrependPath=1" -Wait
        Remove-Item $setupPath -ErrorAction SilentlyContinue
    }

    $pyDirs = @(
        "$env:LOCALAPPDATA\Programs\Python\Python312",
        "$env:LOCALAPPDATA\Programs\Python\Python312\Scripts"
    )
    foreach ($d in $pyDirs) {
        if (Test-Path $d) {
            $env:Path = "$d;$env:Path"
        }
    }

    $PythonCmd = Find-Python
    if (-not $PythonCmd) {
        Write-Host "❌ [LỖI] Cài đặt Python hoàn tất nhưng cần khởi động lại Terminal để nhận PATH." -ForegroundColor Red
        Write-Host "👉 Vui lòng mở lại Terminal và chạy lại '.\guar active'." -ForegroundColor Yellow
        exit 1
    }
    Write-Host "✅ Đã cài đặt Python thành công! Tiếp tục khởi chạy JOG..." -ForegroundColor Green
}

& $PythonCmd "$ScriptDir\guar.py" $args
exit $LASTEXITCODE
