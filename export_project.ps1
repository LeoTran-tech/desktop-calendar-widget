$output = "project_dump.txt"

# Xóa file cũ nếu có
if (Test-Path $output) {
    Remove-Item $output
}

# Những folder không cần xuất
$excludeFolders = @(
    ".git",
    "__pycache__",
    ".venv",
    "venv",
    ".idea",
    ".vscode"
)

# Những loại file muốn lấy code
$textExtensions = @(
    ".py",
    ".json",
    ".txt",
    ".md",
    ".yml",
    ".yaml",
    ".toml",
    ".ini",
    ".css",
    ".html",
    ".js"
)

"DESKTOP CALENDAR PROJECT" | Out-File $output
"Generated: $(Get-Date)" | Out-File $output -Append
"" | Out-File $output -Append

# ============================
# PROJECT STRUCTURE
# ============================

"========================================" | Out-File $output -Append
"PROJECT STRUCTURE" | Out-File $output -Append
"========================================" | Out-File $output -Append
"" | Out-File $output -Append

Get-ChildItem -Recurse |
Where-Object {
    $path = $_.FullName

    -not ($excludeFolders | Where-Object {
        $path -match "\\$([regex]::Escape($_))(\\|$)"
    })
} |
ForEach-Object {
    $relative = $_.FullName.Substring((Get-Location).Path.Length + 1)

    if ($_.PSIsContainer) {
        "[DIR]  $relative"
    }
    else {
        "[FILE] $relative"
    }
} | Out-File $output -Append

# ============================
# FILE CONTENTS
# ============================

"" | Out-File $output -Append
"========================================" | Out-File $output -Append
"FILE CONTENTS" | Out-File $output -Append
"========================================" | Out-File $output -Append

Get-ChildItem -Recurse -File |
Where-Object {

    $path = $_.FullName
    $extension = $_.Extension.ToLower()

    ($textExtensions -contains $extension) -and

    -not ($excludeFolders | Where-Object {
        $path -match "\\$([regex]::Escape($_))(\\|$)"
    }) -and

    $_.Name -ne $output

} |
ForEach-Object {

    $relative = $_.FullName.Substring((Get-Location).Path.Length + 1)

    "" | Out-File $output -Append
    "========================================" | Out-File $output -Append
    "FILE: $relative" | Out-File $output -Append
    "========================================" | Out-File $output -Append
    "" | Out-File $output -Append

    Get-Content $_.FullName |
    Out-File $output -Append
}

Write-Host "Done: $output"