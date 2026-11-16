"""Ajoute une voix off synthétique (eSpeak-NG + MBROLA) sur la vidéo générée.

Prérequis (Debian/Ubuntu) : sudo apt install espeak-ng mbrola mbrola-fr1
Usage : python3 add_voice.py   (après make_video.py)
Le héros a une voix chuchotée et proche ; « Yanis » a une voix grave et
filtrée (interphone), puis étouffée (derrière la porte).
Pour une voix plus naturelle, enregistre-toi ou utilise ElevenLabs avec les
mêmes répliques et les mêmes temps (voir la liste LINES).
"""
import os, subprocess, tempfile
import make_video as mv

HERE = os.path.dirname(os.path.abspath(__file__))
VIDEO = mv.OUT
OUT = os.path.join(HERE, "regle_du_3e_partie1_voix.mp4")

# Texte prononcé (écrit phonétiquement si besoin) pour chaque sous-titre parlé.
SPOKEN = {
    "Trois… deux… un…": ("hero", "Trois.  Deux.  Un."),
    "Encore leur rumeur débile…": ("hero", "Encore leur rumeur débile."),
    "L'interphone du 3e. Mais il n'y a personne en bas.": ("hero", "L'interphone du troisième. Mais, il n'y a personne en bas."),
    "« Allô ? C'est Yanis… j'ai oublié mon badge. Ouvre-moi. »": ("interphone", "Allô ? C'est Yanis. J'ai oublié mon badge. Ouvre moi."),
    "Yanis ? Il dort à l'infirmerie depuis ce soir…": ("hero", "Yanis ? Il dort à l'infirmerie depuis ce soir."),
    "« Pourquoi tu m'ouvres pas ? Il fait froid dehors… »": ("interphone", "Pourquoi tu m'ouvres pas ? Il fait froid, dehors."),
    "Quelqu'un frappe à ma porte. La 312.": ("hero", "Quelqu'un frappe à ma porte. La trois cent douze."),
    "« C'est moi… Yanis. Ouvre. »": ("door", "C'est moi.  Yanis.  Ouvre."),
}

VOICE = {   # (voix espeak, hauteur, vitesse, filtre ffmpeg)
    "hero": ("mb-fr1", 58, 135, "highpass=f=120,volume=2.2,aecho=0.8:0.6:30:0.15"),
    "interphone": ("mb-fr1", 22, 112, "highpass=f=400,lowpass=f=2800,acrusher=bits=8:mix=0.35,volume=2.6,"
                                      "aecho=0.8:0.7:60|120:0.3|0.2"),
    "door": ("mb-fr1", 18, 100, "lowpass=f=900,volume=3.2,aecho=0.8:0.8:40:0.35"),
}

def main():
    tmp = tempfile.mkdtemp()
    lines, g = [], 0.0
    for sc in mv.SCENES:
        for t0, t1, text, _ in sc.get("subs", []):
            if text in SPOKEN:
                lines.append((g + t0, g + t1, *SPOKEN[text]))
        g += sc["d"]
    inputs, filters = ["-i", VIDEO], []
    for i, (start, end, who, text) in enumerate(lines):
        v, pitch, speed, fx = VOICE[who]
        raw = os.path.join(tmp, f"l{i}.wav")
        subprocess.run(["espeak-ng", "-v", v, "-p", str(pitch), "-s", str(speed), "-w", raw, text],
                       check=True, capture_output=True)
        dur = float(subprocess.check_output(["ffprobe", "-v", "error", "-show_entries", "format=duration",
                                             "-of", "csv=p=0", raw]))
        tempo = max(1.0, dur / max(0.5, end - start))       # accélère si la réplique dépasse le sous-titre
        print(f"{start:5.1f}s  {who:10s} {dur:4.1f}s  {text}")
        inputs += ["-i", raw]
        filters.append(f"[{i + 1}:a]aresample=44100,atempo={tempo:.3f},{fx},adelay={int(start * 1000)}:all=1[v{i}]")
    mix = "".join(f"[v{i}]" for i in range(len(lines)))
    filters.append(f"[0:a]volume=0.55[bg];[bg]{mix}amix=inputs={len(lines) + 1}:normalize=0:duration=first,"
                   f"alimiter=limit=0.95[a]")
    subprocess.run(["ffmpeg", "-v", "error", "-y", *inputs, "-filter_complex", ";".join(filters),
                    "-map", "0:v", "-map", "[a]", "-c:v", "copy", "-c:a", "aac", "-b:a", "160k", OUT], check=True)
    print("OK ->", OUT)

if __name__ == "__main__":
    main()
