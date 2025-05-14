import pandas as pd
import numpy as np
from sklearn.model_selection import train_test_split
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import classification_report
from sklearn.preprocessing import LabelEncoder

# === Load the CSV files ===
safe_df = pd.read_csv('safe_radar_data.csv')
unsafe_df = pd.read_csv('unsafe_radar_data.csv')

# Label Encoding 
# Convert labels to numeric: 'safe' -> 0, 'unsafe' -> 1
safe_df['label'] = 'safe'
unsafe_df['label'] = 'unsafe'

df = pd.concat([safe_df, unsafe_df], ignore_index=True)
df['label'] = LabelEncoder().fit_transform(df['label'])     # safe = 0 , unsafe = 1

# === Sort and Compute Features ===
df_sorted = df.sort_values(by=['vehicle_id', 'timestamp']).copy()
df_sorted['dt'] = df_sorted.groupby('vehicle_id')['timestamp'].diff()

# Filter out invalid dt values
df_sorted = df_sorted[df_sorted['dt'] > 0]

# Compute acceleration and jerk
df_sorted['acceleration'] = df_sorted.groupby('vehicle_id')['velocity'].diff() / df_sorted['dt']
df_sorted['jerk'] = df_sorted.groupby('vehicle_id')['acceleration'].diff() / df_sorted['dt']

# Drop rows with NaNs or infinite values
df_clean = df_sorted.dropna(subset=['acceleration', 'jerk'])
df_clean = df_clean[np.isfinite(df_clean['acceleration']) & np.isfinite(df_clean['jerk'])]

# Feature Selection 
X = df_clean[['x', 'y', 'z', 'velocity', 'azimuth', 'acceleration', 'jerk']]
y = df_clean['label']


# Train/Test Split 
X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, random_state=42)

# Train the Model
model = LogisticRegression(max_iter=1000)
model.fit(X_train, y_train)

# Evaluation
y_pred = model.predict(X_test)
report = classification_report(y_test, y_pred)
print("=== Logistic Regression Classification Report ===")
print(report)
