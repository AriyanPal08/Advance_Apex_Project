import pandas as pd
import numpy as np
import json
from sklearn.preprocessing import MinMaxScaler
import os

df = pd.read_csv("cfpb_raw_2022_2024.csv")

metrics = {}

# Step 3: Dataset Inspection
metrics['before_rows'] = len(df)
metrics['before_cols'] = len(df.columns)
metrics['before_nulls'] = int(df.isnull().sum().sum())
metrics['before_duplicates'] = int(df.duplicated(subset=['Complaint ID']).sum())

# Step 4: Duplicate Removal
df = df.drop_duplicates(subset=['Complaint ID'])

# Step 5: Date Standardization
df['Date received'] = pd.to_datetime(df['Date received'], errors='coerce', format='mixed')
df['Date sent to company'] = pd.to_datetime(df['Date sent to company'], errors='coerce', format='mixed')

# Step 6: Create resolution_days
df['resolution_days'] = (df['Date sent to company'] - df['Date received']).dt.days
metrics['negative_resolution_days'] = int((df['resolution_days'] < 0).sum())
df.loc[df['resolution_days'] < 0, 'resolution_days'] = np.nan

# Step 7: Standardize Product, Issue
df['Product'] = df['Product'].str.strip().str.title()
df['Issue'] = df['Issue'].str.strip().str.title()

# Step 8: Handle Missing Values
df['State'] = df['State'].fillna('Unknown')
df['ZIP code'] = df['ZIP code'].fillna('Unknown')
df['Company response to consumer'] = df['Company response to consumer'].fillna('No Response')
df['Timely response?'] = df['Timely response?'].fillna('Unknown')

df['has_narrative'] = df['Consumer complaint narrative'].notnull().astype(int)

# Step 9: Encoding
timely_map = {'Yes': 1, 'No': 0, 'Unknown': -1}
df['Timely response?'] = df['Timely response?'].map(timely_map)

df['Product_encoded'] = pd.Categorical(df['Product']).codes

# Step 10: MinMaxScaler
scaler = MinMaxScaler()
df['resolution_days_original'] = df['resolution_days']
df['resolution_days'] = scaler.fit_transform(df[['resolution_days']])

# Step 11: AFTER snapshot
metrics['after_rows'] = len(df)
metrics['after_cols'] = len(df.columns)
metrics['after_nulls'] = int(df.isnull().sum().sum())
metrics['after_duplicates'] = int(df.duplicated(subset=['Complaint ID']).sum())

# Key Findings Info
top_products = df['Product'].value_counts().head(10).to_dict()
top_states = df['State'].value_counts().head(15).to_dict()

# timely response rate by company response
timely_rates = df.groupby('Company response to consumer')['Timely response?'].apply(lambda x: (x == 1).mean()).to_dict()

metrics['top_products'] = top_products
metrics['top_states'] = top_states
metrics['timely_rates'] = timely_rates

with open("metrics.json", "w") as f:
    json.dump(metrics, f, indent=4)

df.to_csv("clean_compliance_data.csv", index=False)
print("Done writing metrics.json and clean_compliance_data.csv")
