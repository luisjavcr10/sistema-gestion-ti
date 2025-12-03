from fastapi import FastAPI, Request, HTTPException, Response
from fastapi.middleware.cors import CORSMiddleware
import httpx
import os
from dotenv import load_dotenv

load_dotenv()

app = FastAPI(title="API Gateway - Sistema Gestión TI")

# CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Service URLs
SERVICES = {
    "equipos": os.getenv("EQUIPOS_SERVICE_URL", "http://equipos-service:8001"),
    "proveedores": os.getenv("PROVEEDORES_SERVICE_URL", "http://proveedores-service:8002"),
    "mantenimientos": os.getenv("MANTENIMIENTO_SERVICE_URL", "http://mantenimiento-service:8003"),
    "reportes": os.getenv("REPORTES_SERVICE_URL", "http://reportes-service:8004"),
    "agents": os.getenv("AGENT_SERVICE_URL", "http://agent-service:8005"),
}

client = httpx.AsyncClient()

@app.on_event("shutdown")
async def shutdown_event():
    await client.aclose()

@app.get("/health")
async def health_check():
    # Check all services
    status = {}
    for name, url in SERVICES.items():
        try:
            resp = await client.get(f"{url}/health", timeout=2.0)
            status[name] = "up" if resp.status_code == 200 else "down"
        except:
            status[name] = "down"
    return {"gateway": "up", "services": status}

async def proxy_request(service_name: str, path: str, request: Request, response: Response):
    url = f"{SERVICES[service_name]}/{path}"
    
    # Forward query params
    params = dict(request.query_params)
    
    # Forward body
    content = await request.body()
    
    try:
        rp_req = client.build_request(
            request.method,
            url,
            headers=request.headers.raw,
            content=content,
            params=params
        )
        rp_resp = await client.send(rp_req)
        
        # Exclude some headers
        excluded_headers = ['content-encoding', 'content-length', 'transfer-encoding', 'connection']
        headers = {k: v for k, v in rp_resp.headers.items() if k.lower() not in excluded_headers}
                
        return Response(content=rp_resp.content, status_code=rp_resp.status_code, headers=headers)
    except httpx.RequestError as exc:
        raise HTTPException(status_code=503, detail=f"Service {service_name} unavailable: {str(exc)}")

# Routes
@app.api_route("/api/equipos/{path:path}", methods=["GET", "POST", "PUT", "DELETE"])
async def equipos_proxy(path: str, request: Request, response: Response):
    return await proxy_request("equipos", path, request, response)

@app.api_route("/api/proveedores/{path:path}", methods=["GET", "POST", "PUT", "DELETE"])
async def proveedores_proxy(path: str, request: Request, response: Response):
    return await proxy_request("proveedores", path, request, response)

@app.api_route("/api/mantenimientos/{path:path}", methods=["GET", "POST", "PUT", "DELETE"])
async def mantenimientos_proxy(path: str, request: Request, response: Response):
    return await proxy_request("mantenimientos", path, request, response)

@app.api_route("/api/reportes/{path:path}", methods=["GET", "POST"])
async def reportes_proxy(path: str, request: Request, response: Response):
    return await proxy_request("reportes", path, request, response)

@app.api_route("/api/agents/{path:path}", methods=["GET", "POST", "PUT"])
async def agents_proxy(path: str, request: Request, response: Response):
    return await proxy_request("agents", path, request, response)
