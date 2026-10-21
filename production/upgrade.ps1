# Finishes the lip-sync for any segment still missing head/raw{i}.mp4, rebuilds the promo,
# checks it, and pushes it to the live site. Waits (retrying every 20 min) while the free
# Hugging Face GPU quota is empty.
$ErrorActionPreference = 'Stop'
Set-Location $PSScriptRoot
$py = '.\.venv\Scripts\python'

& $py -u make_head.py
if ($LASTEXITCODE -ne 0) { throw 'lip-sync failed' }
& $py -u build.py out
if ($LASTEXITCODE -ne 0) { throw 'build failed' }

$mp4 = 'out\blobrowser-promo.mp4'
$dur = [double](ffprobe -v error -show_entries format=duration -of csv=p=0 $mp4)
$size = (Get-Item $mp4).Length
$vol = (ffmpeg -hide_banner -i $mp4 -vn -af volumedetect -f null NUL 2>&1 | Select-String 'mean_volume: (-?[\d.]+)').Matches[0].Groups[1].Value
"check: duration=$dur size=$size mean_volume=$vol"
if ($dur -lt 65 -or $dur -gt 68) { throw "bad duration $dur" }
if ($size -ge 12MB) { throw "too large $size" }
if ([double]$vol -lt -30) { throw "audio too quiet $vol" }

Copy-Item $mp4 ..\media\blobrowser-promo.mp4 -Force
Set-Location ..
git add media/blobrowser-promo.mp4 production/head
git commit -qm "Promo video: full lip-synced presenter for all segments"
git push -q origin main
"UPGRADE PUSHED $(Get-Date -Format 'yyyy-MM-dd HH:mm')"
