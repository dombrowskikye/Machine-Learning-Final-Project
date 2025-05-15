# Reckless driving predicition using Isolation Forest algorithm

import pandas as pd 
import sklearn
from sklearn.ensemble import IsolationForest
from sklearn.metrics import classification_report, confusion_matrix

#Loading the CSV data from CARLA simulation of good drivers

safe_data = pd.read_csv('safe_driving_data.csv')
safe_data = safe_data.dropna(subset=['x', 'y', 'z', 'velocity'])

# Reduce noise in the data
cleaned_features = safe_data.groupby('vehicle_id')[['x', 'y', 'z', 'velocity']].mean().reset_index()

#Train the Isolation Forest model
model = IsolationForest(n_estimators=100, contamination=0.1, random_state=42)
model.fit(cleaned_features[['x', 'y', 'z', 'velocity']])

# Predict the reckless driving (using outliers) from the safe and reckless driving data
safe_reckless = pd.read_csv('sensor_data_safe_and_reckless.csv')
safe_reckless = safe_reckless.dropna(subset=['x', 'y', 'z', 'velocity'])
safe_reckless_cleaned = safe_reckless.groupby('vehicle_id')[['x', 'y', 'z', 'velocity']].mean().reset_index()

# Ammend labels for the reckless driving
driving_behavior = safe_reckless[['vehicle_id', 'reckless_driving']].drop_duplicates()
safe_reckless_cleaned = safe_reckless_cleaned.merge(driving_behavior, on='vehicle_id', how='left')

# Predict the reckless drivers  
safe_reckless_cleaned['anomaly'] = model.predict(safe_reckless_cleaned[['x', 'y', 'z', 'velocity']])

#convert the IF labels from -1 and 1 to 0 and 1 for ease of running metrics
safe_reckless_cleaned['predicted_label'] = safe_reckless_cleaned['anomaly'].apply(lambda x: 1 if x == -1 else 0)

#Run model metrics
print(classification_report(safe_reckless_cleaned['reckless_driving'], safe_reckless_cleaned['predicted_label'], target_names=['Safe', 'Reckless']))
print(confusion_matrix(safe_reckless_cleaned['reckless_driving'], safe_reckless_cleaned['predicted_label']))


# Get and print the reckless drivers
reckless_drivers = safe_reckless_cleaned[safe_reckless_cleaned['anomaly'] == -1]
print("Reckless drivers detected:")
for index, row in reckless_drivers.iterrows():
    print(f"Driver ID: {row['vehicle_id']}, Anomaly Score: {row['anomaly']}")

# Save the results to a CSV file
reckless_drivers[['vehicle_id', 'anomaly']].to_csv('reckless_drivers.csv', index=False)
