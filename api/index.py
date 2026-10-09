from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
import math

app = FastAPI()

# Allow browser dashboards from any origin to call this endpoint.
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=False,
    allow_methods=["POST", "OPTIONS"],
    allow_headers=["*"],
)

# Telemetry sample bundled into the function so no runtime file access is needed.
TELEMETRY = [{"region":"apac","service":"recommendations","latency_ms":223.28,"uptime_pct":98.677,"timestamp":20250301},{"region":"apac","service":"checkout","latency_ms":221.32,"uptime_pct":98.563,"timestamp":20250302},{"region":"apac","service":"payments","latency_ms":139.19,"uptime_pct":97.473,"timestamp":20250303},{"region":"apac","service":"support","latency_ms":140.07,"uptime_pct":97.692,"timestamp":20250304},{"region":"apac","service":"payments","latency_ms":111.91,"uptime_pct":97.471,"timestamp":20250305},{"region":"apac","service":"checkout","latency_ms":159.42,"uptime_pct":97.557,"timestamp":20250306},{"region":"apac","service":"analytics","latency_ms":192.05,"uptime_pct":97.356,"timestamp":20250307},{"region":"apac","service":"recommendations","latency_ms":205.18,"uptime_pct":98.095,"timestamp":20250308},{"region":"apac","service":"catalog","latency_ms":181.11,"uptime_pct":97.78,"timestamp":20250309},{"region":"apac","service":"analytics","latency_ms":213.52,"uptime_pct":98.862,"timestamp":20250310},{"region":"apac","service":"support","latency_ms":190.24,"uptime_pct":98.582,"timestamp":20250311},{"region":"apac","service":"payments","latency_ms":184.49,"uptime_pct":98.642,"timestamp":20250312},{"region":"emea","service":"support","latency_ms":184.53,"uptime_pct":99.225,"timestamp":20250301},{"region":"emea","service":"analytics","latency_ms":161.59,"uptime_pct":97.408,"timestamp":20250302},{"region":"emea","service":"support","latency_ms":180.92,"uptime_pct":97.753,"timestamp":20250303},{"region":"emea","service":"payments","latency_ms":193.89,"uptime_pct":97.619,"timestamp":20250304},{"region":"emea","service":"payments","latency_ms":129.93,"uptime_pct":98.604,"timestamp":20250305},{"region":"emea","service":"analytics","latency_ms":176.91,"uptime_pct":97.89,"timestamp":20250306},{"region":"emea","service":"checkout","latency_ms":196.23,"uptime_pct":98.376,"timestamp":20250307},{"region":"emea","service":"support","latency_ms":180.74,"uptime_pct":98.135,"timestamp":20250308},{"region":"emea","service":"catalog","latency_ms":160.98,"uptime_pct":99.3,"timestamp":20250309},{"region":"emea","service":"payments","latency_ms":232.47,"uptime_pct":99.235,"timestamp":20250310},{"region":"emea","service":"analytics","latency_ms":169.89,"uptime_pct":99.282,"timestamp":20250311},{"region":"emea","service":"support","latency_ms":188.78,"uptime_pct":97.167,"timestamp":20250312},{"region":"amer","service":"catalog","latency_ms":164.2,"uptime_pct":98.309,"timestamp":20250301},{"region":"amer","service":"checkout","latency_ms":181,"uptime_pct":98.916,"timestamp":20250302},{"region":"amer","service":"support","latency_ms":197.31,"uptime_pct":97.644,"timestamp":20250303},{"region":"amer","service":"analytics","latency_ms":198.89,"uptime_pct":97.188,"timestamp":20250304},{"region":"amer","service":"support","latency_ms":216.14,"uptime_pct":97.18,"timestamp":20250305},{"region":"amer","service":"analytics","latency_ms":211.13,"uptime_pct":99.081,"timestamp":20250306},{"region":"amer","service":"analytics","latency_ms":188.83,"uptime_pct":97.49,"timestamp":20250307},{"region":"amer","service":"payments","latency_ms":140.54,"uptime_pct":97.787,"timestamp":20250308},{"region":"amer","service":"recommendations","latency_ms":185.96,"uptime_pct":97.344,"timestamp":20250309},{"region":"amer","service":"checkout","latency_ms":146.71,"uptime_pct":97.523,"timestamp":20250310},{"region":"amer","service":"catalog","latency_ms":149.77,"uptime_pct":98.785,"timestamp":20250311},{"region":"amer","service":"analytics","latency_ms":240.85,"uptime_pct":98.638,"timestamp":20250312}]

def percentile(values, p):
    """Linear-interpolated percentile (same convention as numpy.percentile)."""
    values = sorted(values)
    if not values:
        return None
    if len(values) == 1:
        return float(values[0])
    position = (len(values) - 1) * p / 100
    lower = math.floor(position)
    upper = math.ceil(position)
    if lower == upper:
        return float(values[lower])
    fraction = position - lower
    return float(values[lower] + (values[upper] - values[lower]) * fraction)

@app.post("/")
async def latency_metrics(request: Request):
    try:
        body = await request.json()
    except Exception:
        return JSONResponse({"error": "Request body must be valid JSON"}, status_code=400)

    regions = body.get("regions")
    threshold = body.get("threshold_ms", 180)

    if not isinstance(regions, list) or not all(isinstance(r, str) for r in regions):
        return JSONResponse({"error": "'regions' must be a list of region names"}, status_code=400)
    if not isinstance(threshold, (int, float)) or isinstance(threshold, bool):
        return JSONResponse({"error": "'threshold_ms' must be numeric"}, status_code=400)

    result = {}
    for region in regions:
        rows = [r for r in TELEMETRY if r["region"] == region]
        if not rows:
            result[region] = {
                "avg_latency": None,
                "p95_latency": None,
                "avg_uptime": None,
                "breaches": 0
            }
            continue

        latencies = [float(r["latency_ms"]) for r in rows]
        uptimes = [float(r["uptime_pct"]) for r in rows]
        result[region] = {
            "avg_latency": sum(latencies) / len(latencies),
            "p95_latency": percentile(latencies, 95),
            "avg_uptime": sum(uptimes) / len(uptimes),
            "breaches": sum(1 for value in latencies if value > threshold)
        }

    return result

@app.options("/")
async def options_root():
    return JSONResponse({"ok": True})
