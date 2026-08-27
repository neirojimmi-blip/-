"""Три стиля субтитров на одном отрезке: терминал, караоке, чип."""
from PIL import Image, ImageDraw, ImageFont
import os, re, math

W,H=1080,1920; FPS=30
F="fonts/"; ORANGE=(255,117,31); NAVY=(46,64,120)
Y=1560
KEY={"память","монтаж","claude","субтитрами","переходами","монтажом","нарезки",
     "crm","календарём","артефакты","excel","таблицы","презентации","курс"}

def load(a,b):
    out=[]
    for l in open('subs4.ass',encoding='utf-8'):
        if not l.startswith('Dialogue:'): continue
        p=l.split(',',8)
        def sec(ts):
            h,m,s=ts.split(':'); return int(h)*3600+int(m)*60+float(s)
        st,en=sec(p[1]),sec(p[2])
        if en<a or st>b: continue
        txt=re.sub(r'\{[^}]*\}','',p[8]).strip()
        out.append((st-a,en-a,txt))
    return out

fbig=ImageFont.truetype(F+"Montserrat-700.ttf",52)
fmed=ImageFont.truetype(F+"Montserrat-500.ttf",48)
flab=ImageFont.truetype(F+"Montserrat-700.ttf",40)

def plate(d,x0,y0,x1,y1,fill,r=24):
    d.rounded_rectangle([x0,y0,x1,y1],radius=r,fill=fill)

def render(style,segs,dur,outdir,label):
    os.makedirs(outdir,exist_ok=True)
    N=int(dur*FPS)
    for i in range(N):
        t=i/FPS
        im=Image.new('RGBA',(W,H),(0,0,0,0)); d=ImageDraw.Draw(im)
        # ярлык варианта
        lb=f"ВАРИАНТ {label}"
        b=d.textbbox((0,0),lb,font=flab)
        plate(d,(W-(b[2]-b[0]))//2-28,150,(W+(b[2]-b[0]))//2+28,150+b[3]-b[1]+34,ORANGE+(235,))
        d.text(((W-(b[2]-b[0]))//2-b[0],150+17-b[1]),lb,font=flab,fill=(255,255,255))

        cur=[s for s in segs if s[0]<=t<=s[1]]
        if cur:
            st,en,txt=cur[0]
            words=txt.split()
            if style=="terminal":
                prog=min((t-st)/0.20,1.0)
                shown=txt[:max(1,int(len(txt)*prog))]
                b=d.textbbox((0,0),shown,font=fmed)
                w=b[2]-b[0]
                plate(d,(W-w)//2-30,Y-16,(W+w)//2+44,Y+b[3]-b[1]+30,(10,16,40,215))
                d.text(((W-w)//2-b[0],Y-b[1]+7),shown,font=fmed,fill=(255,255,255))
                if int(t*2.6)%2==0:
                    cx=(W+w)//2+10
                    d.rectangle([cx,Y+2,cx+6,Y+50],fill=ORANGE)
            elif style=="karaoke":
                tot=d.textlength(txt,font=fbig)
                x=(W-tot)//2
                k=min(int((t-st)/max(en-st,.01)*len(words)),len(words)-1)
                for wi,wd in enumerate(words):
                    col=ORANGE if wi==k else (255,255,255)
                    for ox,oy in ((-3,0),(3,0),(0,-3),(0,3)):
                        d.text((x+ox,Y+oy),wd,font=fbig,fill=(8,12,30))
                    d.text((x,Y),wd,font=fbig,fill=col)
                    x+=d.textlength(wd+" ",font=fbig)
            else:  # chip
                pop=min((t-st)/0.14,1.0)
                sc=0.88+0.12*(1-(1-pop)**3)
                fs=max(int(fmed.size*sc),10)
                f2=ImageFont.truetype(F+"Montserrat-500.ttf",fs)
                tot=sum(d.textlength(w+" ",font=f2) for w in words)
                b=d.textbbox((0,0),txt,font=f2)
                plate(d,(W-tot)//2-34,Y-14,(W+tot)//2+18,Y+b[3]-b[1]+30,NAVY+(232,))
                x=(W-tot)//2
                for wd in words:
                    col=ORANGE if re.sub(r'\W','',wd.lower()) in KEY else (255,255,255)
                    d.text((x,Y-b[1]+8),wd,font=f2,fill=col)
                    x+=d.textlength(wd+" ",font=f2)
        im.save(f"{outdir}/{i:04d}.png")
    return N

A,B=12.0,17.0
segs=load(A,B)
print("реплик в отрезке:",len(segs))
for st,en,tx in segs: print(f"  {st:4.2f}-{en:4.2f}  {tx}")
for style,out,lab in [("terminal","sub_a","A — ТЕРМИНАЛ"),("karaoke","sub_b","B — КАРАОКЕ"),("chip","sub_c","C — ЧИП")]:
    n=render(style,segs,B-A,out,lab); print(out,n,"кадров")
