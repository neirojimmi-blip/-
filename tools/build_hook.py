from PIL import Image, ImageDraw, ImageFont, ImageFilter
import numpy as np, os, math, json

W,H=1080,1920; FPS=30; DUR=2.6; N=int(DUR*FPS)
F="fonts/"
theme=json.load(open('/root/.claude/uploads/7d93c517-e279-5632-8766-ab595629b472/3e1675b7-theme.json'))
ORANGE=tuple(int(theme['colors']['accent'][i:i+2],16) for i in (1,3,5))
os.makedirs('hookseq',exist_ok=True)

def fit(fontpath, text, target_w, lo=20, hi=260):
    while lo<hi:
        m=(lo+hi+1)//2
        f=ImageFont.truetype(fontpath,m)
        if ImageFont.truetype(fontpath,m).getbbox(text)[2]-f.getbbox(text)[0] <= target_w: lo=m
        else: hi=m-1
    return ImageFont.truetype(fontpath,lo)

HEAD="5 ФУНКЦИЙ CLAUDE"
SCRIPT="о которых зря молчат"
f_head=fit(F+"Oswald-Bold.ttf",HEAD,int(W*0.84))
f_scr =fit(F+"MarckFull.ttf",SCRIPT,int(W*0.88))

# ---- слой заголовка (белый капс) ----
head=Image.new('RGBA',(W,H),(0,0,0,0)); d=ImageDraw.Draw(head)
bb=d.textbbox((0,0),HEAD,font=f_head); hx=(W-(bb[2]-bb[0]))//2-bb[0]; hy=845-(bb[3]-bb[1])//2-bb[1]
for ox,oy in [(0,3),(3,0),(-3,0),(0,-3)]:
    d.text((hx+ox,hy+oy),HEAD,font=f_head,fill=(20,28,58,90))
d.text((hx,hy),HEAD,font=f_head,fill=(255,255,255,255))

# ---- слой рукописной строки (оранжевый) ----
scr=Image.new('RGBA',(W,H),(0,0,0,0)); d2=ImageDraw.Draw(scr)
bb2=d2.textbbox((0,0),SCRIPT,font=f_scr); sx=(W-(bb2[2]-bb2[0]))//2-bb2[0]; sy=1045-(bb2[3]-bb2[1])//2-bb2[1]
d2.text((sx+2,sy+3),SCRIPT,font=f_scr,fill=(20,28,58,80))
d2.text((sx,sy),SCRIPT,font=f_scr,fill=ORANGE+(255,))
scr_x0, scr_x1 = sx+bb2[0]-8, sx+bb2[2]+14

# ---- частицы ----
rng=np.random.default_rng(3)
P=95
px=rng.uniform(0,W,P); py=rng.uniform(0,H,P)
pr=rng.uniform(2.4,7.5,P); pa=rng.uniform(0.14,0.72,P)
pvy=rng.uniform(-7,7,P); pph=rng.uniform(0,6.28,P); pfr=rng.uniform(0.5,1.7,P)

def clock(img,t):
    d=ImageDraw.Draw(img); cx,cy,R=W//2,1496,112
    d.ellipse([cx-R,cy-R,cx+R,cy+R],outline=(255,255,255,70),width=3)
    for i in range(12):
        a=math.radians(i*30); r1=R-(20 if i%3==0 else 12)
        d.line([cx+r1*math.sin(a),cy-r1*math.cos(a),cx+(R-4)*math.sin(a),cy-(R-4)*math.cos(a)],
               fill=(255,255,255,95 if i%3==0 else 60),width=3 if i%3==0 else 2)
    ang=math.radians(118+62*(t/DUR))
    d.line([cx,cy,cx+(R-26)*math.sin(ang),cy-(R-26)*math.cos(ang)],fill=ORANGE+(230,),width=7)
    ang2=math.radians(30+150*(t/DUR))
    d.line([cx,cy,cx+(R-58)*math.sin(ang2),cy-(R-58)*math.cos(ang2)],fill=(255,255,255,190),width=6)
    d.ellipse([cx-7,cy-7,cx+7,cy+7],fill=(255,255,255,220))

def ease(x): return 1-(1-x)**3

for i in range(N):
    t=i/FPS
    fr=Image.new('RGBA',(W,H),(0,0,0,0))
    dd=ImageDraw.Draw(fr)
    for k in range(P):
        y=(py[k]+pvy[k]*t)%H
        a=int(255*pa[k]*(0.62+0.38*math.sin(pph[k]+t*pfr[k]*2.4)))
        r=pr[k]
        dd.ellipse([px[k]-r,y-r,px[k]+r,y+r],fill=(255,255,255,max(a,0)))
    clock(fr,t)
    # заголовок: появляется 0.15-0.55
    hp=min(max((t-0.15)/0.40,0),1)
    if hp>0:
        lay=head.copy()
        if hp<1:
            al=lay.split()[3].point(lambda v:int(v*ease(hp)))
            lay.putalpha(al)
        fr=Image.alpha_composite(fr,lay)
    # рукописная строка: прописывается 0.75-2.05 слева направо
    sp=min(max((t-0.75)/1.30,0),1)
    if sp>0:
        cut=int(scr_x0+(scr_x1-scr_x0)*sp)
        mask=Image.new('L',(W,H),0); ImageDraw.Draw(mask).rectangle([0,0,cut,H],fill=255)
        mask=mask.filter(ImageFilter.GaussianBlur(6))
        lay=scr.copy(); lay.putalpha(Image.composite(scr.split()[3],Image.new('L',(W,H),0),mask))
        fr=Image.alpha_composite(fr,lay)
    fr.save(f'hookseq/{i:04d}.png')
print("кадров:",N,"| заголовок",f_head.size,"px | рукопись",f_scr.size,"px | оранжевый",ORANGE)
