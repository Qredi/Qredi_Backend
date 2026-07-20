from contextlib import asynccontextmanager

from fastapi import FastAPI

from app.api.v1 import all_routers


@asynccontextmanager
async def lifespan(app: FastAPI):
    yield


app = FastAPI(
    title="Qredi Backend API",
    version="0.1.0",
    lifespan=lifespan,
)

for router in all_routers:
    app.include_router(router, prefix="/api/v1")


@app.get("/health")
def health():
    return {"status": "Backend Service is Running"}