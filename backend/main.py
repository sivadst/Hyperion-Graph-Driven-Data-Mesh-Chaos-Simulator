from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.db.connection import Base, engine
from app.routers import topology, simulation

Base.metadata.create_all(bind=engine)

app = FastAPI(title="Hyperion API")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(topology.router, prefix="/api/topology", tags=["Topology"])
app.include_router(simulation.router, prefix="/api/simulation", tags=["Simulation"])

@app.get("/health")
def health():
    return {"status": "ok"}
