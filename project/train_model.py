import os
import warnings
import numpy as np
import pandas as pd
import librosa
import joblib
import matplotlib.pyplot as plt
import seaborn as sns

from sklearn.model_selection import train_test_split, GridSearchCV, StratifiedKFold
from sklearn.preprocessing import StandardScaler
from sklearn.ensemble import RandomForestClassifier
from sklearn.svm import SVC
from sklearn.metrics import classification_report, confusion_matrix, f1_score, accuracy_score
from sklearn.utils import resample

warnings.filterwarnings('ignore')

OUTPUT_DIR = "model_results"
os.makedirs(OUTPUT_DIR, exist_ok=True)
SAMPLE_RATE = 22050


# ==========================================
# 1. FEATURE EXTRACTION (ALL 5 REPORT FEATURES)
# ==========================================
def extract_audio_features(y, sr=SAMPLE_RATE):
    """
    Extracts all 5 feature categories required in Section 4.4:
    1. MFCC (20 means + 20 stds = 40)
    2. Duration (1)
    3. Intensity / RMS (2)
    4. Fundamental Frequency F0 Base Pitch (1)
    5. Zero-Crossing Rate ZCR (2)
    Total feature vector length: 46
    """
    if len(y) == 0:
        return np.zeros(46)

    # 1. MFCCs
    mfccs = librosa.feature.mfcc(y=y, sr=sr, n_mfcc=20)
    mfcc_mean = np.mean(mfccs, axis=1)
    mfcc_std = np.std(mfccs, axis=1)

    # 2. Duration
    duration = np.array([librosa.get_duration(y=y, sr=sr)])

    # 3. Intensity / RMS
    rms = librosa.feature.rms(y=y)
    rms_mean = np.array([np.mean(rms)])
    rms_std = np.array([np.std(rms)])

    # 4. Fundamental Frequency (F0 Base Pitch in infant cry range: 250 - 700 Hz)
    pitches, magnitudes = librosa.piptrack(y=y, sr=sr, fmin=250, fmax=700)
    pitch_vals = pitches[pitches > 0]
    f0_mean = np.array([np.mean(pitch_vals) if len(pitch_vals) > 0 else 0.0])

    # 5. Zero-Crossing Rate (Harshness)
    zcr = librosa.feature.zero_crossing_rate(y=y)
    zcr_mean = np.array([np.mean(zcr)])
    zcr_std = np.array([np.std(zcr)])

    return np.hstack([
        mfcc_mean, mfcc_std,
        duration,
        rms_mean, rms_std,
        f0_mean,
        zcr_mean, zcr_std
    ])


# ==========================================
# 2. DATA AUGMENTATION (AUDIO LEVEL)
# ==========================================
def augment_audio_signal(y, sr=SAMPLE_RATE):
    augmented = []
    augmented.append(librosa.effects.pitch_shift(y=y, sr=sr, n_steps=2))
    augmented.append(librosa.effects.pitch_shift(y=y, sr=sr, n_steps=-2))
    augmented.append(librosa.effects.time_stretch(y=y, rate=1.1))
    augmented.append(librosa.effects.time_stretch(y=y, rate=0.9))
    noise = np.random.randn(len(y)) * 0.005
    augmented.append(y + noise)
    return augmented


# ==========================================
# 3. DATASET LOADING & HYBRID RESAMPLING
# ==========================================
def load_and_preprocess_dataset(csv_path="dataset.csv", target_class_size=80):
    df = pd.read_csv(csv_path)
    print(f"[Dataset] Raw dataset count: {len(df)}")
    print(f"[Dataset] Raw class breakdown:\n{df['y'].value_counts()}\n")

    X_raw_audio, y_labels = [], []
    for _, row in df.iterrows():
        try:
            y_audio, _ = librosa.load(row['x'], sr=SAMPLE_RATE, duration=5.0)
            X_raw_audio.append(y_audio)
            y_labels.append(row['y'])
        except Exception:
            continue

    # STRICT 80/20 SPLIT BEFORE AUGMENTATION OR RESAMPLING
    X_train_raw, X_test_raw, y_train_raw, y_test_raw = train_test_split(
        X_raw_audio, y_labels, test_size=0.20, random_state=42, stratify=y_labels
    )

    # 1. Audio-level feature extraction + minority class augmentation
    X_train_list, y_train_list = [], []
    for audio, label in zip(X_train_raw, y_train_raw):
        feats = extract_audio_features(audio)
        X_train_list.append(feats)
        y_train_list.append(label)

        if label != 'hungry':
            for aug_y in augment_audio_signal(audio):
                X_train_list.append(extract_audio_features(aug_y))
                y_train_list.append(label)

    # 2. Hybrid Resampling (Undersample majority 'hungry' + Oversample 'discomfort' & 'tired')
    train_df = pd.DataFrame(X_train_list)
    train_df['label'] = y_train_list

    balanced_dfs = []
    for label, group in train_df.groupby('label'):
        if len(group) >= target_class_size:
            resampled_group = resample(group, replace=False, n_samples=target_class_size, random_state=42)
        else:
            resampled_group = resample(group, replace=True, n_samples=target_class_size, random_state=42)
        balanced_dfs.append(resampled_group)

    train_df_balanced = pd.concat(balanced_dfs)
    X_train_bal = train_df_balanced.drop(columns=['label']).values
    y_train_bal = train_df_balanced['label'].values

    print(f"[Resampling] Balanced Training Set Distribution (Target={target_class_size}):")
    print(pd.Series(y_train_bal).value_counts())

    # Extract test set features (NO RESAMPLING / NO AUGMENTATION)
    X_test = np.array([extract_audio_features(audio) for audio in X_test_raw])
    y_test = np.array(y_test_raw)

    return X_train_bal, y_train_bal, X_test, y_test


