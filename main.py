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
        "blend_1_start": config.getfloat("MIX", "blend_1_start"),
        "blend_1_middle": config.getfloat("MIX", "blend_1_middle"),
        "sample_rate": config.getint("AUDIO", "sample_rate"),
    }

def parse_args():
    parser = argparse.ArgumentParser(description="Oscillating Audio Blender")
    parser.add_argument("--file1", dest="file_1", help="Path to first WAV file")
    parser.add_argument("--file2", dest="file_2", help="Path to second WAV file")
    parser.add_argument("--gain1", dest="gain_1", type=float, help="Gain for first file")
    parser.add_argument("--gain2", dest="gain_2", type=float, help="Gain for second file")
    parser.add_argument("--blend-start", dest="blend_1_start", type=float, help="Blend value at start (0-1)")
    parser.add_argument("--blend-middle", dest="blend_1_middle", type=float, help="Blend value in middle (0-1)")
    parser.add_argument("--cycle-duration", dest="cycle_minutes", type=int, help="Cycle duration in minutes")
    parser.add_argument("--sample-rate", dest="sample_rate", type=int, help="Sample rate")
    parser.add_argument("--output", default="blended_output.ogg", help="Output file name")
    return parser.parse_args()

def load_wav(path):
    with wave.open(path, 'rb') as wf:
        frames = wf.readframes(wf.getnframes())
        return np.frombuffer(frames, dtype=np.int16)

def print_progress(current, total, width=40):
    progress = int(width * current / total)
    bar = "█" * progress + "-" * (width - progress)
    print(f"\rProgress: |{bar}| {int(100 * current / total)}%", end="")

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

        buffer_sec = min(10, total_sec * 0.10)
        if t < buffer_sec or t > (total_sec - buffer_sec):
            blend = cfg["blend_1_start"]
        else:
            # Adjust time to exclude buffer zone
            t_adj = t - buffer_sec
            inner_duration = total_sec - 2 * buffer_sec
            blend = cfg["blend_1_start"] + (cfg["blend_1_middle"] - cfg["blend_1_start"]) * (
                    1 - np.cos(2 * np.pi * t_adj / inner_duration)) / 2

        s1 = a1[i % length]
        s2 = a2[i % length]
        output[i] = s1 * blend + s2 * (1 - blend)

        # CLI progress bar
        if i % (total_samples // 100) == 0:
            print_progress(i, total_samples)

    print_progress(total_samples, total_samples)
    print()  # newline after progress bar

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

    # Report summary
    print("\nParameters:")
    print(f"- File 1: {cfg['file_1']} (gain: {cfg['gain_1']})")
    print(f"- File 2: {cfg['file_2']} (gain: {cfg['gain_2']})")
    print(f"- Blend: File 1 from {cfg['blend_1_start']} → {cfg['blend_1_middle']} → {cfg['blend_1_start']}")
    print(f"- Cycle Duration: {cfg['cycle_minutes']} minute(s)")
    print(f"- Sample Rate: {cfg['sample_rate']} Hz")


if __name__ == "__main__":
    args = parse_args()
    config = load_config()

    # Override config with CLI args if provided
    config["file_1"] = args.file_1 or config["file_1"]
    config["file_2"] = args.file_2 or config["file_2"]
    config["gain_1"] = args.gain_1 if args.gain_1 is not None else config["gain_1"]
    config["gain_2"] = args.gain_2 if args.gain_2 is not None else config["gain_2"]
    config["blend_1_start"] = args.blend_1_start if args.blend_1_start is not None else config["blend_1_start"]
    config["blend_1_middle"] = args.blend_1_middle if args.blend_1_middle is not None else config["blend_1_middle"]
    config["cycle_minutes"] = args.cycle_minutes if args.cycle_minutes is not None else config["cycle_minutes"]
    config["sample_rate"] = args.sample_rate if args.sample_rate is not None else config["sample_rate"]

    if args.output == "blended_output.ogg":
        output = f"oscbldr-{config['cycle_minutes']}-{int(config['gain_1'] * 10):02d}-{int(config['gain_2'] * 10):02d}-{int(config['blend_1_start'] * 100):02d}-{int(config['blend_1_middle'] * 100):02d}.ogg"
    else:
        output = args.output

    generate_audio(config, output)
