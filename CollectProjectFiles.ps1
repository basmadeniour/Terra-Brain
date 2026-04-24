# ===========================
# سكربت لجمع كل ملفات Python في ملف واحد
# ===========================

# تحديد مجلد المشروع الحالي
$ProjectPath = (Get-Location).Path
$OutputFile = Join-Path $ProjectPath "FullProjectCode.txt"

# حذف الملف القديم لو موجود
if (Test-Path $OutputFile) {
    Remove-Item -Path $OutputFile -Force
}

# البحث عن جميع ملفات .py داخل المشروع
Get-ChildItem -Path $ProjectPath -Recurse -Include *.py |
Sort-Object FullName |
ForEach-Object {
    $RelativePath = $_.FullName.Substring($ProjectPath.Length + 1)
    $fileHeader = "--- FILE: $RelativePath ---`n"
    $fileContent = Get-Content $_.FullName -Raw
    "$fileHeader$fileContent`n`n" | Out-File -Append $OutputFile -Encoding UTF8
}

# تأكيد وفتح الملف
if (Test-Path $OutputFile) {
    Write-Host "All Python files collected successfully in $OutputFile"
    Invoke-Item $OutputFile
} else {
    Write-Host "File was not created."
}