# ==========================================
# 4. MODEL TRAINING & HYPERPARAMETER TUNING
# ==========================================
def train_and_evaluate_models(X_train, y_train, X_test, y_test):
    scaler = StandardScaler()
    X_train_scaled = scaler.fit_transform(X_train)
    X_test_scaled = scaler.transform(X_test)

    # Save feature scaler for live app inference
    joblib.dump(scaler, os.path.join(OUTPUT_DIR, "feature_scaler.joblib"))

    models = {
        "SVM": (
            SVC(random_state=42, class_weight="balanced", probability=True),
            {"C": [0.1, 0.5, 1, 5, 10], "gamma": ["scale", "auto"], "kernel": ["rbf", "poly"]}
        ),
        "RandomForest": (
            RandomForestClassifier(random_state=42, class_weight="balanced"),
            {"n_estimators": [50, 100, 200], "max_depth": [5, 10, 15], "min_samples_leaf": [1, 2]}
        )
    }

    best_overall_model = None
    best_overall_f1 = -1.0
    best_model_name = ""

    print("\n" + "="*60)
    print("MODEL TRAINING & EVALUATION (OPTIMIZING FOR MACRO F1)")
    print("="*60)

    cv_strategy = StratifiedKFold(n_splits=5, shuffle=True, random_state=42)

    for name, (model, param_grid) in models.items():
        grid = GridSearchCV(model, param_grid, cv=cv_strategy, scoring="f1_macro", n_jobs=-1)
        grid.fit(X_train_scaled, y_train)

        best_clf = grid.best_estimator_
        y_pred = best_clf.predict(X_test_scaled)

        macro_f1 = f1_score(y_test, y_pred, average="macro")
        acc = accuracy_score(y_test, y_pred)

        print(f"\nModel: {name}")
        print(f"Best Params: {grid.best_params_}")
        print(f"Test Accuracy: {acc * 100:.2f}% | Macro F1: {macro_f1:.4f}")
        print("\nClassification Report:\n", classification_report(y_test, y_pred, zero_division=0))

        if macro_f1 > best_overall_f1:
            best_overall_f1 = macro_f1
            best_overall_model = best_clf
            best_model_name = name

    # Save Best Model Artifacts
    model_path = os.path.join(OUTPUT_DIR, "best_cry_model.joblib")
    joblib.dump(best_overall_model, model_path)
    print(f"\n✓ Saved best model ({best_model_name}) to: {model_path}")

    # Plot & Save Confusion Matrix
    y_pred_best = best_overall_model.predict(X_test_scaled)
    labels = ['discomfort', 'hungry', 'tired']
    cm = confusion_matrix(y_test, y_pred_best, labels=labels)

    plt.figure(figsize=(7, 5))
    sns.heatmap(cm, annot=True, fmt='d', cmap='Blues', xticklabels=labels, yticklabels=labels)
    plt.title(f'Best Model ({best_model_name})\nMacro F1: {best_overall_f1:.3f} | Accuracy: {accuracy_score(y_test, y_pred_best)*100:.1f}%')
    plt.xlabel('Predicted Label')
    plt.ylabel('True Label')
    plt.tight_layout()

    cm_path = os.path.join(OUTPUT_DIR, "confusion_matrix.png")
    plt.savefig(cm_path, dpi=150)
    plt.close()
    print(f"✓ Saved updated confusion matrix to: {cm_path}")


if __name__ == "__main__":
    X_tr, y_tr, X_te, y_te = load_and_preprocess_dataset("dataset.csv", target_class_size=80)
    train_and_evaluate_models(X_tr, y_tr, X_te, y_te)