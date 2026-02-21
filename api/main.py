from fastapi import FastAPI, Response
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import List
import json
import os
import numpy as np

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

# Root route to verify the app is not 404
@app.get("/")
async def health():
    return {"status": "ok"}

# Load data from the root directory
def load_data():
    # Vercel path logic: look in the parent directory of this file
    path = os.path.join(os.getcwd(), "telemetry.json")
    with open(path, "r") as f:
        return json.load(f)

data_store = load_data()

class MetricsRequest(BaseModel):
    regions: List[str]
    threshold_ms: float

@app.post("/api/latency")
async def get_latency(req: MetricsRequest, response: Response):
    # Explicitly set CORS header in response body
    response.headers["Access-Control-Allow-Origin"] = "*"
    
    results = {}
    for r in req.regions:
        subset = [x for x in data_store if x['region'] == r]
        if not subset:
            continue
            
        lats = [x['latency_ms'] for x in subset]
        uptimes = [x['uptime_pct'] for x in subset]
        
        results[r] = {
            "avg_latency": round(float(np.mean(lats)), 2),
            "p95_latency": round(float(np.percentile(lats, 95)), 2),
            "avg_uptime": round(float(np.mean(uptimes)), 4),
            "breaches": sum(1 for l in lats if l > req.threshold_ms)
        }
    return results