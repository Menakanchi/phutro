# Cài môi trường cho carla-ped-bench (Windows). Chạy một lần:
#   powershell -ExecutionPolicy Bypass -File .\setup.ps1
$ErrorActionPreference = 'Stop'
Set-Location -LiteralPath $PSScriptRoot

$py = $null
try { $v = & py -3.12 --version 2>$null; if ($LASTEXITCODE -eq 0) { $py = @('py', '-3.12') } } catch {}
if (-not $py) {
    Write-Host '[LỖI] Không tìm thấy Python 3.12.' -ForegroundColor Red
    Write-Host '      Cài từ https://www.python.org/downloads/release/python-31210/ (tick "Add python.exe to PATH" và "py launcher"), rồi chạy lại setup.ps1.'
    exit 1
}
Write-Host "Python: $v"

if (-not (Test-Path '.venv\Scripts\python.exe')) {
    & $py[0] $py[1] -m venv .venv
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
