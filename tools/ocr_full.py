from PIL import Image
import numpy as np, subprocess, os, json
Y0,Y1=1395,1515
STEP=0.15; DUR=52.93
os.makedirs('ocr/seq',exist_ok=True)
subprocess.run(['ffmpeg','-y','-v','error','-i','reel_final.mp4','-vf',
                f'fps={1/STEP},crop=1080:{Y1-Y0}:0:{Y0}','ocr/seq/%04d.png'],check=True)
files=sorted(os.listdir('ocr/seq'))
rows=[]
for i,fn in enumerate(files):
    a=np.array(Image.open('ocr/seq/'+fn).convert('RGB')).astype(int)
    r,g,b=a[:,:,0],a[:,:,1],a[:,:,2]
    mask=((r>205)&(g>205)&(b>195))|((r>195)&(g>160)&(b<130))
    px=int(mask.sum())
    t=round(i*STEP,2)
    if px<1200: rows.append((t,'')); continue
    out=np.where(mask,0,255).astype(np.uint8)
    im=Image.fromarray(out).resize((out.shape[1]*2,out.shape[0]*2),Image.LANCZOS)
    im.save('ocr/_c.png')
    res=subprocess.run(['tesseract','ocr/_c.png','-','-l','rus','--psm','7'],capture_output=True,text=True)
    rows.append((t,' '.join(res.stdout.split())))
json.dump(rows,open('ocr_rows.json','w'),ensure_ascii=False)
print("кадров обработано:",len(rows))
