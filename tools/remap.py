import json, re
old=json.load(open('edl.json'))['mainRanges']
merged=json.load(open('new_ranges.json'))
T_OLD, T_NEW = 1.1, 1.15
def build(rs,T):
    out=[];acc=0.0
    for a,b in rs: out.append((a,b,acc)); acc+=(b-a)/T
    return out,acc
om,odur=build([(r['from'],r['to']) for r in old],T_OLD)
nm,ndur=build([tuple(x) for x in merged],T_NEW)
def old2src(t):
    for a,b,c in om:
        d=(b-a)/T_OLD
        if t<=c+d+1e-9: return a+max(t-c,0)*T_OLD
    return om[-1][1]
def src2new(s):
    for a,b,c in nm:
        if s<=b+1e-9: return c+max(s-a,0)/T_NEW
    return ndur
def conv(t): return round(src2new(old2src(t)),2)

# читаем старые группы из subs.ass, переносим тайминги
txt=open('subs.ass',encoding='utf-8').read()
head,body=txt.split('[Events]')
fmt,*lines=[l for l in body.strip().split('\n')]
def parse(ts):
    h,m,s=ts.split(':'); return int(h)*3600+int(m)*60+float(s)
def fmt_ts(t):
    h=int(t//3600); m=int(t%3600//60); s=t%60
    return f"{h}:{m:02d}:{s:05.2f}"
ev=[]
for l in lines:
    if not l.startswith('Dialogue:'): continue
    p=l.split(',',8)
    ev.append([conv(parse(p[1])), conv(parse(p[2])), p[8]])

ORANGE=r"{\c&H1F75FF&}"; WHITE=r"{\c&HFFFFFF&}"
# восстановленные порядковые
ev.append([src2new(12.42), src2new(13.66), "ВО-ВТОРЫХ"])
ev.append([src2new(37.78), src2new(39.16), "В-ЧЕТВЁРТЫХ"])
# убираем дубли порядковых из прочих строк - они восстановлены отдельно
import re as _re
for e in ev[:-2]:
    e[2]=_re.sub(r'\s*(ВО-ВТОРЫХ|В-ЧЕТВЁРТЫХ|В-ЧЕТВЕРТЫХ)\s*',' ',e[2]).strip()
ev=[e for e in ev if e[2].strip()]
ev.sort(key=lambda e:e[0])
# убираем наложения
for i in range(len(ev)-1):
    if ev[i][1]>ev[i+1][0]: ev[i][1]=max(ev[i+1][0]-0.02, ev[i][0]+0.3)
out=[f"Dialogue: 0,{fmt_ts(a)},{fmt_ts(b)},Sub,,0,0,,{t}" for a,b,t in ev]
open('subs2.ass','w',encoding='utf-8').write(head+'[Events]\n'+fmt+'\n'+'\n'.join(out)+'\n')
print(f"итоговая длительность нарезки: {ndur:.2f} с")
print(f"субтитров: {len(ev)}")
for a,b,t in ev:
    if 'ВТОРЫХ' in t or 'ЧЕТВ' in t or 'ПЕРВЫХ' in t or 'ТРЕТЬ' in t or 'ПЯТЫХ' in t:
        print(f"  {a:6.2f}-{b:6.2f}  {t}")
json.dump({'ndur':ndur,'ranges':merged,'T':T_NEW},open('cut2.json','w'))
