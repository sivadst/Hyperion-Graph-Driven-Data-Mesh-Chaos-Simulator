from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from app.db.connection import get_db
from app.db.models import Topology, Node, Edge
import json

router = APIRouter()

def seed_default_topologies(db: Session):
    if db.query(Topology).first() is not None:
        return

    # Seed Medallion Architecture
    medallion = Topology(name="Medallion Architecture Mesh")
    db.add(medallion)
    db.commit()

    bronze = Node(topology_id=medallion.id, name="Bronze Ingestion", node_type="KAFKA_TOPIC", config_json=json.dumps({"throughput_cap": 5000}))
    silver = Node(topology_id=medallion.id, name="Silver Cleaning", node_type="SPARK_JOB", config_json=json.dumps({"latency_baseline": 150}))
    gold = Node(topology_id=medallion.id, name="Gold Analytical", node_type="VECTOR_STORE", config_json=json.dumps({"latency_baseline": 50}))
    
    db.add_all([bronze, silver, gold])
    db.commit()

    db.add(Edge(topology_id=medallion.id, source_node_id=bronze.id, target_node_id=silver.id))
    db.add(Edge(topology_id=medallion.id, source_node_id=silver.id, target_node_id=gold.id))
    db.commit()

    # Seed Lambda Real-Time Stream
    lambda_arch = Topology(name="Lambda Real-Time Stream")
    db.add(lambda_arch)
    db.commit()
    
    src = Node(topology_id=lambda_arch.id, name="Event Source", node_type="KAFKA_TOPIC")
    flink = Node(topology_id=lambda_arch.id, name="Flink Stream", node_type="SPARK_JOB")
    batch = Node(topology_id=lambda_arch.id, name="Batch Processing", node_type="SPARK_JOB")
    dashboard = Node(topology_id=lambda_arch.id, name="Live Dashboard", node_type="BI_DASHBOARD")
    db.add_all([src, flink, batch, dashboard])
    db.commit()

    db.add(Edge(topology_id=lambda_arch.id, source_node_id=src.id, target_node_id=flink.id))
    db.add(Edge(topology_id=lambda_arch.id, source_node_id=src.id, target_node_id=batch.id))
    db.add(Edge(topology_id=lambda_arch.id, source_node_id=flink.id, target_node_id=dashboard.id))
    db.commit()


@router.get("/")
def get_topologies(db: Session = Depends(get_db)):
    seed_default_topologies(db)
    topologies = db.query(Topology).all()
    return [{"id": t.id, "name": t.name} for t in topologies]

@router.get("/{topology_id}")
def get_topology(topology_id: str, db: Session = Depends(get_db)):
    t = db.query(Topology).filter(Topology.id == topology_id).first()
    if not t:
        raise HTTPException(status_code=404, detail="Topology not found")
    
    return {
        "id": t.id,
        "name": t.name,
        "nodes": [{"id": n.id, "name": n.name, "type": n.node_type} for n in t.nodes],
        "edges": [{"id": e.id, "source": e.source_node_id, "target": e.target_node_id} for e in t.edges]
    }
