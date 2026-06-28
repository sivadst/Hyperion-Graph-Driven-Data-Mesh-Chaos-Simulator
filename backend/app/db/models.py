import uuid
from datetime import datetime, timezone
from sqlalchemy import Column, String, Integer, Float, DateTime, ForeignKey, Text
from sqlalchemy.orm import relationship
from .connection import Base

def generate_uuid():
    return str(uuid.uuid4())

class Topology(Base):
    __tablename__ = "topologies"

    id = Column(String, primary_key=True, default=generate_uuid)
    name = Column(String, nullable=False)
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))

    nodes = relationship("Node", back_populates="topology", cascade="all, delete-orphan")
    edges = relationship("Edge", back_populates="topology", cascade="all, delete-orphan")
    simulation_runs = relationship("SimulationRun", back_populates="topology", cascade="all, delete-orphan")

class Node(Base):
    __tablename__ = "nodes"

    id = Column(String, primary_key=True, default=generate_uuid)
    topology_id = Column(String, ForeignKey("topologies.id"), nullable=False)
    name = Column(String, nullable=False)
    node_type = Column(String, nullable=False)
    config_json = Column(Text, nullable=True)

    topology = relationship("Topology", back_populates="nodes")
    telemetry_logs = relationship("TelemetryLog", back_populates="node", cascade="all, delete-orphan")

class Edge(Base):
    __tablename__ = "edges"

    id = Column(String, primary_key=True, default=generate_uuid)
    topology_id = Column(String, ForeignKey("topologies.id"), nullable=False)
    source_node_id = Column(String, ForeignKey("nodes.id"), nullable=False)
    target_node_id = Column(String, ForeignKey("nodes.id"), nullable=False)

    topology = relationship("Topology", back_populates="edges")

class SimulationRun(Base):
    __tablename__ = "simulation_runs"

    id = Column(String, primary_key=True, default=generate_uuid)
    topology_id = Column(String, ForeignKey("topologies.id"), nullable=False)
    status = Column(String, default="IDLE")
    started_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))

    topology = relationship("Topology", back_populates="simulation_runs")
    telemetry_logs = relationship("TelemetryLog", back_populates="run", cascade="all, delete-orphan")

class TelemetryLog(Base):
    __tablename__ = "telemetry_logs"

    id = Column(Integer, primary_key=True, autoincrement=True)
    run_id = Column(String, ForeignKey("simulation_runs.id"), nullable=False)
    node_id = Column(String, ForeignKey("nodes.id"), nullable=False)
    timestamp = Column(DateTime, default=lambda: datetime.now(timezone.utc))
    throughput = Column(Float, default=0.0)
    latency = Column(Float, default=0.0)
    data_quality_score = Column(Float, default=1.0)

    run = relationship("SimulationRun", back_populates="telemetry_logs")
    node = relationship("Node", back_populates="telemetry_logs")
