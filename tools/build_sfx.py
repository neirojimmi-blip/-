"""Звук переходов: воздушный «вуш» и низкий удар.

Синтетические клики пользователь уже дважды браковала, поэтому здесь нет
ни щелчков, ни цифрового «тика»: только отфильтрованный шум с плавной
огибающей и мягкий низкочастотный толчок. Уровень заниженный — эффект
должен подчёркивать склейку, а не спорить с речью.
"""
import numpy as np
import wave

SR = 48000


def write(path, x):
    x = np.clip(x, -1, 1)
    with wave.open(path, "w") as w:
        w.setnchannels(1)
        w.setsampwidth(2)
        w.setframerate(SR)
        w.writeframes((x * 32767).astype("<i2").tobytes())


def sweep_noise(dur, f_lo, f_hi, rise=0.55):
    """Шум через однополюсный фильтр с плавающей частотой среза."""
    n = int(dur * SR)
    t = np.arange(n) / n
    rng = np.random.default_rng(11)
    x = rng.normal(0, 1, n)
    # частота среза идёт вверх и возвращается
    cur = f_lo + (f_hi - f_lo) * np.sin(np.pi * np.clip(t / rise, 0, 1) ** 0.8)
    a = 1 - np.exp(-2 * np.pi * cur / SR)
    y = np.empty(n)
    acc = 0.0
    for i in range(n):
        acc += a[i] * (x[i] - acc)
        y[i] = acc
    # убираем самый низ, чтобы не гудело
    hp = np.empty(n)
    acc2 = 0.0
    b = 1 - np.exp(-2 * np.pi * 160 / SR)
    for i in range(n):
        acc2 += b * (y[i] - acc2)
        hp[i] = y[i] - acc2
    return hp / (np.abs(hp).max() + 1e-9)


def env(n, attack, release, shape=1.8):
    t = np.arange(n) / n
    a = np.clip(t / attack, 0, 1) ** 0.7
    r = np.clip((1 - t) / release, 0, 1) ** shape
    return a * r


def whoosh(dur=0.40, gain=0.42):
    n = int(dur * SR)
    y = sweep_noise(dur, 300, 5200) * env(n, 0.35, 0.62)
    return y * gain


def whoosh_soft(dur=0.34, gain=0.30):
    n = int(dur * SR)
    y = sweep_noise(dur, 220, 2600) * env(n, 0.45, 0.70)
    return y * gain


def thump(dur=0.30, f0=78, gain=0.5):
    n = int(dur * SR)
    t = np.arange(n) / SR
    f = f0 * np.exp(-t * 7)
    ph = 2 * np.pi * np.cumsum(f) / SR
    y = np.sin(ph) * np.exp(-t * 11)
    return y * gain


def air(dur=0.55, gain=0.22):
    """Длинный выдох для входа полноэкранной вставки."""
    n = int(dur * SR)
    return sweep_noise(dur, 900, 6500, rise=0.4) * env(n, 0.22, 0.78, 2.4) * gain


def mix(*parts):
    n = max(len(p) for p in parts)
    out = np.zeros(n)
    for p in parts:
        out[:len(p)] += p
    return out / max(1.0, np.abs(out).max() / 0.95)


write("n3/sfx_in.wav", mix(whoosh(), thump()))          # вход вставки
write("n3/sfx_out.wav", mix(whoosh_soft(), thump(0.24, 64, 0.36)))  # уход вставки
write("n3/sfx_air.wav", air())                          # мягкий акцент на склейке
print("собрано: sfx_in, sfx_out, sfx_air")
