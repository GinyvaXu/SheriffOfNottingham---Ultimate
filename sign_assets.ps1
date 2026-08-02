# sign_assets.ps1 - Code-sign the game exe and installer.
#
# Why: Windows 11 "Smart App Control" (SAC) blocks unsigned executables from
# unknown publishers. Signing with a publicly trusted code-signing certificate
# (OV/EV cert, or Microsoft Azure Trusted Signing) removes that block.
#
# Prerequisites:
#   1) A code-signing certificate installed in the current user's certificate
#      store (or an Azure Trusted Signing setup - see -Azure below).
#   2) Windows SDK signtool.exe (find it in "C:\Program Files (x86)\Windows Kits\10\bin\<ver>\x64\signtool.exe").
#   3) Inno Setup ISCC.exe to rebuild the installer after signing the exe.
#
# Usage:
#   .\sign_assets.ps1 -Thumbprint "<CERT_SHA1_THUMBPRINT>"
#   .\sign_assets.ps1 -Thumbprint "<...>" -TimestampUrl "http://timestamp.digicert.com"
#   .\sign_assets.ps1 -Azure -KeyName "<azure-rsa-2023-...>" -CertificateName "<cert-profile>"
#   .\sign_assets.ps1 -SkipInstall          # sign dist exe only, keep existing installer
#
# What it does:
#   1. Sign dist\SheriffOfNottingham.exe (SHA-256 + timestamp).
#   2. Rebuild installer\SheriffOfNottingham-Setup-<ver>.exe with ISCC (unless -SkipInstall).
#   3. Sign the installer exe too (both must be signed, or SAC blocks the inner exe).
param(
    [string]$Thumbprint = $env:SIGN_CERT_THUMBPRINT,
    [string]$TimestampUrl = "http://timestamp.digicert.com",
    [switch]$SkipInstall,
    # Azure Trusted Signing mode
    [switch]$Azure,
    [string]$KeyName = $env:SIGN_AZURE_KEY,
    [string]$CertificateName = $env:SIGN_AZURE_CERT,
    [string]$Endpoint = $env:SIGN_AZURE_ENDPOINT
)
$ErrorActionPreference = "Stop"
Set-Location $PSScriptRoot

function Find-Signtool {
    $roots = @("$env:ProgramFiles(x86)\Windows Kits\10\bin", "$env:ProgramFiles\Windows Kits\10\bin")
    foreach ($r in $roots) {
        if (Test-Path $r) {
            $exe = Get-ChildItem $r -Recurse -Filter signtool.exe -ErrorAction SilentlyContinue |
                   Sort-Object { [version]$_.Directory.Name -replace '[^0-9.]','' } -Descending |
                   Select-Object -First 1
            if ($exe) { return $exe.FullName }
        }
    }
    $cmd = Get-Command signtool.exe -ErrorAction SilentlyContinue
    if ($cmd) { return $cmd.Source }
    throw "signtool.exe not found. Install the Windows SDK or add it to PATH."
}

$signtool = Find-Signtool
Write-Host "Using signtool: $signtool"

# ---- 1) sign the game exe ----
$exe = Join-Path $PSScriptRoot "dist\SheriffOfNottingham.exe"
if (-not (Test-Path $exe)) { throw "Not found: $exe - run PyInstaller first (??.bat or the spec)." }

if ($Azure) {
    if (-not $KeyName -or -not $CertificateName -or -not $Endpoint) {
        throw "Azure Trusted Signing needs -KeyName, -CertificateName and -Endpoint (or SIGN_AZURE_* env vars)."
    }
    $signArgs = @("sign", "/fd", "SHA256", "/tr", $TimestampUrl, "/td", "SHA256",
                  "/csp", "Microsoft Azure Code Signing",
                  "/k", "$KeyName|$CertificateName|$Endpoint", $exe)
} else {
    if (-not $Thumbprint) { throw "Provide -Thumbprint (or set SIGN_CERT_THUMBPRINT)." }
    $signArgs = @("sign", "/fd", "SHA256", "/tr", $TimestampUrl, "/td", "SHA256",
                  "/sha1", $Thumbprint, $exe)
}
Write-Host "Signing game exe..."
& $signtool $signArgs
if ($LASTEXITCODE -ne 0) { throw "signtool failed for $exe" }

# ---- 2) rebuild installer (so the signed exe is inside it) ----
if (-not $SkipInstall) {
    $iscc = "C:\Users\zhenl\InnoSetup6\ISCC.exe"
    if (-not (Test-Path $iscc)) { throw "ISCC.exe not found at $iscc" }
    Write-Host "Rebuilding installer..."
    & $iscc (Join-Path $PSScriptRoot "installer.iss") | Out-Null
    if ($LASTEXITCODE -ne 0) { throw "ISCC failed" }
}

# ---- 3) sign the installer exe ----
$setup = Get-ChildItem (Join-Path $PSScriptRoot "installer") -Filter "SheriffOfNottingham-Setup-*.exe" |
         Sort-Object LastWriteTime -Descending | Select-Object -First 1
if (-not $setup) { throw "Installer exe not found under installer\" }
if ($Azure) {
    $signArgs = @("sign", "/fd", "SHA256", "/tr", $TimestampUrl, "/td", "SHA256",
                  "/csp", "Microsoft Azure Code Signing",
                  "/k", "$KeyName|$CertificateName|$Endpoint", $setup.FullName)
} else {
    $signArgs = @("sign", "/fd", "SHA256", "/tr", $TimestampUrl, "/td", "SHA256",
                  "/sha1", $Thumbprint, $setup.FullName)
}
Write-Host "Signing installer: $($setup.Name)"
& $signtool $signArgs
if ($LASTEXITCODE -ne 0) { throw "signtool failed for installer" }

Write-Host ""
Write-Host "Done. Both files are signed:"
Write-Host "  $exe"
Write-Host "  $($setup.FullName)"
Write-Host "Verify with: & `"$signtool`" verify /pa /v $exe"
