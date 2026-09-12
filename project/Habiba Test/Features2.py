import librosa
import numpy as np

def featureextraction(path, output_list):
    aud, sr = librosa.load(path, sr=22050)
    mfcc = librosa.feature.mfcc(y=aud, sr=sr, n_mfcc=20)
    mfccmean=np.mean(mfcc,axis=1)
    mfccstd=np.std(mfcc,axis=1)
    duration = float(librosa.get_duration(y=aud, sr=sr))
    rms = librosa.feature.rms(y=aud)
    rms_mean = float(np.mean(rms))
    rms_std = float(np.std(rms))
    fndfreq = librosa.yin(aud, sr=sr, fmin=300, fmax=600,)
    f0_mean = float(np.nanmean(fndfreq)) if np.any(~np.isnan(fndfreq)) else 0
    f0_std = float(np.nanstd(fndfreq)) if np.any(~np.isnan(fndfreq)) else 0
    zcr = librosa.feature.zero_crossing_rate(aud)
    zcrmean = float(np.mean(zcr))
    zcrstd = float(np.std(zcr))
    row = {
        "Path": path,
        "duration": duration,
        "rmsmean": rms_mean,
        "rmsstd": rms_std,
        "zcr_mean": zcrmean,
        "zcr_std": zcrstd,
        "f0_mean": f0_mean,
        "f0_std": f0_std,
        }
    for i in range(20):
        row[f"mfcc mean {i+1}"]=float(mfccmean[i])
        row[f"mfcc std {i+1}"]=float(mfccstd[i])
    

    output_list.append(row)
    return output_list