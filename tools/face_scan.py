"""Где в кадре лицо — чтобы зумы и плашки не били по нему."""
import cv2, numpy as np, sys

cap = cv2.VideoCapture(sys.argv[1])
fps = cap.get(cv2.CAP_PROP_FPS)
casc = cv2.CascadeClassifier(cv2.data.haarcascades + "haarcascade_frontalface_default.xml")
boxes, i = [], 0
while True:
    ok, fr = cap.read()
    if not ok:
        break
    if i % 15 == 0:
        g = cv2.cvtColor(fr, cv2.COLOR_BGR2GRAY)
        f = casc.detectMultiScale(g, 1.1, 6, minSize=(40, 40))
        for (x, y, w, h) in f:
            boxes.append((i / fps, x, y, w, h))
    i += 1
cap.release()
H = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT) or 1280)
print(f"кадров {i}, детекций {len(boxes)}")
if boxes:
    a = np.array([[b[1], b[2], b[3], b[4]] for b in boxes], float)
    cx = a[:, 0] + a[:, 2] / 2
    cy = a[:, 1] + a[:, 3] / 2
    print(f"центр лица x: медиана {np.median(cx):.0f}  ({np.median(cx)/720:.3f} ширины)")
    print(f"центр лица y: медиана {np.median(cy):.0f}  ({np.median(cy)/1280:.3f} высоты)")
    print(f"размер лица: {np.median(a[:,2]):.0f}x{np.median(a[:,3]):.0f}")
    print(f"низ лица y: {np.median(a[:,1]+a[:,3]):.0f}")
