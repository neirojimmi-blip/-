from PIL import Image
import numpy as np, subprocess, sys, os

Y0,Y1 = 1395, 1515

def binarize(png):
    a=np.array(Image.open(png).convert('RGB')).astype(int)
    band=a[Y0:Y1]
    r,g,b=band[:,:,0],band[:,:,1],band[:,:,2]
    white = (r>205)&(g>205)&(b>195)
    yellow= (r>195)&(g>160)&(b<130)
    mask = white|yellow
    out=np.where(mask,0,255).astype(np.uint8)
    im=Image.fromarray(out).resize((out.shape[1]*2,out.shape[0]*2), Image.LANCZOS)
    return im, mask.sum()

def ocr(im,tmp='ocr/_t.png'):
    im.save(tmp)
    r=subprocess.run(['tesseract',tmp,'-','-l','rus','--psm','7'],capture_output=True,text=True)
    return ' '.join(r.stdout.split())

if __name__=='__main__':
    for t in sys.argv[1:]:
        p=f'ocr/f{t}.png'
        subprocess.run(['ffmpeg','-y','-v','error','-ss',t,'-i','reel_final.mp4','-frames:v','1',p],check=True)
        im,px=binarize(p)
        print(f"{t}s  пикселей текста {px:6d}  ->  {ocr(im)!r}")
