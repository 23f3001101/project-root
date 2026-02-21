from fastapi import FastAPI, Response
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import List
import json
import os
import numpy as np

app = FastAPI()

# 1. Standard CORS Middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# 2. Load the data from YOUR telemetry.json
# This path works on Vercel to find files in the project root
data_path = os.path.join(os.getcwd(), "telemetry.json")
with open(data_path, "r") as f:
    raw_data = json.load(f)

class MetricsRequest(BaseModel):
    regions: List[str]
    threshold_ms: float

# 3. Manual OPTIONS handler (Sometimes needed to satisfy strict CORS tests)
@app.options("/api/metrics")
async def preflight():
    return Response(
        status_code=200,
        headers={
            "Access-Control-Allow-Origin": "*",
            "Access-Control-Allow-Methods": "POST, OPTIONS",
            "Access-Control-Allow-Headers": "*",
        },
    )

@app.post("/api/metrics")
async def get_metrics(req: MetricsRequest):
    output = {}
    
    for region_name in req.regions:
        # Filter the JSON data for the specific region
        region_subset = [d for d in raw_data if d['region'] == region_name]
        
        if not region_subset:
            continue
            
        lats = [d['latency_ms'] for d in region_subset]
        uptimes = [d['uptime_pct'] for d in region_subset]
        
        # Calculate exactly as required
        avg_lat = float(np.mean(lats))
        p95_lat = float(np.percentile(lats, 95))
        avg_uptime = float(np.mean(uptimes))
        # Breaches: Count of records where latency is STRICTLY ABOVE threshold
        breaches_count = sum(1 for lat in lats if lat > req.threshold_ms)
        
        output[region_name] = {
            "avg_latency": round(avg_lat, 2),
            "p95_latency": round(p95_lat, 2),
            "avg_uptime": round(avg_uptime, 4),
            "breaches": breaches_count
        }
        
    return output