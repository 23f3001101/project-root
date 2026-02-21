from fastapi import FastAPI, Response, Body
from pydantic import BaseModel
from typing import List
import json
import os
import numpy as np

app = FastAPI()

# Your prescribed CORS headers
CORS_HEADERS = {
    "Access-Control-Allow-Origin": "*",
    "Access-Control-Allow-Methods": "POST, GET, OPTIONS",
    "Access-Control-Allow-Headers": "Content-Type, Authorization",
    "Access-Control-Expose-Headers": "Access-Control-Allow-Origin",
}

# Load the telemetry data from the project root
data_path = os.path.join(os.getcwd(), "telemetry.json")
try:
    with open(data_path, "r") as f:
        telemetry_data = json.load(f)
except Exception:
    telemetry_data = []

class LatencyRequest(BaseModel):
    regions: List[str]
    threshold_ms: float

@app.get("/")
async def health(response: Response):
    for k, v in CORS_HEADERS.items():
        response.headers[k] = v
    return {"status": "online"}

# Manual OPTIONS handler for Preflight requests
@app.options("/api/metrics")
async def preflight():
    return Response(status_code=200, headers=CORS_HEADERS)

@app.post("/api/metrics")
async def get_metrics(req: LatencyRequest, response: Response):
    # Apply your specific CORS headers to the response
    for k, v in CORS_HEADERS.items():
        response.headers[k] = v
    
    output = {}
    for region in req.regions:
        # Filter JSON data for the region
        subset = [d for d in telemetry_data if d['region'] == region]
        
        if not subset:
            continue
            
        lats = [d['latency_ms'] for d in subset]
        uptimes = [d['uptime_pct'] for d in subset]
        
        output[region] = {
            "avg_latency": round(float(np.mean(lats)), 2),
            "p95_latency": round(float(np.percentile(lats, 95)), 2),
            "avg_uptime": round(float(np.mean(uptimes)), 4),
            "breaches": sum(1 for lat in lats if lat > req.threshold_ms)
        }
    
    return output