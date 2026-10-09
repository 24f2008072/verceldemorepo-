# eShopCo latency metrics API

## Deploy
1. Create a GitHub repository and upload these files, preserving the `api/index.py` path.
2. Import the repository into Vercel and deploy.
3. The POST endpoint is `https://YOUR-VERCEL-PROJECT.vercel.app/`.

## Request
```json
{"regions":["apac","amer"],"threshold_ms":180}
```

The response contains `avg_latency`, `p95_latency`, `avg_uptime`, and `breaches` for each requested region. CORS allows POST and OPTIONS from any origin.
