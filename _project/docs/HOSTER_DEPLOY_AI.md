# Hoster.by Deploy For AI

This file explains how to upload selected site files to hoster.by.

## Credentials

Credentials are stored outside the site tree:

`C:\Pass\hoster-ftp.env`

Do not copy the password into commits, chat summaries, or public files.

Expected keys:

```env
FTP_SERVER=vh154.hoster.by
FTP_USER=autoftp
FTP_PASSWORD=...
FTP_REMOTE_ROOT=www/public_html
FTP_DOMAIN=ms8at.by
```

## Upload Target

FTP root contains `www`, and live site files are under:

```text
www/public_html
```

Local relative paths must be preserved on upload. Example:

```text
ru/monoblock/monoblock.html -> www/public_html/ru/monoblock/monoblock.html
en/monoblock/monoblock.html -> www/public_html/en/monoblock/monoblock.html
```

## PowerShell Upload Pattern

Use this pattern for a prepared deploy folder that mirrors site-relative paths:

```powershell
$config = Get-Content 'C:\Pass\hoster-ftp.env' | Where-Object { $_ -match '=' } | ForEach-Object {
  $key, $value = $_ -split '=', 2
  [pscustomobject]@{ Key = $key.Trim(); Value = $value.Trim() }
} | Group-Object Key -AsHashTable -AsString

$deployRoot = 'Z:\Del\AutoAI\Upload_html\deploy-monoblock-20260603'
$deployRootFull = (Resolve-Path -LiteralPath $deployRoot).Path.TrimEnd('\')

$files = Get-ChildItem -LiteralPath $deployRootFull -Recurse -File | Sort-Object FullName
foreach ($file in $files) {
  $relative = $file.FullName.Substring($deployRootFull.Length + 1).Replace('\','/')
  $remotePath = $config.FTP_REMOTE_ROOT.Value.Trim('/') + '/' + $relative
  $encodedPath = ($remotePath.Split('/') | ForEach-Object { [System.Uri]::EscapeDataString($_) }) -join '/'
  $url = 'ftp://' + $config.FTP_SERVER.Value + '/' + $encodedPath

  curl.exe -4 -sS --connect-timeout 30 --max-time 300 --ftp-create-dirs `
    -u ($config.FTP_USER.Value + ':' + $config.FTP_PASSWORD.Value) `
    -T $file.FullName `
    $url

  if ($LASTEXITCODE -ne 0) {
    throw "FTP upload failed for $relative"
  }
}
```

## Current Monoblock Deploy Pack

Prepared folder:

```text
Z:\Del\AutoAI\Upload_html\deploy-monoblock-20260603
```

It contains:

```text
en/monoblock/index.html
en/monoblock/monoblock.html
ru/monoblock/index.html
ru/monoblock/monoblock.html
ru/monoblock/monoblock_main.png
ru/monoblock/monoblock_front.png
ru/monoblock/monoblock_up.png
ru/monoblock/monoblok (1).jpg
ru/monoblock/monoblok (2).jpg
ru/monoblock/certificate.pdf
ru/monoblock/warranty.pdf
```

## Notes

- Upload small targeted deploy folders, not the whole working tree.
- Keep site-relative folder structure inside deploy folders.
- If FTP times out on a large file, rerun the same command for that file.
- Before deploying, verify that changed image paths match the HTML.
