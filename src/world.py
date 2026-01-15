import networkx as nx

def build_toy_world() -> nx.DiGraph:
    G = nx.DiGraph()

    # demand = what the node needs each day
    # inventory = buffer stock held by the node
    # local_production = used to satisfy own demand first
    # export_supply = supply available specifically to ship out to others
    G.add_node("USA", demand=100, inventory=40, local_production=40, export_supply=10)
    G.add_node("EU",  demand=90,  inventory=35, local_production=35, export_supply=5)
    G.add_node("CHN", demand=110, inventory=45, local_production=60, export_supply=120)  # big exporter
    G.add_node("IND", demand=80,  inventory=30, local_production=25, export_supply=0)
    G.add_node("SGP", demand=40,  inventory=15, local_production=5,  export_supply=0)   # hub

    # Force exports through SGP so chokepoint shocks matter
    G.add_edge("CHN", "SGP", capacity=120)
    G.add_edge("SGP", "USA", capacity=60)
    G.add_edge("SGP", "EU",  capacity=60)
    G.add_edge("SGP", "IND", capacity=50)

    # Some non-CHN trade
    G.add_edge("USA", "EU", capacity=25)
    G.add_edge("EU", "IND", capacity=20)

    return G
