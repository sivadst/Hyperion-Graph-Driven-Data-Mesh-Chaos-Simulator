import asyncio
import networkx as nx
import numpy as np
import time
from datetime import datetime, timezone
import json
from .ml_defense import AIDecisionCore

class SimulationEngine:
    def __init__(self, db_session_maker):
        self.db_session_maker = db_session_maker
        self.active_runs = {}  # run_id -> dict with state
        self.locks = {} # run_id -> asyncio.Lock()
        self.ai_cores = {} # run_id -> AIDecisionCore
        
        # In-memory buffer for tumbling window telemetry
        self.telemetry_buffer = {} # run_id -> { node_id -> [records] }
        
    async def get_lock(self, run_id):
        if run_id not in self.locks:
            self.locks[run_id] = asyncio.Lock()
        return self.locks[run_id]

    async def start_run(self, run_id: str, topology_id: str, nodes: list, edges: list):
        async with await self.get_lock(run_id):
            if run_id in self.active_runs:
                return
            
            G = nx.DiGraph()
            for node in nodes:
                config = json.loads(node.config_json) if node.config_json else {}
                G.add_node(node.id, 
                           name=node.name, 
                           type=node.node_type,
                           status="Nominal",
                           config=config,
                           anomaly_score=0.0,
                           throughput=0.0,
                           latency=0.0,
                           data_quality_score=1.0,
                           faults=[])
            for edge in edges:
                G.add_edge(edge.source_node_id, edge.target_node_id, status="Active", routing_weight=1.0)
            
            self.active_runs[run_id] = {
                "topology_id": topology_id,
                "graph": G,
                "tick": 0,
                "status": "RUNNING",
                "last_flush_time": time.time(),
                "warmup_ticks": 50,
                "use_ai": True
            }
            self.telemetry_buffer[run_id] = {n.id: [] for n in nodes}
            
            ai_core = AIDecisionCore(G)
            self.ai_cores[run_id] = ai_core

        # start the tick loop in background
        asyncio.create_task(self._tick_loop(run_id))

    async def inject_fault(self, run_id: str, node_id: str, fault_type: str, severity: float):
        async with await self.get_lock(run_id):
            if run_id in self.active_runs:
                G = self.active_runs[run_id]["graph"]
                if node_id in G.nodes:
                    G.nodes[node_id]["faults"].append({
                        "type": fault_type,
                        "severity": severity
                    })

    async def stop_run(self, run_id: str):
        async with await self.get_lock(run_id):
            if run_id in self.active_runs:
                self.active_runs[run_id]["status"] = "COMPLETED"

    async def _tick_loop(self, run_id: str):
        while True:
            async with await self.get_lock(run_id):
                if run_id not in self.active_runs or self.active_runs[run_id]["status"] != "RUNNING":
                    break
                
                run_state = self.active_runs[run_id]
                G = run_state["graph"]
                tick = run_state["tick"]
                
                # 1. Generate baseline signals
                base_throughput = 1000 + 500 * np.sin(tick * 0.1)
                noise = np.random.normal(0, 50, len(G.nodes))
                
                # Topological sort for propagation
                try:
                    sorted_nodes = list(nx.topological_sort(G))
                except nx.NetworkXUnfeasible:
                    sorted_nodes = list(G.nodes)

                for i, node_id in enumerate(sorted_nodes):
                    node = G.nodes[node_id]
                    
                    # Base metrics
                    node["throughput"] = max(0, base_throughput + noise[i])
                    node["latency"] = max(10, 50 + np.random.normal(0, 5))
                    node["data_quality_score"] = 1.0
                    
                    # Apply downstream propagation (simplified matrix approach)
                    incoming_edges = list(G.predecessors(node_id))
                    if incoming_edges:
                        # Combine degraded states from upstream
                        upstream_quality = np.mean([G.nodes[u]["data_quality_score"] for u in incoming_edges if G[u][node_id]["routing_weight"] > 0])
                        if not np.isnan(upstream_quality):
                            node["data_quality_score"] = min(node["data_quality_score"], upstream_quality)
                    
                    # Apply active faults
                    for fault in node["faults"]:
                        if fault["type"] == "null_injection":
                            node["data_quality_score"] *= (1.0 - fault["severity"])
                        elif fault["type"] == "latency_spike":
                            node["latency"] += fault["severity"]
                    
                    # Store in buffer
                    self.telemetry_buffer[run_id][node_id].append({
                        "throughput": node["throughput"],
                        "latency": node["latency"],
                        "data_quality_score": node["data_quality_score"]
                    })
                
                # 2. AI Defense Layer
                ai_core = self.ai_cores[run_id]
                if tick < run_state["warmup_ticks"]:
                    # Warmup: collect data
                    ai_core.collect_warmup_data(G)
                elif tick == run_state["warmup_ticks"]:
                    # Train
                    ai_core.train()
                else:
                    # Infer and remediate
                    if run_state["use_ai"]:
                        remediated = ai_core.evaluate_and_remediate(G)
                        if remediated:
                            ai_core.recalculate_centrality(G)

                run_state["tick"] += 1
                
                # 3. Aggregation Window Flush (5 seconds)
                now = time.time()
                if now - run_state["last_flush_time"] >= 5.0:
                    self._flush_telemetry(run_id)
                    run_state["last_flush_time"] = now

            await asyncio.sleep(0.2) # 200ms tick

        # Cleanup
        self._flush_telemetry(run_id) # final flush
        if run_id in self.active_runs:
            del self.active_runs[run_id]

    def _flush_telemetry(self, run_id):
        # Flush aggregated metrics to DB
        if run_id not in self.telemetry_buffer:
            return
            
        buffer = self.telemetry_buffer[run_id]
        if not buffer:
            return

        with self.db_session_maker() as session:
            from app.db.models import TelemetryLog
            now_dt = datetime.now(timezone.utc)
            for node_id, records in buffer.items():
                if not records:
                    continue
                
                avg_throughput = np.mean([r["throughput"] for r in records])
                avg_latency = np.mean([r["latency"] for r in records])
                avg_quality = np.mean([r["data_quality_score"] for r in records])
                
                log = TelemetryLog(
                    run_id=run_id,
                    node_id=node_id,
                    timestamp=now_dt,
                    throughput=avg_throughput,
                    latency=avg_latency,
                    data_quality_score=avg_quality
                )
                session.add(log)
            session.commit()
            
        # Clear buffer
        for node_id in buffer.keys():
            buffer[node_id] = []
