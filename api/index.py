from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
import numpy as np
import json
import os

app = FastAPI()

# Enable CORS for all origins and POST methods
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["POST", "OPTIONS"],
    allow_headers=["*"],
)

# Load the telemetry data
# Vercel places the root files in the same relative path
data_path = os.path.join(os.path.dirname(__file__), "..", "telemetry.json")
with open(data_path, "r") as f:
    telemetry_data = json.load(f)

class LatencyQuery(BaseModel):
    regions: list[str]
    threshold_ms: float

@app.post("/api/metrics")
async def get_metrics(query: LatencyQuery):
    response = {}
    
    for reg in query.regions:
        # Filter records for the current region
        subset = [d for d in telemetry_data if d['region'] == reg]
        
        if not subset:
            continue
            
        latencies = [d['latency_ms'] for d in subset]
        uptimes = [d['uptime_pct'] for d in subset]
        
        # Calculate statistics
        avg_lat = float(np.mean(latencies))
        p95_lat = float(np.percentile(latencies, 95))
        avg_uptime = float(np.mean(uptimes))
        breaches = sum(1 for lat in latencies if lat > query.threshold_ms)
        
        response[reg] = {
            "avg_latency": avg_lat,
            "p95_latency": p95_lat,
            "avg_uptime": avg_uptime,
            "breaches": breaches
        }
        
    return response