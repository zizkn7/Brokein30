"""Ajoute la voix off sur la vidéo générée par make_video.py.

Voix neuronale Kokoro (installée par ./setup_kokoro.sh) :
  - l'héroïne : voix française naturelle « ff_siwis », chuchotée et proche ;
  - « Yanis » : mélange ff_siwis + voix grave masculine, baissé d'un ton,
    filtré façon interphone, puis étouffé derrière la porte.
Si Kokoro n'est pas installé, repli sur eSpeak-NG + MBROLA (robotique).

Usage : python3 add_voice.py
"""
import os, subprocess, tempfile, wave
import numpy as np
import make_video as mv

HERE = os.path.dirname(os.path.abspath(__file__))
ASSETS = os.path.join(HERE, "kokoro_assets")
VIDEO = mv.OUT
OUT = os.path.join(HERE, "regle_du_3e_partie1_voix.mp4")

# sous-titre -> (personnage, texte prononcé)
SPOKEN = {
    "Trois… deux… un…": ("hero", "Trois.|Deux.|Un."),
    "Encore leur rumeur débile…": ("hero", "Pff… encore leur rumeur débile."),
    "L'interphone du 3e. Mais il n'y a personne en bas.": ("hero", "L'interphone du troisième… Mais il n'y a personne en bas."),
    "« Allô ? C'est Yanis… j'ai oublié mon badge. Ouvre-moi. »": ("interphone", "Allô ? C'est Yanis… J'ai oublié mon badge. Ouvre-moi."),
    "Yanis ? Il dort à l'infirmerie depuis ce soir…": ("hero", "Yanis ? Mais… il dort à l'infirmerie depuis ce soir."),
    "« Pourquoi tu m'ouvres pas ? Il fait froid dehors… »": ("interphone", "Pourquoi tu m'ouvres pas ? Il fait froid, dehors…"),
    "Quelqu'un frappe à ma porte. La 312.": ("hero", "Quelqu'un frappe à ma porte. La trois cent douze."),
    "« C'est moi… Yanis. Ouvre. »": ("door", "C'est moi… Yanis. Ouvre."),
}

# (style kokoro, vitesse, demi-tons, filtre ffmpeg)
KOKORO = {
    "hero":       ("hero", 1.0, 0,  "highpass=f=100,volume=1.8,aecho=0.8:0.5:25:0.12"),
    "interphone": ("yanis", 0.92, -2, "highpass=f=350,lowpass=f=3200,acrusher=bits=10:mix=0.25,volume=2.4,"
                                      "aecho=0.8:0.7:60|120:0.3|0.2"),
    "door":       ("yanis", 0.80, -3, "lowpass=f=1100,volume=3.0,aecho=0.8:0.8:40:0.35"),
}
ESPEAK = {   # repli : (voix, hauteur, vitesse, filtre)
    "hero": ("mb-fr1", 58, 135, KOKORO["hero"][3]),
    "interphone": ("mb-fr1", 22, 112, KOKORO["interphone"][3]),
    "door": ("mb-fr1", 18, 100, KOKORO["door"][3]),
}

def write_wav(path, audio, sr):
    with wave.open(path, "wb") as w:
        w.setnchannels(1); w.setsampwidth(2); w.setframerate(sr)
        w.writeframes((np.clip(audio, -1, 1) * 32767).astype(np.int16).tobytes())

def make_tts():
    try:
        from kokoro_onnx import Kokoro
        k = Kokoro(os.path.join(ASSETS, "kokoro-q8.onnx"), os.path.join(ASSETS, "voices.npz"))
    except Exception as e:
        print("Kokoro indisponible (", e, ") -> repli eSpeak. Lance ./setup_kokoro.sh pour la voix naturelle.")
        def tts(who, text, path):
            v, p, s, fx = ESPEAK[who]
            subprocess.run(["espeak-ng", "-v", v, "-p", str(p), "-s", str(s), "-w", path, text.replace("|", " ")],
                           check=True, capture_output=True)
            return fx, 0
        return tts
    siwis = k.get_voice_style("ff_siwis")
    styles = {"hero": siwis,
              "yanis": siwis * 0.45 + k.get_voice_style("am_onyx") * 0.35 + k.get_voice_style("am_michael") * 0.20}
    def tts(who, text, path):
        st, speed, semis, fx = KOKORO[who]
        parts = []                                       # "a|b|c" = une syllabe par tic-tac (1,5 s)
        for piece in text.split("|"):
            a, sr = k.create(piece, voice=styles[st], speed=speed, lang="fr-fr")
            if "|" in text:
                a = np.concatenate([a, np.zeros(max(0, int(1.5 * sr) - len(a)), np.float32)])
            parts.append(a)
        write_wav(path, np.concatenate(parts), sr)
        return fx, semis
    return tts

def main():
    tts = make_tts()
    tmp = tempfile.mkdtemp()
    lines, g = [], 0.0
    for sc in mv.SCENES:
        for t0, t1, text, _ in sc.get("subs", []):
            if text in SPOKEN:
                lines.append((g + t0, g + t1, *SPOKEN[text]))
        g += sc["d"]
    inputs, filters = ["-i", VIDEO], []
    for i, (start, end, who, text) in enumerate(lines):
        raw = os.path.join(tmp, f"l{i}.wav")
        fx, semis = tts(who, text, raw)
        sr = int(subprocess.check_output(["ffprobe", "-v", "error", "-show_entries", "stream=sample_rate",
                                          "-of", "csv=p=0", raw]))
        dur = float(subprocess.check_output(["ffprobe", "-v", "error", "-show_entries", "format=duration",
                                             "-of", "csv=p=0", raw]))
        ratio = 2 ** (semis / 12)                            # changement de hauteur
        pitch = f"asetrate={int(sr * ratio)},aresample=44100,atempo={1 / ratio:.4f}," if semis else "aresample=44100,"
        tempo = max(1.0, dur / max(0.5, end - start + 0.4))  # accélère si la réplique dépasse son créneau
        print(f"{start:5.1f}s  {who:10s} {dur:4.1f}s  {text}")
        inputs += ["-i", raw]
        filters.append(f"[{i + 1}:a]{pitch}atempo={tempo:.3f},{fx},adelay={int(start * 1000)}:all=1[v{i}]")
    mix = "".join(f"[v{i}]" for i in range(len(lines)))
    filters.append(f"[0:a]volume=0.55[bg];[bg]{mix}amix=inputs={len(lines) + 1}:normalize=0:duration=first,"
                   f"alimiter=limit=0.95[a]")
    subprocess.run(["ffmpeg", "-v", "error", "-y", *inputs, "-filter_complex", ";".join(filters),
                    "-map", "0:v", "-map", "[a]", "-c:v", "copy", "-c:a", "aac", "-b:a", "160k", OUT], check=True)
    print("OK ->", OUT)

if __name__ == "__main__":
    main()
