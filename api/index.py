from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import List, Dict
import pandas as pd
import os

app = FastAPI()

# Enable CORS for all origins and POST methods
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["POST", "OPTIONS"],
    allow_headers=["*"],
)

# Load data into memory (Ensure telemetry.csv is in the root or same folder)
# Vercel's current working directory is the project root
csv_path = os.path.join(os.getcwd(), "telemetry.csv")
df = pd.read_csv(csv_path)

class LatencyRequest(BaseModel):
    regions: List[str]
    threshold_ms: int

@app.post("/api/metrics")
async def calculate_metrics(request: LatencyRequest):
    response_data = {}
    
    for region in request.regions:
        # Filter dataframe by region
        region_data = df[df['region'] == region]
        
        if region_data.empty:
            continue
            
        # Calculate Metrics
        avg_lat = region_data['latency_ms'].mean()
        p95_lat = region_data['latency_ms'].quantile(0.95)
        avg_uptime = region_data['uptime'].mean()
        breaches = int((region_data['latency_ms'] > request.threshold_ms).sum())
        
        response_data[region] = {
            "avg_latency": float(round(avg_lat, 2)),
            "p95_latency": float(round(p95_lat, 2)),
            "avg_uptime": float(round(avg_uptime, 4)),
            "breaches": breaches
        }
        
    return response_data