import json, re, difflib

CLEAN = """5 функций CLAUDE о которых зря молчат
во-первых это память между чатами можно включить в настройках такую возможность
чтобы CLAUDE помнил все ваши привычки всё о вас и вашем бизнесе чтобы постоянно не повторять
во-вторых вы можете делать монтаж видеороликов прямо в CLAUDE
нет он не просто подскажет вам это сделать а отдаст готовый файл
уже с субтитрами переходами монтажом
также есть возможность нарезки большого видео на маленькие ролики
в-третьих вы можете подключить CLAUDE к любым сервисам
начиная от CRM заканчивая вашим календарём прямо в этих сервисах
готовые решения с CLAUDE артефакты EXCEL файлы презентации таблицы
это всё создаёт CLAUDE прямо в чате
и в-пятых это ИИ-агент в вашем браузере
сам заполняет файлы ходит по разным сайтам
выполняет за вас задачу настоящего ИИ-агента в интернете
все такие фишки я показываю на курсе CLAUDE от А до Я
пиши КУРС в комментариях расскажу подробности""".split()

KEY = {"память","монтаж","субтитрами","переходами","монтажом","нарезки","crm",
       "календарём","артефакты","excel","таблицы","презентации","ии-агент",
       "ии-агента","браузере","курс","claude"}

tl = json.load(open('word_timeline.json'))
def n(s): return re.sub(r'[^a-zа-яё0-9]','',s.lower())

# выравнивание: идём по таймлайну, для каждого чистого слова берём первое похожее
times=[]; p=0
for w in CLEAN:
    nw=n(w); best=None
    for j in range(p, min(p+14, len(tl))):
        r=difflib.SequenceMatcher(None, nw, n(tl[j][1])).ratio()
        if r>0.62 and (best is None or r>best[1]): best=(j,r)
    if best:
        times.append(tl[best[0]][0]); p=best[0]+1
    else:
        times.append(None)

# заполняем пропуски интерполяцией
known=[(i,t) for i,t in enumerate(times) if t is not None]
for i,t in enumerate(times):
    if t is None:
        pr=[k for k in known if k[0]<i]; nx=[k for k in known if k[0]>i]
        if pr and nx:
            (i0,t0),(i1,t1)=pr[-1],nx[0]
            times[i]=t0+(t1-t0)*(i-i0)/(i1-i0)
        elif pr: times[i]=pr[-1][1]+0.25
        else: times[i]=0.3
times=[round(max(t,0.0),2) for t in times]
for i in range(1,len(times)):
    if times[i]<=times[i-1]: times[i]=times[i-1]+0.12

# группы по 3 слова
groups=[]
for i in range(0,len(CLEAN),3):
    ws=CLEAN[i:i+3]; st=times[i]
    en=times[i+3] if i+3<len(times) else times[-1]+0.9
    if en-st<0.35: en=st+0.35
    groups.append((st,en,ws))
# стык без дыр короче 0.6 c
for i in range(len(groups)-1):
    st,en,ws=groups[i]; nst=groups[i+1][0]
    if nst-en < 0.6: groups[i]=(st,nst,ws)

def ts(t):
    h=int(t//3600); m=int(t%3600//60); s=t%60
    return f"{h}:{m:02d}:{s:05.2f}"

ORANGE=r"{\c&H1F75FF&}"; WHITE=r"{\c&HFFFFFF&}"
lines=[]
for st,en,ws in groups:
    parts=[]
    for w in ws:
        parts.append((ORANGE+w.upper()+WHITE) if n(w) in KEY else w.upper())
    lines.append(f"Dialogue: 0,{ts(st)},{ts(en)},Sub,,0,0,,{' '.join(parts)}")

header = """[Script Info]
ScriptType: v4.00+
PlayResX: 1080
PlayResY: 1920
WrapStyle: 2
ScaledBorderAndShadow: yes

[V4+ Styles]
Format: Name, Fontname, Fontsize, PrimaryColour, SecondaryColour, OutlineColour, BackColour, Bold, Italic, Underline, StrikeOut, ScaleX, ScaleY, Spacing, Angle, BorderStyle, Outline, Shadow, Alignment, MarginL, MarginR, MarginV, Encoding
Style: Sub,Montserrat,48,&H00FFFFFF,&H00FFFFFF,&H00000000,&H8C000000,-1,0,0,0,100,100,0,0,3,4,3,2,60,60,300,204

[Events]
Format: Layer, Start, End, Style, Name, MarginL, MarginR, Effect, Text
"""
open('subs.ass','w',encoding='utf-8').write(header+"\n".join(lines)+"\n")
print(f"субтитров: {len(groups)}, с {groups[0][0]} по {groups[-1][1]} с")
for g in groups[:6]: print(f"  {g[0]:5.2f}-{g[1]:5.2f}  {' '.join(g[2]).upper()}")
