import joblib
import pandas as pd
import processing as p
import Features2 as f
import time
from scipy.io.wavfile import write
loaded_model = joblib.load('my_ml_model.joblib')
prediction = " "
def AudioML(log_callback=None):
    # Listen for a maximum of 5 minutes (300 seconds) before stopping automatically
    input_file = p.go(timeout_seconds=10, short_sample_duration= 0.03, long_sample_duration=10,log_callback=log_callback)

    if input_file is None:
        #print("No audio was caught during the listening period.")
        prediction = ["N"]
    else :
    # Run your saving and feature extraction steps here
        #print("Audio captured successfully!")

        temp_path = "temp_live_audio.wav"
        write(temp_path, 22050, input_file)
        #print("Temporary saving is Done!")

        output_list= []
        f.featureextraction(temp_path,output_list)
        output_df=pd.DataFrame(f.featureextraction(temp_path,output_list))
        single_input = output_df.loc[:, "f0_mean":]

        prediction = loaded_model.predict(single_input)
        output_list= []
        #print(f"The model prediction for this file is: {prediction[0]}")
    return(prediction[0])