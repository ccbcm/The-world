$ErrorActionPreference='Stop'
$framework='C:\Windows\Microsoft.NET\Framework64\v4.0.30319'
$refs=@('System.dll','System.Core.dll','System.Drawing.dll','System.Windows.Forms.dll','System.Web.Extensions.dll','WPF\WindowsBase.dll','WPF\PresentationCore.dll','WPF\PresentationFramework.dll','System.Xaml.dll','WPF\WindowsFormsIntegration.dll')
$argsList=@('/nologo','/win32manifest:app.manifest','/target:winexe','/platform:x64','/optimize+','/out:CCBCMWallpaper.exe')
foreach($r in $refs){$argsList+='/reference:'+(Join-Path $framework $r)}
$argsList+='Player.cs'
$argsList+='VlcPlayer.cs'
& (Join-Path $framework 'csc.exe') @argsList
if($LASTEXITCODE -ne 0){throw 'Build failed'}
