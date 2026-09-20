$ErrorActionPreference='Stop'
$version='3.0.23.1'
$source=Join-Path $env:TEMP "ccbcm-vlc-$version.nupkg"
$expected='70927AFA9AD34B77E7D9A5E6D02CAE099771F6EB3114DA18111A4B76F65B836F'
if(-not(Test-Path $source)){Invoke-WebRequest "https://api.nuget.org/v3-flatcontainer/videolan.libvlc.windows/$version/videolan.libvlc.windows.$version.nupkg" -OutFile $source}
if((Get-FileHash $source -Algorithm SHA256).Hash -ne $expected){throw 'Native dependency checksum mismatch'}
Add-Type -AssemblyName System.IO.Compression.FileSystem
$target=Join-Path $PSScriptRoot 'vlc'
New-Item -ItemType Directory -Force $target | Out-Null
$package=[IO.Compression.ZipFile]::OpenRead($source)
try{foreach($entry in $package.Entries){if($entry.FullName -match '^build/x64/(.+\.dll)$'){
 $relative=$Matches[1];$file=Join-Path $target $relative
 New-Item -ItemType Directory -Force (Split-Path $file) | Out-Null
 [IO.Compression.ZipFileExtensions]::ExtractToFile($entry,$file,$true)
}}}finally{$package.Dispose()}
$license=Join-Path $target 'COPYING.LIB'
Invoke-WebRequest 'https://raw.githubusercontent.com/videolan/vlc/3.0.23/COPYING.LIB' -OutFile $license
Copy-Item (Join-Path $PSScriptRoot 'VLC-NOTICE.txt') (Join-Path $target 'NOTICE.txt') -Force
$archive=Join-Path $env:TEMP ('ccbcm-vlc-'+[guid]::NewGuid().ToString('N')+'.zip')
[IO.Compression.ZipFile]::CreateFromDirectory($target,$archive,[IO.Compression.CompressionLevel]::Optimal,$false)
$out=Join-Path $PSScriptRoot '../../downloads/runtime'
New-Item -ItemType Directory -Force $out | Out-Null
$parts=@();$stream=[IO.File]::OpenRead($archive)
try{$buffer=New-Object byte[] (20MB);$n=0;while(($count=$stream.Read($buffer,0,$buffer.Length)) -gt 0){
 $name="vlc-$version-$n.bin";$file=Join-Path $out $name
 $part=[IO.File]::Create($file);try{$part.Write($buffer,0,$count)}finally{$part.Dispose()}
 $parts+=@{name=$name;size=$count;sha256=(Get-FileHash $file -Algorithm SHA256).Hash.ToLowerInvariant()};$n++
}}finally{$stream.Dispose()}
@{version=$version;parts=$parts}|ConvertTo-Json -Depth 4|Set-Content (Join-Path $PSScriptRoot 'runtime.json') -Encoding utf8
Write-Output "Packaged $($parts.Count) runtime segments."
