# Machine-Learning-Final-Project
 ## **Mathew Frayre and Kye Dombrowski's Final Project Repo**


* This README includes instructions on how to re-create test data and test the model algorithms. Test data sets will be provided incase datasets aren't able to be recreated with CARLA. 

* The project repository and folder contains many utility scripts that were used to aid the development process and can be ignored! 


**Downloading Carla**

* Carla 0.9.13 Instructions Link (long process and only necessary for data collection): https://carla.readthedocs.io/en/0.9.13/


**Logistic Regression Driver Behavior Classification (CARLA)**

This project uses CARLA to simulate safe and unsafe driving behavior, collects radar-based sensor data, and trains a logistic regression model to classify drivers.

------------------------------------------------------------

Requirements:
- Python 3.7
- CARLA Simulator installed and running (tested on Town01)
- All required Python libraries are listed in requirements.txt

To install dependencies:
pip install -r requirements.txt

------------------------------------------------------------

**Running the Data Collection:**

1. Start the CARLA server before running any scripts.

2. Run the following two scripts in separate terminals:
   - safe_radar_logger_v1.py
   - unsafe_radar_logger_v2.py

   These scripts will automatically:
   - Spawn vehicles (safe and unsafe behavior, respectively)
   - Attach a radar sensor
   - Log detection data to output/safe_radar_data.csv and output/unsafe_radar_data.csv

------------------------------------------------------------

**Running Logistic Regression:**

Once the data is collected:

1. Ensure the following files are in the same directory as logistic_regression.py:
   - safe_radar_data.csv
   - unsafe_radar_data.csv

2. Run the script:
python logistic_regression.py

3. This will:
   - Merge and label the radar data
   - Calculate motion features like acceleration and jerk
   - Train and evaluate a logistic regression model
   - Print a classification report

------------------------------------------------------------

**How It Works:**

Both safe_radar_logger_v1.py and unsafe_radar_logger_v2.py:

- Load the CARLA world Town01
- Position the spectator (you) at the same location as the radar sensor
- Begin a loop for a hardcoded duration (TOTAL_RUNTIME)
- Continuously spawn vehicles for the radar to detect as they pass by
- Log detections to .csv files in the output/ folder
- Stop data collection after the time expires or vehicle spawn limit is reached

After collecting data:

- Place both CSV outputs in the same directory as logistic_regression.py
- The script:
  - Merges the data and encodes labels (safe = 0, unsafe = 1)
  - Computes extra features: acceleration and jerk
  - Performs an 80/20 train-test split
  - Trains a logistic regression model
  - Outputs a classification report


**Isolation Forest Driver Behavior with CARLA**

* Isoaltion forest algorithm is trained with data collected with CARLA. This approach is targetted at classifying drivers as safe or reckless. 

---------------------------------------------------------

**Getting Started:**

1. Make sure you are running Python 3.7 
2. Make sure CARLA is downloaded and running (only if you want to collect driving data)
3. Download requirements from the requirements.txt file (pip install -r requirements.txt)

**Collection Data** 

1. Start CARLA. 
2. Run data collection scripts separately. 
    - safe_driving.py
    - safe_and_reckless_driving.py\
3. The scripts from step 2 will produce two data files to use for model training. 

**Training the Isolation Forest Model** 

1. Ensure these data files exist:
    - sensor_data_safe_and_reckless.csv 
    - safe_driving_data.csv 

2. Ensure those files are in the same directory as:
    - reckless_driving_IF.py

3. Run reckless_driving_IF.py

4. Observe the classified reckless drivers in the terminal and a CSV output file. 

**MODEL INFORMATION** 

* Model is trained from a baseline safe driving file. The safe driving contains only safe driving behaviors. 
* Model is fed a dataset including safe and unsafe driving behaviors to predict if the driver is reckless. 
* Model is tested on its validity with a column in the data with the true classification. 


**Isolation Forest Metrics**

              precision    recall  f1-score   

        Safe       0.71      0.83      0.77         
    Reckless       0.00      0.00      0.00         
    accuracy                           0.62         
   macro avg       0.36      0.42      0.38         
weighted avg       0.54      0.62      0.58         


