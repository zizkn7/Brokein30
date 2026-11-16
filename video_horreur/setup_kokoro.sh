#!/usr/bin/env bash
# Installe la voix neuronale Kokoro (voix française ff_siwis) depuis npm/PyPI.
set -euo pipefail
cd "$(dirname "$0")"; mkdir -p kokoro_assets; cd kokoro_assets
pip install -q kokoro-onnx
npm pack kokoro-q8-shards@1.0.0 kokoro-js@1.2.1 --silent
mkdir -p q8 kjs && tar xzf kokoro-q8-shards-1.0.0.tgz -C q8 && tar xzf kokoro-js-1.2.1.tgz -C kjs
cat q8/package/kokoro-q8.part{0,1,2,3,4,5}.bin > kokoro-q8.onnx
echo "fbae9257e1e05ffc727e951ef9b9c98418e6d79f1c9b6b13bd59f5c9028a1478  kokoro-q8.onnx" | sha256sum -c -
python3 -c "
import numpy as np, glob, os
v={os.path.basename(f)[:-4]: np.fromfile(f,dtype=np.float32).reshape(-1,1,256) for f in glob.glob('kjs/package/voices/*.bin')}
np.savez('voices.npz', **v)"
rm -rf q8 kjs *.tgz
echo "Kokoro prêt."
