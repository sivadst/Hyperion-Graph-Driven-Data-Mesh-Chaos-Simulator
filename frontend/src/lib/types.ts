export interface TopologyNode {
    id: string;
    name: string;
    type: string;
}

export interface TopologyEdge {
    id: string;
    source: string;
    target: string;
}

export interface Topology {
    id: string;
    name: string;
    nodes: TopologyNode[];
    edges: TopologyEdge[];
}

export interface NodeState {
    id: string;
    status: 'Nominal' | 'Degraded' | 'Critical' | 'Isolated';
    throughput: number;
    latency: number;
    data_quality_score: number;
    anomaly_score: number;
}

export interface EdgeState {
    source: string;
    target: string;
    status: 'Active' | 'Severed';
    weight: number;
}

export interface SimulationState {
    tick: number;
    status: string;
    nodes: NodeState[];
    edges: EdgeState[];
    centrality: {
        betweenness: Record<string, number>;
        pagerank: Record<string, number>;
    };
}
