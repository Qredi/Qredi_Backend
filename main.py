from contextlib import asynccontextmanager

from fastapi import FastAPI

from app.api.v1 import all_routers

from fastapi.middleware.cors import CORSMiddleware

@asynccontextmanager
async def lifespan(app: FastAPI):
    yield


app = FastAPI(
    title="Qredi Backend API",
    version="0.1.0",
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

for router in all_routers:
    app.include_router(router, prefix="/api/v1")


@app.get("/health")
def health():
    return {"status": "Backend Service is Running"}