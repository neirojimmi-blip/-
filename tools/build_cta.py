from PIL import Image, ImageDraw, ImageFont
import os, math, json
W,H=1080,1920; FPS=30; DUR=2.6; N=int(DUR*FPS)
F="fonts/"
theme=json.load(open('/root/.claude/uploads/7d93c517-e279-5632-8766-ab595629b472/3e1675b7-theme.json'))
ORANGE=tuple(int(theme['colors']['accent'][i:i+2],16) for i in (1,3,5))
RADIUS=theme['radius']
os.makedirs('ctaseq',exist_ok=True)
TXT="ПИШИ: КУРС"

def fit(fp,t,tw):
    lo,hi=20,220
    while lo<hi:
        m=(lo+hi+1)//2; f=ImageFont.truetype(F+fp,m); b=f.getbbox(t)
        if b[2]-b[0]<=tw: lo=m
        else: hi=m-1
    return ImageFont.truetype(F+fp,lo)

f=fit("Oswald-Bold.ttf",TXT,int(W*0.60))
tmp=ImageDraw.Draw(Image.new('RGB',(10,10)))
bb=tmp.textbbox((0,0),TXT,font=f)
tw,th=bb[2]-bb[0], bb[3]-bb[1]
padx,pady=58,34
pw,ph=tw+padx*2, th+pady*2
CY=1420                     # нижняя треть: заведомо ниже лица

def ease_out_back(x):
    c1,c3=1.70158,2.70158
    return 1+c3*(x-1)**3+c1*(x-1)**2

for i in range(N):
    t=i/FPS
    im=Image.new('RGBA',(W,H),(0,0,0,0)); d=ImageDraw.Draw(im)
    p=min(max(t/0.42,0),1)
    s=0.55+0.45*ease_out_back(p) if p<1 else 1.0
    a=int(255*min(p*1.6,1))
    cw,ch=int(pw*s),int(ph*s)
    x0,y0=(W-cw)//2, CY-ch//2
    # тень
    d.rounded_rectangle([x0+6,y0+12,x0+cw+6,y0+ch+12],radius=int(RADIUS*s),fill=(23,33,64,int(a*0.35)))
    d.rounded_rectangle([x0,y0,x0+cw,y0+ch],radius=int(RADIUS*s),fill=ORANGE+(a,))
    fs=max(int(f.size*s),8)
    ff=ImageFont.truetype(F+"Oswald-Bold.ttf",fs)
    b2=d.textbbox((0,0),TXT,font=ff)
    d.text((W//2-(b2[2]-b2[0])//2-b2[0], CY-(b2[3]-b2[1])//2-b2[1]),TXT,font=ff,fill=(255,255,255,a))
    # стрелка вниз под плашкой
    if p>0.6:
        aa=int(a*0.9); cx=W//2; ay=y0+ch+38
        d.polygon([(cx-26,ay),(cx+26,ay),(cx,ay+34)],fill=ORANGE+(aa,))
    im.save(f'ctaseq/{i:04d}.png')
print(f"CTA: {N} кадров, плашка {pw}x{ph}, центр y={CY}, шрифт {f.size}px")
