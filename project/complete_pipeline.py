#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Complete Infant Crying Classification Pipeline
Combines: Data Augmentation → Feature Extraction → Model Training
Run: python complete_pipeline.py --dataset dataset.csv --output results/
"""

import warnings
warnings.filterwarnings('ignore')

import os
import sys
import argparse
import pandas as pd
import numpy as np
import librosa
import soundfile as sf
from pathlib import Path
import datetime
from tqdm import tqdm
import joblib

# Audio augmentation
from audiomentations import Compose, AddGaussianNoise, PitchShift, HighPassFilter

# ML Models
from sklearn.model_selection import train_test_split, GridSearchCV
from sklearn.preprocessing import StandardScaler
from sklearn.pipeline import Pipeline
from sklearn.linear_model import LogisticRegression, RidgeClassifier
from sklearn.tree import DecisionTreeClassifier
from sklearn.ensemble import RandomForestClassifier, BaggingClassifier, GradientBoostingClassifier
from sklearn.naive_bayes import GaussianNB
from sklearn.neural_network import MLPClassifier
from sklearn.neighbors import KNeighborsClassifier
from sklearn.svm import SVC
from xgboost import XGBClassifier
from sklearn.metrics import (
    accuracy_score, precision_score, recall_score, f1_score,
    classification_report, make_scorer
)
import matplotlib.pyplot as plt
import seaborn as sns

# ================================================================================
# CONFIGURATION
# ================================================================================

class Config:
    TARGET_SAMPLE_RATE = 22050
    DURATION = 7.0
    TARGET_NUM_SAMPLES = int(TARGET_SAMPLE_RATE * DURATION)
    SEED = 42

config = Config()

# ================================================================================
# AUDIO PROCESSING CLASS
# ================================================================================

class AudioPreprocessor:
    def __init__(self, sample_rate=22050):
        self.sample_rate = sample_rate
        self.signal = None
    
    def read_audio(self, file_path):
        """Load audio file"""
        try:
            self.signal, self.sample_rate = librosa.load(file_path, sr=self.sample_rate)
            return self.signal
        except Exception as e:
            return None
    
    def augment_audio(self, signal):
        """Apply audio augmentation"""
        augment = Compose([
            AddGaussianNoise(min_amplitude=0.01, max_amplitude=0.015, p=1),
            PitchShift(min_semitones=-2, max_semitones=2, p=1),
            HighPassFilter(min_cutoff_freq=3000, max_cutoff_freq=4000, p=1)
        ])
        return augment(signal, self.sample_rate)

# ================================================================================
# STEP 1: DATA AUGMENTATION
# ================================================================================

def augment_dataset(csv_file, output_dir):
    """Balance dataset using augmentation"""
    print("\n" + "="*80)
    print("STEP 1: DATA AUGMENTATION")
    print("="*80)
    
    df = pd.read_csv(csv_file)
    print(f"\nOriginal dataset: {len(df)} files")
    print(f"Class distribution:\n{df['y'].value_counts()}\n")
    
    class_counts = df['y'].value_counts().to_dict()
    target_count = class_counts.get('hungry', 382)
    
    aug_dir = os.path.join(output_dir, 'aug_dataset')
    os.makedirs(aug_dir, exist_ok=True)
    
    audio_proc = AudioPreprocessor(sample_rate=config.TARGET_SAMPLE_RATE)
    
    for idx, row in tqdm(df.iterrows(), total=len(df), desc="Augmenting"):
        label = row['y']
        audio_path = row['x']
        
        label_dir = os.path.join(aug_dir, label)
        os.makedirs(label_dir, exist_ok=True)
        
        signal = audio_proc.read_audio(audio_path)
        if signal is None:
            continue
        
        if label == 'hungry':
            aug_count = 1
        else:
            class_count = class_counts.get(label, 10)
            aug_count = max(1, target_count // class_count)
        
        original_name = os.path.basename(audio_path)
        sf.write(
            os.path.join(label_dir, original_name),
            signal,
            config.TARGET_SAMPLE_RATE
        )
        
        for i in range(1, aug_count):
            augmented_signal = audio_proc.augment_audio(signal)
            aug_name = f"{os.path.splitext(original_name)[0]}_aug_{i}.wav"
            sf.write(
                os.path.join(label_dir, aug_name),
                augmented_signal,
                config.TARGET_SAMPLE_RATE
            )
    
    total_aug = sum(len(os.listdir(os.path.join(aug_dir, label))) 
                    for label in os.listdir(aug_dir) 
                    if os.path.isdir(os.path.join(aug_dir, label)))
    
    print(f"\n✓ Augmented dataset: {total_aug} files")
    print(f"✓ Location: {aug_dir}\n")
    
    return aug_dir

# ================================================================================
# STEP 2: FEATURE EXTRACTION
# ================================================================================

def extract_features(aug_dir, output_dir):
    """Extract MFCC features from augmented audio"""
    print("\n" + "="*80)
    print("STEP 2: FEATURE EXTRACTION")
    print("="*80)
    
    features_dir = os.path.join(output_dir, 'features')
    mfcc_dir = os.path.join(features_dir, 'mfcc')
    os.makedirs(mfcc_dir, exist_ok=True)
    
    X = []
    y = []
    
    audio_files = list(Path(aug_dir).rglob("*.wav"))
    print(f"\nExtracting from {len(audio_files)} files...")
    
    for audio_file in tqdm(audio_files, desc="Extracting MFCC"):
        try:
            label = audio_file.parent.name
            signal, sr = librosa.load(str(audio_file), sr=config.TARGET_SAMPLE_RATE)
            
            mfcc = librosa.feature.mfcc(
                y=signal, sr=sr, n_mfcc=20,
                fmin=300., fmax=600., n_mels=20, n_fft=1024
            )
            mfcc_mean = np.mean(mfcc, axis=1)
            mfcc_norm = (mfcc_mean - mfcc_mean.min()) / (mfcc_mean.max() - mfcc_mean.min() + 1e-8)
            
            X.append(mfcc_norm)
            y.append(label)
        except:
            continue
    
    X = np.array(X)
    y = np.array(y)
    
    print(f"\n✓ Features extracted: {X.shape}")
    print(f"✓ Class distribution:\n{pd.Series(y).value_counts()}\n")
    
    np.save(os.path.join(mfcc_dir, 'X.npy'), X)
    np.save(os.path.join(mfcc_dir, 'y.npy'), y)
    
    return X, y

# ================================================================================
# STEP 3: MODEL TRAINING
# ================================================================================

def train_models(X, y, output_dir):
    """Train multiple ML models"""
    print("\n" + "="*80)
    print("STEP 3: MODEL TRAINING")
    print("="*80)
    
    np.random.seed(config.SEED)
    
    X_train, X_test, y_train, y_test = train_test_split(
        X, y, test_size=0.2, random_state=config.SEED, stratify=y
    )
    
    print(f"\nTrain: {len(X_train)} | Test: {len(X_test)}")
    
    scoring = {
        "accuracy": "accuracy",
        "f1_macro": "f1_macro",
        "precision_macro": make_scorer(precision_score, labels=np.unique(y), average="macro", zero_division=0),
        "recall_macro": make_scorer(recall_score, labels=np.unique(y), average="macro", zero_division=0),
    }
    
    # FIXED: Removed 'multi_class' parameter for newer scikit-learn
    models_config = {
        "LR": {
            "model": LogisticRegression(class_weight="balanced", max_iter=1000, random_state=config.SEED),
            "params": {"LR__C": [0.1, 1, 10]}
        },
        "Ridge": {
            "model": RidgeClassifier(class_weight="balanced", random_state=config.SEED),
            "params": {"Ridge__alpha": [0.1, 1.0, 10.0]}
        },
        "DTC": {
            "model": DecisionTreeClassifier(criterion="entropy", class_weight="balanced", random_state=config.SEED),
            "params": {"DTC__max_depth": [5, 10, 15], "DTC__max_leaf_nodes": [20, 30]}
        },
        "RF": {
            "model": RandomForestClassifier(criterion="entropy", class_weight="balanced", random_state=config.SEED, n_jobs=-1),
            "params": {"RF__max_depth": [5, 10, 15], "RF__n_estimators": [50, 100]}
        },
        "NB": {
            "model": GaussianNB(),
            "params": {}
        },
        "KNN": {
            "model": KNeighborsClassifier(n_jobs=-1),
            "params": {"KNN__n_neighbors": [3, 5, 7]}
        },
        "SVC": {
            "model": SVC(class_weight='balanced', random_state=config.SEED, probability=True),
            "params": {"SVC__C": [0.1, 1, 10], "SVC__gamma": [0.001, 0.01]}
        },
    }
    
    results = {}
    models_dir = os.path.join(output_dir, 'models')
    os.makedirs(models_dir, exist_ok=True)
    
    print("\nTraining models...")
    for model_name, config_dict in models_config.items():
        print(f"\n{model_name}...", end=" ")
        
        try:
            pipeline = Pipeline([
                ("scaler", StandardScaler()),
                (model_name, config_dict["model"])
            ])
            
            # Handle empty params
            params = config_dict["params"] if config_dict["params"] else {}
            
            grid = GridSearchCV(
                estimator=pipeline,
                param_grid=params,
                cv=5,
                scoring=scoring,
                refit='accuracy',
                n_jobs=-1,
                verbose=0
            )
            
            grid.fit(X_train, y_train)
            best_model = grid.best_estimator_
            y_pred = best_model.predict(X_test)
            
            acc = accuracy_score(y_test, y_pred)
            precision_macro = precision_score(y_test, y_pred, average='macro', zero_division=0)
            recall_macro = recall_score(y_test, y_pred, average='macro', zero_division=0)
            f1_macro = f1_score(y_test, y_pred, average='macro', zero_division=0)
            
            results[model_name] = {
                'accuracy': acc,
                'precision_macro': precision_macro,
                'recall_macro': recall_macro,
                'f1_macro': f1_macro,
                'model': best_model,
                'best_params': grid.best_params_
            }
            
            joblib.dump(best_model, os.path.join(models_dir, f"{model_name}_model.pkl"))
            print(f"✓ Acc: {acc:.4f}, F1: {f1_macro:.4f}")
            
        except Exception as e:
            print(f"✗ Error: {e}")
            results[model_name] = {'error': str(e)}
    
    return results, X_test, y_test

# ================================================================================
# STEP 4: SAVE RESULTS
# ================================================================================

def save_results(results, X_test, y_test, output_dir):
    """Save and visualize results"""
    print("\n" + "="*80)
    print("STEP 4: RESULTS")
    print("="*80)
    
    results_dir = os.path.join(output_dir, 'results')
    os.makedirs(results_dir, exist_ok=True)
    
    results_data = []
    for model_name, result in results.items():
        if 'error' not in result:
            results_data.append({
                'Model': model_name,
                'Accuracy': result['accuracy'],
                'Precision': result['precision_macro'],
                'Recall': result['recall_macro'],
                'F1': result['f1_macro']
            })
    
    results_df = pd.DataFrame(results_data)
    results_df = results_df.sort_values('Accuracy', ascending=False)
    
    csv_path = os.path.join(results_dir, 'model_results.csv')
    results_df.to_csv(csv_path, index=False)
    
    print("\n" + results_df.to_string(index=False))
    print(f"\n✓ CSV saved: {csv_path}")
    
    # Plot
    try:
        fig, ax = plt.subplots(figsize=(12, 6))
        x_pos = np.arange(len(results_df))
        width = 0.2
        
        ax.bar(x_pos - width*1.5, results_df['Accuracy'], width, label='Accuracy', color='#2ecc71')
        ax.bar(x_pos - width*0.5, results_df['Precision'], width, label='Precision', color='#3498db')
        ax.bar(x_pos + width*0.5, results_df['Recall'], width, label='Recall', color='#e74c3c')
        ax.bar(x_pos + width*1.5, results_df['F1'], width, label='F1', color='#f39c12')
        
        ax.set_ylabel('Score', fontsize=12)
        ax.set_title('Model Comparison - Infant Crying Classification', fontsize=14, fontweight='bold')
        ax.set_xticks(x_pos)
        ax.set_xticklabels(results_df['Model'])
        ax.legend()
        ax.grid(axis='y', alpha=0.3)
        ax.set_ylim([0, 1.1])
        
        plot_path = os.path.join(results_dir, 'model_comparison.png')
        plt.savefig(plot_path, dpi=150, bbox_inches='tight')
        print(f"✓ Plot saved: {plot_path}")
        plt.close()
    except Exception as e:
        print(f"Warning: Could not create plot: {e}")
    
    # Best model
    if len(results_df) > 0:
        best_model_name = results_df.iloc[0]['Model']
        best_result = results[best_model_name]
        
        print("\n" + "="*80)
        print("BEST MODEL")
        print("="*80)
        print(f"Model: {best_model_name}")
        print(f"Accuracy: {best_result['accuracy']:.4f}")
        print(f"F1 (Macro): {best_result['f1_macro']:.4f}")
    
    return results_df

# ================================================================================
# MAIN
# ================================================================================

def main():
    parser = argparse.ArgumentParser(description='Infant Crying Classification')
    parser.add_argument('--dataset', type=str, default='dataset.csv', help='CSV file path')
    parser.add_argument('--output', type=str, default='results/', help='Output directory')
    
    args = parser.parse_args()
    
    print("\n" + "█"*80)
    print("█" + " "*78 + "█")
    print("█" + "  INFANT CRYING CLASSIFICATION PIPELINE".center(78) + "█")
    print("█" + " "*78 + "█")
    print("█"*80)
    
    aug_dir = augment_dataset(args.dataset, args.output)
    X, y = extract_features(aug_dir, args.output)
    results, X_test, y_test = train_models(X, y, args.output)
    save_results(results, X_test, y_test, args.output)
    
    print("\n" + "█"*80)
    print("█" + "  ✓ PIPELINE COMPLETED".center(78) + "█")
    print("█" + f"  Results: {args.output}".center(78) + "█")
    print("█"*80 + "\n")

if __name__ == "__main__":
    main()