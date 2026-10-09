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
TELEMETRY = [{"region":"apac","service":"recommendations","latency_ms":223.28,"uptime_pct":98.677,"timestamp":20250301},{"region":"apac","service":"checkout","latency_ms":221.32,"uptime_pct":98.563,"timestamp":20250302},{"region":"apac","service":"support","latency_ms":245.1,"uptime_pct":97.823,"timestamp":20250303},{"region":"amer","service":"recommendations","latency_ms":187.9,"uptime_pct":99.31,"timestamp":20250301},{"region":"amer","service":"checkout","latency_ms":174.55,"uptime_pct":99.472,"timestamp":20250302},{"region":"amer","service":"support","latency_ms":196.23,"uptime_pct":99.008,"timestamp":20250303},{"region":"emea","service":"recommendations","latency_ms":212.64,"uptime_pct":98.912,"timestamp":20250301},{"region":"emea","service":"checkout","latency_ms":208.77,"uptime_pct":99.113,"timestamp":20250302},{"region":"emea","service":"support","latency_ms":219.88,"uptime_pct":98.741,"timestamp":20250303}]


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

    if not isinstance(body, dict):
        return JSONResponse({"error": "Request body must be a JSON object"}, status_code=400)

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
                "breaches": 0,
            }
            continue

        latencies = [float(r["latency_ms"]) for r in rows]
        uptimes = [float(r["uptime_pct"]) for r in rows]
        result[region] = {
            "avg_latency": sum(latencies) / len(latencies),
            "p95_latency": percentile(latencies, 95),
            "avg_uptime": sum(uptimes) / len(uptimes),
            "breaches": sum(1 for value in latencies if value > threshold),
        }

    return result


@app.options("/")
async def options_root():
    return JSONResponse({"ok": True})
