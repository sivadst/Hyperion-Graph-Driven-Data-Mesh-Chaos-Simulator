import pytest
import asyncio
import json
from app.core.engine import SimulationEngine
from app.db.connection import Base, engine, SessionLocal
from app.db.models import Topology, Node, Edge

@pytest.fixture(scope="session", autouse=True)
def setup_db():
    Base.metadata.create_all(bind=engine)
    yield
    Base.metadata.drop_all(bind=engine)

@pytest.mark.asyncio
async def test_simulation_engine_run():
    sim_engine = SimulationEngine(SessionLocal)
    
    # Mock data
    nodes = [
        Node(id="n1", name="Source", node_type="KAFKA", config_json="{}"),
        Node(id="n2", name="Target", node_type="SPARK", config_json="{}")
    ]
    edges = [
        Edge(id="e1", source_node_id="n1", target_node_id="n2")
    ]
    
    await sim_engine.start_run("test_run", "test_topology", nodes, edges)
    
    await asyncio.sleep(0.5) # Let tick loop run a few times
    
    assert "test_run" in sim_engine.active_runs
    state = sim_engine.active_runs["test_run"]
    assert state["status"] == "RUNNING"
    assert state["tick"] > 0
    
    await sim_engine.inject_fault("test_run", "n1", "latency_spike", 500)
    
    await asyncio.sleep(0.5)
    
    # Verify fault applied
    G = state["graph"]
    assert any(f["type"] == "latency_spike" for f in G.nodes["n1"]["faults"])
    
    await sim_engine.stop_run("test_run")
    assert state["status"] == "COMPLETED"

