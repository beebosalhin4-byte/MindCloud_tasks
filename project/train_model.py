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
from sklearn.ensemble import RandomForestClassifier, ExtraTreesClassifier
from sklearn.svm import SVC
from sklearn.metrics import classification_report, confusion_matrix, f1_score, accuracy_score

warnings.filterwarnings('ignore')

OUTPUT_DIR = "model_results"
os.makedirs(OUTPUT_DIR, exist_ok=True)
SAMPLE_RATE = 22050


# ==========================================
# 1. AUDIO FEATURE EXTRACTION (46 FEATURES)
# ==========================================
def extract_audio_features(y, sr=SAMPLE_RATE):
    """
    Extracts 46 spectral and temporal features:
    - 40 MFCCs (20 means + 20 stds)
    - 1 Duration
    - 2 RMS Intensity (mean + std)
    - 1 F0 Base Pitch (250Hz - 700Hz)
    - 2 Zero-Crossing Rate (mean + std)
    """
    if len(y) == 0:
        return np.zeros(46)

    # MFCCs
    mfccs = librosa.feature.mfcc(y=y, sr=sr, n_mfcc=20)
    mfcc_mean = np.mean(mfccs, axis=1)
    mfcc_std = np.std(mfccs, axis=1)

    # Duration
    duration = np.array([librosa.get_duration(y=y, sr=sr)])

    # RMS Loudness
    rms = librosa.feature.rms(y=y)
    rms_mean = np.array([np.mean(rms)])
    rms_std = np.array([np.std(rms)])

    # Pitch F0 (Infant cry band: 250 - 700 Hz)
    pitches, magnitudes = librosa.piptrack(y=y, sr=sr, fmin=250, fmax=700)
    pitch_vals = pitches[pitches > 0]
    f0_mean = np.array([np.mean(pitch_vals) if len(pitch_vals) > 0 else 0.0])

    # Zero Crossing Rate
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
# 2. FEATURE-LEVEL SMOTE (SYNTHETIC GENERATION)
# ==========================================
def apply_smote_resampling(X_class, target_count, k_neighbors=3, noise_level=0.02):
    """
    Generates synthetic samples using k-nearest neighbor linear interpolation
    instead of exact row duplication to prevent overfitting.
    """
    current_count = len(X_class)
    if current_count >= target_count:
        indices = np.random.choice(current_count, target_count, replace=False)
        return X_class[indices]

    needed = target_count - current_count
    synthetic_samples = []

    for _ in range(needed):
        idx = np.random.randint(0, current_count)
        base_point = X_class[idx]

        # Compute Euclidean distance to other points in the same class
        distances = np.linalg.norm(X_class - base_point, axis=1)
        k_nearest_indices = np.argsort(distances)[1:k_neighbors + 1]

        # Interpolate between base point and a random neighbor
        neighbor_idx = np.random.choice(k_nearest_indices)
        neighbor_point = X_class[neighbor_idx]

        lambda_val = np.random.uniform(0.1, 0.9)
        new_point = base_point + lambda_val * (neighbor_point - base_point)
        new_point += np.random.normal(0, noise_level, size=new_point.shape)
        synthetic_samples.append(new_point)

    return np.vstack([X_class, np.array(synthetic_samples)])


# ==========================================
# 3. DATASET PREPROCESSING & BALANCING
# ==========================================
def load_and_preprocess_dataset(csv_path="dataset.csv", target_class_size=140):
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

    # Strict 80/20 Stratified Split
    X_train_raw, X_test_raw, y_train_raw, y_test_raw = train_test_split(
        X_raw_audio, y_labels, test_size=0.20, random_state=42, stratify=y_labels
    )

    # Extract base features
    X_train_base = np.array([extract_audio_features(a) for a in X_train_raw])
    y_train_base = np.array(y_train_raw)

    # Scale training features before SMOTE
    scaler = StandardScaler()
    X_train_scaled = scaler.fit_transform(X_train_base)

    # Apply SMOTE per class to balance at target_class_size (140)
    X_train_balanced_list = []
    y_train_balanced_list = []

    for label in ['hungry', 'discomfort', 'tired']:
        class_mask = (y_train_base == label)
        X_class = X_train_scaled[class_mask]

        X_resampled = apply_smote_resampling(X_class, target_count=target_class_size)
        X_train_balanced_list.append(X_resampled)
        y_train_balanced_list.extend([label] * target_class_size)

    X_train_bal = np.vstack(X_train_balanced_list)
    y_train_bal = np.array(y_train_balanced_list)

    print(f"[Resampling] SMOTE Balanced Distribution (Target={target_class_size} per class):")
    print(pd.Series(y_train_bal).value_counts())

    # Process test set (Unseen & Unmodified)
    X_test_base = np.array([extract_audio_features(a) for a in X_test_raw])
    X_test_scaled = scaler.transform(X_test_base)
    y_test = np.array(y_test_raw)

    # Save scaler artifact
    joblib.dump(scaler, os.path.join(OUTPUT_DIR, "feature_scaler.joblib"))

    return X_train_bal, y_train_bal, X_test_scaled, y_test


# ==========================================
# 4. MODEL TRAINING & EVALUATION
# ==========================================
def train_and_evaluate_models(X_train, y_train, X_test, y_test):
    models = {
        "SVM": (
            SVC(random_state=42, class_weight='balanced', probability=True),
            {"C": [0.5, 1, 2, 5], "gamma": ["scale", "auto"], "kernel": ["rbf"]}
        ),
        "RandomForest": (
            RandomForestClassifier(random_state=42, class_weight='balanced'),
            {"n_estimators": [100, 200], "max_depth": [6, 10, 14], "min_samples_leaf": [1, 2]}
        ),
        "ExtraTrees": (
            ExtraTreesClassifier(random_state=42, class_weight='balanced'),
            {"n_estimators": [100, 200], "max_depth": [6, 10, 14], "min_samples_leaf": [1, 2]}
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
        grid.fit(X_train, y_train)

        best_clf = grid.best_estimator_
        y_pred = best_clf.predict(X_test)

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

    # Save Best Model
    model_path = os.path.join(OUTPUT_DIR, "best_cry_model.joblib")
    joblib.dump(best_overall_model, model_path)
    print(f"\n✓ Saved best model ({best_model_name}) to: {model_path}")

    # Plot & Save Confusion Matrix
    y_pred_best = best_overall_model.predict(X_test)
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
    X_tr, y_tr, X_te, y_te = load_and_preprocess_dataset("dataset.csv", target_class_size=140)
    train_and_evaluate_models(X_tr, y_tr, X_te, y_te)