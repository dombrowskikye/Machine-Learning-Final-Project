# Reckless driving predicition using Isolation Forest algorithm

import pandas as pd 
import sklearn
from sklearn.ensemble import IsolationForest

#Loading the CSV data from CARLA simulation of good and bad drivers

data = pd.read_csv('sensor_data_safe_and_reckless.csv')

data = data.dropna(subset=['x', 'y', 'z', 'velocity'])

# Reduce noise in the data
cleaned_features = data.groupby('vehicle_id')[['x', 'y', 'z', 'velocity']].mean().reset_index()

#Train the Isolation Forest model
model = IsolationForest(n_estimators=100, contamination=0.1, random_state=42)
model.fit(cleaned_features[['x', 'y', 'z', 'velocity']])

# Predict the reckless driving (using outliers) 
cleaned_features['anomaly'] = model.predict(cleaned_features[['x', 'y', 'z', 'velocity']])

# Get and print the reckless drivers
reckless_drivers = cleaned_features[cleaned_features['anomaly'] == -1]
print("Reckless drivers detected:")
for index, row in reckless_drivers.iterrows():
    print(f"Driver ID: {row['vehicle_id']}, Anomaly Score: {row['anomaly']}")

# Save the results to a CSV file
reckless_drivers[['vehicle_id', 'anomaly']].to_csv('reckless_drivers.csv', index=False)
