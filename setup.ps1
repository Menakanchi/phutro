# Cài môi trường cho carla-ped-bench (Windows). Chạy một lần:
#   powershell -ExecutionPolicy Bypass -File .\setup.ps1
# Không có Python 3.12 thì script tự tải và cài (chỉ cho tài khoản hiện tại, không cần quyền admin).
$ErrorActionPreference = 'Stop'
Set-Location -LiteralPath $PSScriptRoot

function Test-Py312([string]$exe) {
    if (-not $exe) { return $false }
    try { $out = & $exe --version 2>&1; return ($LASTEXITCODE -eq 0 -and "$out" -match 'Python 3\.12\.') } catch { return $false }
}

function Find-Py312 {
    try { $p = (& py -3.12 -c "import sys; print(sys.executable)" 2>$null); if ($LASTEXITCODE -eq 0 -and (Test-Py312 $p)) { return $p } } catch {}
    $candidates = @(
        (Join-Path $env:LOCALAPPDATA 'Programs\Python\Python312\python.exe'),
        (Join-Path $env:ProgramFiles 'Python312\python.exe'),
        'C:\Python312\python.exe'
    )
    try { $candidates += (Get-Command python -All -ErrorAction SilentlyContinue | ForEach-Object { $_.Source }) } catch {}
    foreach ($c in $candidates) { if ((Test-Path -LiteralPath $c) -and (Test-Py312 $c)) { return $c } }
    return $null
}

$python = Find-Py312
if (-not $python) {
    Write-Host 'Chưa có Python 3.12 — đang tải và cài (khoảng 25 MB, 1-3 phút)...'
    $installer = Join-Path $env:TEMP 'python-3.12.10-amd64.exe'
    $log = Join-Path $env:TEMP 'python-3.12.10-install.log'
    try {
        [Net.ServicePointManager]::SecurityProtocol = [Net.SecurityProtocolType]::Tls12
        Invoke-WebRequest -UseBasicParsing -Uri 'https://www.python.org/ftp/python/3.12.10/python-3.12.10-amd64.exe' -OutFile $installer
    } catch {
        Write-Host "[LỖI] Không tải được bộ cài Python: $($_.Exception.Message)" -ForegroundColor Red
        Write-Host '      Tải tay https://www.python.org/ftp/python/3.12.10/python-3.12.10-amd64.exe, chạy, tick "Add python.exe to PATH", rồi chạy lại setup.ps1.'
        exit 1
    }
    $p = Start-Process -FilePath $installer -ArgumentList '/passive', 'InstallAllUsers=0', 'PrependPath=1', 'Include_launcher=1', 'Include_test=0', "/log `"$log`"" -Wait -PassThru
    if ($p.ExitCode -ne 0) {
        Write-Host "[LỖI] Bộ cài Python thoát mã $($p.ExitCode). Nhật ký: $log" -ForegroundColor Red
        exit 1
    }
    $python = Find-Py312
    if (-not $python) {
        Write-Host "[LỖI] Đã chạy bộ cài nhưng vẫn không thấy Python 3.12. Nhật ký: $log" -ForegroundColor Red
        exit 1
    }
}
Write-Host "Python 3.12: $python"

if (-not (Test-Path '.venv\Scripts\python.exe')) {
    & $python -m venv .venv
    if ($LASTEXITCODE -ne 0) { Write-Host '[LỖI] Không tạo được .venv' -ForegroundColor Red; exit 1 }
}
& .\.venv\Scripts\python.exe -m pip install --upgrade pip --quiet
& .\.venv\Scripts\python.exe -m pip install -r requirements.txt --quiet
if ($LASTEXITCODE -ne 0) {
    Write-Host '[LỖI] pip install thất bại. Nếu lỗi ở gói carla: cài từ wheel trong thư mục CARLA:' -ForegroundColor Red
    Write-Host '      .venv\Scripts\pip install <CARLA>\PythonAPI\carla\dist\carla-0.9.16-cp312-cp312-win_amd64.whl'
    exit 1
}
& .\.venv\Scripts\python.exe -m pytest -q tests
if ($LASTEXITCODE -ne 0) { Write-Host '[LỖI] test công cụ không qua — báo lại người gửi.' -ForegroundColor Red; exit 1 }
Write-Host ''
Write-Host 'Cài xong. Bước tiếp theo: bật CarlaUE4.exe rồi chạy  .venv\Scripts\python bench.py check' -ForegroundColor Green
