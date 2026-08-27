"""Плашка с кодовым словом на живом кадре, в момент реплики."""
from PIL import Image, ImageDraw, ImageFont
import os
W,H=1080,1920; FPS=30; DUR=2.40; N=int(DUR*FPS)
F="fonts/"; ORANGE=(255,117,31); RADIUS=24
CY=1150
os.makedirs('ctaseq',exist_ok=True)
LEAD="ПИШИ В КОММЕНТАРИЯХ"
WORD="КУРС"
fw=ImageFont.truetype(F+"Montserrat-700.ttf",120)
fl=ImageFont.truetype(F+"Montserrat-500.ttf",42)
def eob(x):
    c1,c3=1.70158,2.70158
    return 1+c3*(x-1)**3+c1*(x-1)**2
for i in range(N):
    t=i/FPS
    im=Image.new('RGBA',(W,H),(0,0,0,0)); d=ImageDraw.Draw(im)
    p=min(t/0.34,1.0); s=0.6+0.4*eob(p) if p<1 else 1.0
    a=int(255*min(p*1.8,1))
    if t>DUR-0.25: a=int(a*max(0,(DUR-t)/0.25))
    # верхняя строка
    bl=d.textbbox((0,0),LEAD,font=fl)
    d.text(((W-(bl[2]-bl[0]))//2-bl[0]+2, CY-150-bl[1]+3),LEAD,font=fl,fill=(8,14,34,int(a*0.7)))
    d.text(((W-(bl[2]-bl[0]))//2-bl[0], CY-150-bl[1]),LEAD,font=fl,fill=(255,255,255,a))
    # плашка с кодовым словом
    fs=max(int(120*s),10)
    ff=ImageFont.truetype(F+"Montserrat-700.ttf",fs)
    b=d.textbbox((0,0),WORD,font=ff)
    pw,ph=(b[2]-b[0])+140, (b[3]-b[1])+76
    x0,y0=(W-pw)//2, CY-ph//2
    d.rounded_rectangle([x0+7,y0+13,x0+pw+7,y0+ph+13],radius=int(RADIUS*s),fill=(10,16,40,int(a*0.45)))
    d.rounded_rectangle([x0,y0,x0+pw,y0+ph],radius=int(RADIUS*s),fill=ORANGE+(a,))
    d.text((W//2-(b[2]-b[0])//2-b[0], CY-(b[3]-b[1])//2-b[1]),WORD,font=ff,fill=(255,255,255,a))
    if p>0.65:
        cx=W//2; ay=y0+ph+30
        d.polygon([(cx-28,ay),(cx+28,ay),(cx,ay+36)],fill=ORANGE+(int(a*0.92),))
    im.save(f'ctaseq/{i:04d}.png')
print(f"плашка кодового слова: {N} кадров, центр y={CY}")
