"""Финальная заставка по скиллу: 4.5 c, полноэкранный градиент #3a4560 -> #141c33
с констелляцией, БЕЗ циферблата. Главный элемент - оранжевая плашка ПОДПИШИСЬ,
под ней капс-строки контекста. Печать CHAR 0.025. Вход zoom-in 1.12->1 + вспышка.
Прописная строка Pushkin не ставится: шрифта нет, fallback-курсивы запрещены.
"""
from PIL import Image, ImageDraw, ImageFont
import numpy as np, math, os

W,H=1080,1920; FPS=30; DUR=4.5; N=int(DUR*FPS)
F="fonts/"; ORANGE=(255,117,31)
CHAR=0.025
os.makedirs('finseq',exist_ok=True)

PLATE="КУРС"
CTX=["ПИШИ В КОММЕНТАРИЯХ","И Я ПРИШЛЮ ПРОГРАММУ"]

def fit(fp,t,tw,lo=20,hi=240):
    while lo<hi:
        m=(lo+hi+1)//2; f=ImageFont.truetype(F+fp,m); b=f.getbbox(t)
        if b[2]-b[0]<=tw: lo=m
        else: hi=m-1
    return ImageFont.truetype(F+fp,lo)

fpl=fit("Montserrat-700.ttf",PLATE,int(W*0.46))
fctx=ImageFont.truetype(F+"Montserrat-500.ttf",52)

rng=np.random.default_rng(9)
P=70
px=rng.uniform(0,W,P); py=rng.uniform(0,H,P)
pr=rng.uniform(2.0,5.5,P); pa=rng.uniform(0.15,0.6,P)
pvy=rng.uniform(-5,5,P); pph=rng.uniform(0,6.28,P)

def background():
    g=Image.new('RGB',(1,H))
    for y in range(H):
        f=y/H
        g.putpixel((0,y),(int(58+(20-58)*f),int(69+(28-69)*f),int(96+(51-96)*f)))
    return g.resize((W,H)).convert('RGBA')

BG=background()

def constellation(t):
    lay=Image.new('RGBA',(W,H),(0,0,0,0)); d=ImageDraw.Draw(lay)
    pts=[]
    for k in range(P):
        y=(py[k]+pvy[k]*t)%H
        pts.append((px[k],y,k))
    for i in range(P):
        for j in range(i+1,P):
            dx=pts[i][0]-pts[j][0]; dy=pts[i][1]-pts[j][1]
            dist=math.hypot(dx,dy)
            if dist<175:
                a=int(46*(1-dist/175))
                d.line([pts[i][0],pts[i][1],pts[j][0],pts[j][1]],fill=(255,255,255,a),width=1)
    for x,y,k in pts:
        a=int(255*pa[k]*(0.6+0.4*math.sin(pph[k]+t*1.6)))
        d.ellipse([x-pr[k],y-pr[k],x+pr[k],y+pr[k]],fill=(255,255,255,max(a,0)))
    return lay

# геометрия плашки
tmp=ImageDraw.Draw(Image.new('RGB',(8,8)))
bb=tmp.textbbox((0,0),PLATE,font=fpl)
pw,ph=bb[2]-bb[0]+120, bb[3]-bb[1]+76
PCY=820

for i in range(N):
    t=i/FPS
    fr=Image.alpha_composite(BG.copy(), constellation(t))
    d=ImageDraw.Draw(fr)

    n_pl=int(max(0,t-0.10)/CHAR)
    if n_pl>0:
        txt=PLATE[:min(n_pl,len(PLATE))]
        b=d.textbbox((0,0),txt,font=fpl)
        cw=b[2]-b[0]+120
        x0=(W-cw)//2; y0=PCY-ph//2
        ov=Image.new('RGBA',(W,H),(0,0,0,0)); od=ImageDraw.Draw(ov)
        od.rounded_rectangle([x0+7,y0+13,x0+cw+7,y0+ph+13],radius=24,fill=(12,18,38,110))
        fr=Image.alpha_composite(fr,ov); d=ImageDraw.Draw(fr)
        d.rounded_rectangle([x0,y0,x0+cw,y0+ph],radius=24,fill=ORANGE)
        d.text((x0+60-b[0], PCY-(b[3]-b[1])//2-b[1]),txt,font=fpl,fill=(255,255,255))

    base=0.10+len(PLATE)*CHAR+0.25
    cy=PCY+ph//2+120
    for li,line in enumerate(CTX):
        st=base+li*0.35
        n_c=int(max(0,t-st)/CHAR)
        if n_c<=0: break
        s=line[:min(n_c,len(line))]
        b=d.textbbox((0,0),s,font=fctx)
        d.text(((W-(b[2]-b[0]))//2-b[0], cy-b[1]),s,font=fctx,fill=(226,234,250))
        cy+=76

    # вход: zoom-in 1.12 -> 1 за 9 кадров + вспышка
    if i<9:
        z=1.12+(1.0-1.12)*(i/9)
        nw,nh=int(W*z),int(H*z)
        fr=fr.resize((nw,nh),Image.LANCZOS).crop(((nw-W)//2,(nh-H)//2,(nw-W)//2+W,(nh-H)//2+H))
    if i<4:
        fl=Image.new('RGBA',(W,H),(255,255,255,int(150*(1-i/4))))
        fr=Image.alpha_composite(fr,fl)
    fr.convert('RGB').save(f'finseq/{i:04d}.jpg',quality=95)
print(f"заставка: {N} кадров, {DUR} c, плашка {pw}x{ph} @ y={PCY}")
