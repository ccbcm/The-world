"""Rasterize the existing website mark into launcher/Windows icon sizes."""
from PIL import Image, ImageDraw
from pathlib import Path
import math
root = Path(__file__).resolve().parents[2]
size=1024
im=Image.new('RGBA',(size,size))
d=ImageDraw.Draw(im)
d.rounded_rectangle((0,0,size-1,size-1),radius=300,fill='#d3c2f7')
scale=23; origin=144
def point(x,y): return (origin+x*scale,origin+y*scale)
cx=21-math.sqrt(28)
d.line([point(cx+8*math.cos(math.radians(48.5904+i*(311.4096-48.5904)/240)),18+8*math.sin(math.radians(48.5904+i*(311.4096-48.5904)/240))) for i in range(241)],fill='#272034',width=4*scale,joint='curve')
for x,y in [(21,12),(21,24)]:
    px,py=point(x,y); r=2*scale;d.ellipse((px-r,py-r,px+r,py+r),fill='#272034')
d.polygon([point(x,y) for x,y in [(24,3),(26,8),(31,10),(26,12),(24,17),(22,12),(17,10),(22,8)]],fill='#272034')
brand=root/'gallery'/'brand';brand.mkdir(exist_ok=True)
im.resize((512,512),Image.Resampling.LANCZOS).save(brand/'ccbcm.png')
im.save(root/'authoring'/'wallpaper-player'/'ccbcm.ico',sizes=[(16,16),(24,24),(32,32),(48,48),(64,64),(128,128),(256,256)])
res=root/'mobile'/'android'/'app'/'src'/'main'/'res'
for density,n in [('mdpi',48),('hdpi',72),('xhdpi',96),('xxhdpi',144),('xxxhdpi',192)]:
    folder=res/('mipmap-'+density);folder.mkdir(exist_ok=True)
    im.resize((n,n),Image.Resampling.LANCZOS).save(folder/'ic_launcher.png')
print('Generated CCBCM icons')
