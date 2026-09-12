#!/usr/bin/env python
# -*- coding: utf-8 -*-

import os
import joblib

# Paths to your model files
INPUT_MODEL_PATH = "/home/habib/mindcloud/project/results/models/RF_model.pkl"      # Path to existing model
OUTPUT_MODEL_PATH = "/home/habib/mindcloud/project/results/results/RF_model.joblib"  # New output path

def convert_pkl_to_joblib(input_path, output_path):
    if not os.path.exists(input_path):
        print(f"Error: Could not find file at '{input_path}'")
        return

    print(f"Loading model from: {input_path}...")
    # Load the serialized Scikit-Learn pipeline
    model = joblib.load(input_path)

    print(f"Saving model to: {output_path}...")
    # Re-save with .joblib extension
    joblib.dump(model, output_path)

    print("✓ Conversion complete!")

if __name__ == "__main__":
    convert_pkl_to_joblib(INPUT_MODEL_PATH, OUTPUT_MODEL_PATH)