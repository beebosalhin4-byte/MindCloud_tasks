import sounddevice as sd
import soundfile as sf
import noisereduce as nr
import webrtcvad as wvad
import os
import numpy as np
import pandas as pd
import librosa
import time

##############this code records short samples (each of 30 ms), and if noise is detected, 
# it records an audio file os length 3 min, removes back-noise, and saves it and its original copy locally
# note: that only occurs once. In other words, the whole script will need to be re-runned to check for a new 3-min recording ######################

def process_and_save_audio(output_filename="after noise removal.wav", duration=60*3, sr=16000):
    """
    Captures mic input, removes background noise, runs VAD, 
    and saves the result to a WAV audio file on disk.
    """
    print("\n--------------------------------------------------")
    print("Starting audio recording process...")
    print(f"Listening on microphone for {duration} seconds... Speak or play cry sound now!")
    
    # 1. Capture raw audio from laptop mic
    t0 = time.time()
    raw_audio = sd.rec(int(duration * sr), samplerate=sr, channels=1, dtype='float32')
    sd.wait()  # Hardware blocking pause for audio capture
    print(f"Recording finished in {time.time() - t0:.2f}s. Audio captured into RAM.")

    # Flatten audio matrix to 1D vector
    raw_audio = np.squeeze(raw_audio)

###################if you wanna upload the file instead of recording, comment the previous, and uncomment the next
    #try:
    #    raw_audio, _ = librosa.load(r"C:\Users\Habib\Downloads\how-to-settle-an-overtired-fussy-or-colicky-baby-2-aqvs-4.wav", sr=sr, mono=True)
    #except FileNotFoundError:
    #    print(f"ERROR: Could not find the file. Make sure it's in your project folder!")
    #    return None
    #duration = len(raw_audio) / sr
    
    # 2. Spectral Noise Reduction
    print("Applying noise reduction filter...")
    t0 = time.time()
    clean_audio = nr.reduce_noise(
        y=raw_audio, sr=sr, stationary=True
    )
    print(f"Noise removed successfully in {time.time() - t0:.2f}s.")
    
    # 3. Voice Activity Detection (VAD)
    print("Running Voice Activity Detection (WebRTC VAD)...")
    t0 = time.time()
    
    vad = wvad.Vad(0)
    pcm_data = (clean_audio * 32767).astype(np.int16).tobytes()
    frame_bytes = int(sr * 0.030 * 2)  # 30ms frame size
    total_frames = len(pcm_data) // frame_bytes
    
    voiced_frames = sum(
        vad.is_speech(pcm_data[i * frame_bytes : (i + 1) * frame_bytes], sr)
        for i in range(total_frames)
    )
    
    speech_ratio = voiced_frames / max(1, total_frames)
    is_cry_detected = speech_ratio > 0.25
    print(f"VAD analysis finished in {time.time() - t0:.3f}s. Voiced frame ratio: {speech_ratio:.1%}")
    
    # 4. Save to Audio File (.wav)
    print("Finalizing output...")
    if is_cry_detected:
        sf.write("original1.wav", raw_audio,sr)
        sf.write("after noise removal1.wav", clean_audio, sr)
        print(f"SUCCESS: Voice/Cry detected! Cleaned audio file saved to '{output_filename}'")
        return output_filename
    else:
        print("NOTICE: No voice/cry detected in sample. Skipping WAV file saving.")
        return None

def is_cry_detected(duration=0.03, sr=16000):
    t0 = time.time()
    raw_audio = sd.rec(int(duration * sr), samplerate=sr, channels=1, dtype='float32')
    sd.wait()  # Hardware blocking pause for audio capture
    raw_audio = np.squeeze(raw_audio)
    pcm_bytes = (raw_audio * 32767).astype(np.int16).tobytes() 
    vad = wvad.Vad(0)
    # Validate frame byte size (must be exactly 960 bytes for 30ms at 16kHz)
    if len(pcm_bytes) != int(sr * duration * 2):
        return False

    return vad.is_speech(pcm_bytes, sr)

while not is_cry_detected():
    print("No noise detected")
    time.sleep(0.01)
    continue
print("System initializing...")
saved_filepath = process_and_save_audio()
print("Pipeline execution complete!")