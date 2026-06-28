from fastapi import APIRouter, Depends, HTTPException, WebSocket, WebSocketDisconnect
from sqlalchemy.orm import Session
from app.db.connection import get_db, SessionLocal
from app.db.models import Topology, SimulationRun
from app.core.engine import SimulationEngine
from typing import Dict
import asyncio
import json

router = APIRouter()

# Global Engine Instance
engine = SimulationEngine(SessionLocal)

# Active WebSocket connections per run
active_connections: Dict[str, list[WebSocket]] = {}

@router.post("/start/{topology_id}")
async def start_simulation(topology_id: str, db: Session = Depends(get_db)):
    t = db.query(Topology).filter(Topology.id == topology_id).first()
    if not t:
        raise HTTPException(status_code=404, detail="Topology not found")
    
    run = SimulationRun(topology_id=topology_id, status="RUNNING")
    db.add(run)
    db.commit()
    db.refresh(run)
    
    await engine.start_run(run.id, topology_id, t.nodes, t.edges)
    return {"run_id": run.id, "status": "Started"}

@router.post("/stop/{run_id}")
async def stop_simulation(run_id: str, db: Session = Depends(get_db)):
    await engine.stop_run(run_id)
    run = db.query(SimulationRun).filter(SimulationRun.id == run_id).first()
    if run:
        run.status = "COMPLETED"
        db.commit()
    return {"status": "Stopped"}

@router.post("/inject/{run_id}/{node_id}")
async def inject_fault(run_id: str, node_id: str, payload: dict):
    # payload: {"type": "null_injection", "severity": 0.4}
    fault_type = payload.get("type", "latency_spike")
    severity = payload.get("severity", 100.0)
    await engine.inject_fault(run_id, node_id, fault_type, severity)
    return {"status": "Fault Injected"}

@router.websocket("/ws/{run_id}")
async def websocket_endpoint(websocket: WebSocket, run_id: str):
    await websocket.accept()
    if run_id not in active_connections:
        active_connections[run_id] = []
    active_connections[run_id].append(websocket)
    
    try:
        while True:
            # Poll engine state and stream to client
            async with await engine.get_lock(run_id):
                if run_id in engine.active_runs:
                    run_state = engine.active_runs[run_id]
                    G = run_state["graph"]
                    
                    nodes_state = []
                    for n in G.nodes:
                        ndata = G.nodes[n]
                        nodes_state.append({
                            "id": n,
                            "status": ndata["status"],
                            "throughput": ndata.get("throughput", 0),
                            "latency": ndata.get("latency", 0),
                            "data_quality_score": ndata.get("data_quality_score", 1.0),
                            "anomaly_score": ndata.get("anomaly_score", 0.0)
                        })
                        
                    edges_state = []
                    for u, v in G.edges:
                        edata = G[u][v]
                        edges_state.append({
                            "source": u,
                            "target": v,
                            "status": edata["status"],
                            "weight": edata["routing_weight"]
                        })
                    
                    ai_core = engine.ai_cores.get(run_id)
                    centrality = ai_core.centrality_metrics if ai_core else {}
                        
                    payload = {
                        "tick": run_state["tick"],
                        "status": run_state["status"],
                        "nodes": nodes_state,
                        "edges": edges_state,
                        "centrality": centrality
                    }
                    
                    await websocket.send_json(payload)
                else:
                    await websocket.send_json({"status": "COMPLETED"})
                    break
            
            await asyncio.sleep(0.5) # Stream 2x per second
            
    except WebSocketDisconnect:
        active_connections[run_id].remove(websocket)
