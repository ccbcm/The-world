$ErrorActionPreference='Stop'
$target=Join-Path $env:LOCALAPPDATA 'Programs\CCBCMWallpaper'
New-Item -ItemType Directory -Force -Path $target | Out-Null
Copy-Item -LiteralPath (Join-Path $PSScriptRoot 'CCBCMWallpaper.exe') -Destination $target -Force
if(Test-Path (Join-Path $PSScriptRoot 'demo.mp4')) {
  Copy-Item -LiteralPath (Join-Path $PSScriptRoot 'demo.mp4') -Destination $target -Force
  [IO.File]::WriteAllText((Join-Path $target 'Blue.ccbwall'),'{"video":"demo.mp4"}')
}
$exe=Join-Path $target 'CCBCMWallpaper.exe'
$classes='HKCU:\Software\Classes'
New-Item -Path "$classes\CCBCM.Wallpaper\shell\open\command" -Force | Out-Null
Set-Item -Path "$classes\CCBCM.Wallpaper\shell\open\command" -Value ('"'+$exe+'" "%1"')
New-Item -Path "$classes\.ccbwall\OpenWithProgids" -Force | Out-Null
New-ItemProperty -Path "$classes\.ccbwall\OpenWithProgids" -Name 'CCBCM.Wallpaper' -Value '' -PropertyType String -Force | Out-Null
# Only claim an unassigned extension. Never change the MP4 association.
if(-not (Get-Item "$classes\.ccbwall").GetValue('')) { Set-Item "$classes\.ccbwall" -Value 'CCBCM.Wallpaper' }
$shell=New-Object -ComObject WScript.Shell
foreach($folder in @([Environment]::GetFolderPath('Desktop'),[Environment]::GetFolderPath('Programs'))) {
  $link=$shell.CreateShortcut((Join-Path $folder 'CCBCM 动态壁纸.lnk'))
  $link.TargetPath=$exe
  $link.Arguments='--settings'
  $link.WorkingDirectory=$target
  $link.Save()
}
Write-Host 'Installed. Open CCBCM Wallpaper from your desktop. Startup remains opt-in.'
