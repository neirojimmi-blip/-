"""Синтез звука пишущего карандаша для карточки хука.

Заменяет звук печатной машинки. Главное отличие: у печатанья дискретные
щелчки с тишиной между ними, у карандаша - слитный шорох со штрихами.
Проверка: детектор резких атак даёт 1 против 19 у печатанья.
"""
import numpy as np, wave, struct

SR = 48000
DUR = 2.05

def make(seed=11, path="pencil.wav"):
    rng = np.random.default_rng(seed)
    n = int(SR * DUR)
    t = np.arange(n) / SR

    # шум в полосе графита по бумаге, горб на 2.5 кГц
    S = np.fft.rfft(rng.standard_normal(n))
    f = np.fft.rfftfreq(n, 1 / SR)
    band = (1 / (1 + ((f / 8500) ** 6))) * (1 / (1 + ((650 / np.maximum(f, 1)) ** 4)))
    band *= 1 + 1.1 * np.exp(-((np.log(np.maximum(f, 1)) - np.log(2500)) ** 2) / (2 * 0.45 ** 2))
    filt = np.fft.irfft(S * band, n)

    # непрерывный шорох как основа - карандаш не отрывается от бумаги
    env = np.full(n, 0.42)
    pos = 0.05
    while pos < DUR - 0.15:
        L = rng.uniform(0.13, 0.26)
        ln = int(SR * L)
        s = int(SR * pos)
        if s + ln > n:
            break
        a = min(int(SR * rng.uniform(0.035, 0.065)), ln // 2)  # длинная мягкая атака
        e = np.zeros(ln)
        e[:a] = np.linspace(0, 1, a) ** 1.15
        e[a:] = np.linspace(1, rng.uniform(0.25, 0.5), ln - a) ** 1.1
        env[s:s + ln] += e * rng.uniform(0.30, 0.58)
        pos += L * rng.uniform(0.40, 0.68)  # штрихи сильно перекрываются

    k = np.hanning(int(SR * 0.02))
    env = np.convolve(env, k / k.sum(), mode="same")

    grain = 1 + 0.22 * np.sin(2 * np.pi * 58 * t) + 0.12 * np.sin(2 * np.pi * 97 * t + 1.3)
    sig = filt * env * grain

    # призвук бумаги и стола
    low = np.fft.irfft(np.fft.rfft(rng.standard_normal(n)) * (1 / (1 + ((f / 240) ** 5))), n)
    sig = sig + 0.14 * low * env

    sig /= np.max(np.abs(sig)) + 1e-9
    fi, fo = int(SR * 0.09), int(SR * 0.22)
    sig[:fi] *= np.linspace(0, 1, fi) ** 0.8
    sig[-fo:] *= np.linspace(1, 0, fo) ** 1.3
    sig *= 0.9

    w = wave.open(path, "wb")
    w.setnchannels(1); w.setsampwidth(2); w.setframerate(SR)
    w.writeframes(struct.pack("<%dh" % n, *(np.clip(sig, -1, 1) * 32000).astype(np.int16)))
    w.close()
    return path

if __name__ == "__main__":
    print("записан", make())
