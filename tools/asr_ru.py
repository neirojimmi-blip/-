"""Расшифровка русской речи локально: sherpa-onnx + GigaAM v2.

Хосты с весами Whisper и Vosk закрыты политикой сети, а релизы GitHub —
нет, поэтому берём оттуда. Модель отдаёт слова с таймкодами, из них
собираются реплики по паузам.
"""
import json, sys, wave
import numpy as np
import sherpa_onnx

M = "asr/sherpa-onnx-nemo-transducer-giga-am-v2-russian-2025-04-19"


def read_wav(path):
    with wave.open(path) as w:
        assert w.getframerate() == 16000 and w.getnchannels() == 1, "нужен моно 16 кГц"
        n = w.getnframes()
        a = np.frombuffer(w.readframes(n), dtype=np.int16)
    return a.astype(np.float32) / 32768.0


def main(wav, out="words.json"):
    rec = sherpa_onnx.OfflineRecognizer.from_transducer(
        encoder=f"{M}/encoder.int8.onnx",
        decoder=f"{M}/decoder.onnx",
        joiner=f"{M}/joiner.onnx",
        tokens=f"{M}/tokens.txt",
        model_type="nemo_transducer",
        num_threads=4,
    )
    samples = read_wav(wav)
    print(f"аудио: {len(samples)/16000:.2f} с")

    # длинную дорожку режем по тишине — модель обучена на коротких кусках
    vad_cfg = sherpa_onnx.VadModelConfig()
    chunks = []
    try:
        vad_cfg.silero_vad.model = "asr/silero_vad.onnx"
        vad_cfg.sample_rate = 16000
        vad = sherpa_onnx.VoiceActivityDetector(vad_cfg, buffer_size_in_seconds=60)
        step = 512
        for i in range(0, len(samples), step):
            vad.accept_waveform(samples[i:i + step])
            while not vad.empty():
                chunks.append((vad.front.start / 16000, vad.front.samples))
                vad.pop()
        vad.flush()
        while not vad.empty():
            chunks.append((vad.front.start / 16000, vad.front.samples))
            vad.pop()
    except Exception as e:
        print("VAD недоступен, читаю целиком:", e)
        chunks = [(0.0, samples)]

    words = []
    for off, seg in chunks:
        s = rec.create_stream()
        s.accept_waveform(16000, np.asarray(seg, dtype=np.float32))
        rec.decode_stream(s)
        r = s.result
        ts = list(r.timestamps) if r.timestamps else []
        toks = list(r.tokens) if r.tokens else []
        if ts and toks and len(ts) == len(toks):
            cur, cur_t = "", None
            for tok, t in zip(toks, ts):
                if tok.startswith("▁") or tok.startswith(" "):
                    if cur:
                        words.append({"w": cur, "t": round(off + cur_t, 3)})
                    cur, cur_t = tok.lstrip("▁ "), t
                else:
                    if cur_t is None:
                        cur_t = t
                    cur += tok
            if cur:
                words.append({"w": cur, "t": round(off + cur_t, 3)})
        else:
            words.append({"w": r.text.strip(), "t": round(off, 3)})
        print(f"{off:6.2f}  {r.text.strip()}")

    json.dump(words, open(out, "w"), ensure_ascii=False, indent=1)
    print(f"\nслов: {len(words)} → {out}")
    print("\nТЕКСТ ЦЕЛИКОМ:\n" + " ".join(w["w"] for w in words))


if __name__ == "__main__":
    main(sys.argv[1] if len(sys.argv) > 1 else "n3/audio.wav",
         sys.argv[2] if len(sys.argv) > 2 else "n3/words.json")
