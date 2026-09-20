$ErrorActionPreference='Stop'
$framework=Join-Path $env:WINDIR 'Microsoft.NET\Framework64\v4.0.30319'
$output=Join-Path $PSScriptRoot '..\..\downloads'
New-Item -ItemType Directory -Force -Path $output | Out-Null
& (Join-Path $framework 'csc.exe') /nologo /target:winexe /platform:x64 /optimize+ "/win32manifest:$PSScriptRoot\app.manifest" "/out:$output\CCBCM-Wallpaper-Setup.exe" "/reference:$framework\System.dll" "/reference:$framework\System.Core.dll" "/reference:$framework\System.Drawing.dll" "/reference:$framework\System.Windows.Forms.dll" "/reference:$framework\Microsoft.CSharp.dll" "/reference:$framework\System.IO.Compression.FileSystem.dll" "/reference:$framework\System.Web.Extensions.dll" "/resource:$PSScriptRoot\runtime.json,runtime" "/resource:$PSScriptRoot\CCBCMWallpaper.exe,player" "/resource:$PSScriptRoot\demo.mp4,demo" "$PSScriptRoot\Setup.cs"
if($LASTEXITCODE -ne 0){throw 'Installer build failed'}
