import networkx as nx
import numpy as np
from sklearn.ensemble import IsolationForest

class AIDecisionCore:
    def __init__(self, baseline_graph: nx.DiGraph):
        self.model = IsolationForest(contamination=0.1, random_state=42)
        self.is_trained = False
        self.warmup_data = []
        self.centrality_metrics = {}
        self.recalculate_centrality(baseline_graph)

    def recalculate_centrality(self, G: nx.DiGraph):
        try:
            self.centrality_metrics['betweenness'] = nx.betweenness_centrality(G)
            self.centrality_metrics['pagerank'] = nx.pagerank(G)
        except Exception:
            # Fallback if graph is empty or disconnected
            self.centrality_metrics['betweenness'] = {n: 0 for n in G.nodes}
            self.centrality_metrics['pagerank'] = {n: 0 for n in G.nodes}

    def collect_warmup_data(self, G: nx.DiGraph):
        for node_id, data in G.nodes(data=True):
            self.warmup_data.append([
                data.get("throughput", 0),
                data.get("latency", 0),
                data.get("data_quality_score", 1.0)
            ])

    def train(self):
        if len(self.warmup_data) > 0:
            X = np.array(self.warmup_data)
            self.model.fit(X)
            self.is_trained = True
            print("AI Decision Core trained on baseline telemetry.")

    def evaluate_and_remediate(self, G: nx.DiGraph) -> bool:
        if not self.is_trained:
            return False

        remediated = False
        for node_id, data in G.nodes(data=True):
            features = np.array([[
                data.get("throughput", 0),
                data.get("latency", 0),
                data.get("data_quality_score", 1.0)
            ]])
            
            # Predict anomaly (-1 is anomaly, 1 is normal)
            prediction = self.model.predict(features)[0]
            score = self.model.decision_function(features)[0]
            
            # Convert decision score to a 0-1 anomaly score (approximate)
            # lower decision_function -> more anomalous
            anomaly_score = max(0.0, min(1.0, 0.5 - score))
            data["anomaly_score"] = anomaly_score
            
            if prediction == -1 and data["status"] != "Isolated":
                # Critical anomaly detected
                data["status"] = "Critical"
                
                # Check mitigation thresholds
                if anomaly_score > 0.7:
                    # Apply circuit breaking
                    data["status"] = "Isolated"
                    # Mutate outgoing edges to stop blast radius
                    for successor in list(G.successors(node_id)):
                        G[node_id][successor]["routing_weight"] = 0.0
                        G[node_id][successor]["status"] = "Severed"
                    remediated = True
        
        return remediated
