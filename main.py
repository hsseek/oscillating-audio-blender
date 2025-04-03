import numpy as np
import configparser
import wave
import os
import argparse
from scipy.io.wavfile import write
from pydub import AudioSegment
from datetime import datetime

def log(msg):
    now = datetime.now().strftime("[%H:%M:%S]")
    print(f"{now} {msg}")

def load_config():
    config = configparser.ConfigParser()
    config.read("config.ini")
    return {
        "file_1": config.get("FILES", "file_1"),
        "file_2": config.get("FILES", "file_2"),
        "cycle_minutes": config.getint("TIMING", "cycle_minutes"),
        "gain_1": config.getfloat("MIX", "gain_1"),
        "gain_2": config.getfloat("MIX", "gain_2"),
        "blend_min": config.getfloat("MIX", "blend_min"),
        "blend_max": config.getfloat("MIX", "blend_max"),
        "sample_rate": config.getint("AUDIO", "sample_rate"),
    }

def parse_args():
    parser = argparse.ArgumentParser(description="Oscillating Audio Blender")
    parser.add_argument("-f1", help="Path to first WAV file")
    parser.add_argument("-f2", help="Path to second WAV file")
    parser.add_argument("-g1", type=float, help="Gain for first file")
    parser.add_argument("-g2", type=float, help="Gain for second file")
    parser.add_argument("--blend-start", type=float, help="Blend value at start (0-1)")
    parser.add_argument("--blend-end", type=float, help="Blend value at end (0-1)")
    parser.add_argument("--cycle-duration", type=int, help="Cycle duration in minutes")
    parser.add_argument("--sample-rate", type=int, help="Sample rate")
    parser.add_argument("--output", default="blended_output.ogg", help="Output file name")
    return parser.parse_args()

def load_wav(path):
    with wave.open(path, 'rb') as wf:
        frames = wf.readframes(wf.getnframes())
        return np.frombuffer(frames, dtype=np.int16)

def generate_audio(cfg, output_file):
    sr = cfg["sample_rate"]

    if not os.path.exists(cfg["file_1"]) or not os.path.exists(cfg["file_2"]):
        log("ERROR: Input WAV files not found.")
        return

    log("Loading WAV files...")
    a1 = load_wav(cfg["file_1"]).astype(np.float64)
    a2 = load_wav(cfg["file_2"]).astype(np.float64)
    length = min(len(a1), len(a2))
    a1 = a1[:length] * cfg["gain_1"]
    a2 = a2[:length] * cfg["gain_2"]
    log("Files loaded and gain applied.")

    total_sec = cfg["cycle_minutes"] * 60
    total_samples = total_sec * sr
    output = np.zeros(total_samples, dtype=np.float64)

    for i in range(total_samples):
        t = i / sr
        blend = cfg["blend_min"] + (cfg["blend_max"] - cfg["blend_min"]) * (
            1 - np.cos(2 * np.pi * t / total_sec)) / 2
        s1 = a1[i % length]
        s2 = a2[i % length]
        output[i] = s1 * blend + s2 * (1 - blend)

    max_val = np.max(np.abs(output))
    if max_val > 32767:
        log("Limiting output to prevent clipping.")
        output = output / max_val * 32767
    output = output.astype(np.int16)

    temp_wav = "temp_output.wav"
    write(temp_wav, sr, output)
    log("Temporary WAV file written.")

    AudioSegment.from_wav(temp_wav).export(output_file, format="ogg", bitrate="32k")
    os.remove(temp_wav)
    log(f"✅ Export complete: {output_file}")

if __name__ == "__main__":
    args = parse_args()
    config = load_config()

    # Override config with CLI args if provided
    config["file_1"] = args.file_1 or config["file_1"]
    config["file_2"] = args.file_2 or config["file_2"]
    config["gain_1"] = args.gain_1 if args.gain_1 is not None else config["gain_1"]
    config["gain_2"] = args.gain_2 if args.gain_2 is not None else config["gain_2"]
    config["blend_min"] = args.blend_min if args.blend_min is not None else config["blend_min"]
    config["blend_max"] = args.blend_max if args.blend_max is not None else config["blend_max"]
    config["cycle_minutes"] = args.cycle if args.cycle is not None else config["cycle_minutes"]
    config["sample_rate"] = args.sample_rate if args.sample_rate is not None else config["sample_rate"]

    generate_audio(config, args.output)
