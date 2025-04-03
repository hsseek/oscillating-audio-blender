import numpy as np
import wave
import configparser
from scipy.io.wavfile import write
from pydub import AudioSegment
import os

# Load config
config = configparser.ConfigParser()
config.read("config.ini")

PINK_FILE = config["FILES"]["pink_file"]
BROWN_FILE = config["FILES"]["brown_file"]
CYCLE_MINUTES = int(config["TIMING"]["cycle_minutes"])
PINK_MIN = float(config["MIX"]["pink_min"])
PINK_MAX = float(config["MIX"]["pink_max"])
PINK_GAIN = float(config["MIX"].get("pink_gain", 1.0))
BROWN_GAIN = float(config["MIX"].get("brown_gain", 1.0))
SAMPLE_RATE = int(config["AUDIO"].get("sample_rate", 8000))

EXPORT_FILENAME = "blended_output.ogg"

print("\n🔧 Configuration:")
print(f"  Pink file      : {PINK_FILE}")
print(f"  Brown file     : {BROWN_FILE}")
print(f"  Export length  : {CYCLE_MINUTES} minutes")
print(f"  Sample rate    : {SAMPLE_RATE} Hz")
print(f"  Pink gain      : {PINK_GAIN}")
print(f"  Brown gain     : {BROWN_GAIN}")

# Load WAV file data
def load_wav(filename):
    with wave.open(filename, 'rb') as wf:
        frames = wf.readframes(wf.getnframes())
        audio = np.frombuffer(frames, dtype=np.int16)
        return audio

pink_audio = load_wav(PINK_FILE)
brown_audio = load_wav(BROWN_FILE)
min_len = min(len(pink_audio), len(brown_audio))
pink_audio = pink_audio[:min_len]
brown_audio = brown_audio[:min_len]

# Apply manual gain
pink_audio = (pink_audio.astype(np.float64) * PINK_GAIN)
brown_audio = (brown_audio.astype(np.float64) * BROWN_GAIN)

# Total duration and samples (cycle duration is A->B->A)
total_seconds = CYCLE_MINUTES * 60

print(f"  Total seconds  : {total_seconds} seconds")

# Output array
output = np.zeros(total_seconds * SAMPLE_RATE, dtype=np.float64)

# Loop and mix
print("\n🎛️  Generating blended audio...")
for i in range(len(output)):
    t = i / SAMPLE_RATE
    blend = (PINK_MIN + PINK_MAX) / 2 - (PINK_MAX - PINK_MIN) / 2 * np.cos(2 * np.pi * t / total_seconds)
    pink_sample = pink_audio[i % len(pink_audio)]
    brown_sample = brown_audio[i % len(brown_audio)]
    mixed_sample = pink_sample * blend + brown_sample * (1 - blend)
    output[i] = mixed_sample

# Apply limiter if needed
max_val = np.max(np.abs(output))
if max_val > 32767:
    print(f"⚠️  Limiting output: max sample was {max_val:.1f}")
    output = output / max_val * 32767

output = output.astype(np.int16)

# Save temp WAV for conversion
temp_wav = "temp_output.wav"
write(temp_wav, SAMPLE_RATE, output)

# Convert to .ogg using pydub
sound = AudioSegment.from_wav(temp_wav)
sound.export(EXPORT_FILENAME, format="ogg", bitrate="32k")
os.remove(temp_wav)

print(f"\n✅ Export complete: {EXPORT_FILENAME}")
