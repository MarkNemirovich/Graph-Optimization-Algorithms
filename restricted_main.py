# main.py
import time
from restricted_graph import create_graph, draw_graph
from restricted_PPA import physarum_algorithm

def main():
    min_capacity = 6
    suppliers_nodes_list = [1, 2, 3]
    dc_nodes_list = [4, 5, 6, 7]
    retail_nodes_list = [8, 9]
    edgelist = [
        (1, 4), (1, 5), (1, 6),
        (2, 5), (2, 6), (2, 7),
        (3, 5), (3, 7),
        (4, 8), (4, 9),
        (5, 8), (5, 9),
        (6, 9), 
        (7, 9),
        (1, 8), (1, 9), (3, 9)
    ]
    demand_data = {
        1: {8:5, 9:12},
        2: {8:16, 9:0},
        3: {8:6, 9:6}
    }
    effective_distance_func = lambda Q: 5 + 3 * (2.718281828**(-0.3 * Q))
    EPSILON = 1e-2

    start_time = time.time()
    G = create_graph(suppliers_nodes_list, dc_nodes_list, retail_nodes_list, edgelist)
    graphs = physarum_algorithm(G, demand_data, effective_distance_func, EPSILON, get_subgraphs=True, min_capacity= min_capacity)
    
    for g in graphs:
        print(f"Subgraph for supplier {g.graph['s_id']}:")
        print("Nodes:", list(g.nodes))
        print("Edges:", list(g.edges))
    
    end_time = time.time()
    print(f"Execution time: {end_time - start_time:.4f}s")

    for g in graphs:
        print(f"Subnetwork = {g.graph['s_id']}")
        print(sorted(g.edges.data('flow'), key=lambda x: x[2], reverse=True))
    print("Global edges flow:")
    print(sorted(G.edges.data('flow'), key=lambda x: x[2], reverse=True))

    # draw_graph_flows(G, threshold=1)
    draw_graph(G, edge_label_attr='flow')            # для отображения потока
    # draw_graph(G, edge_label_attr='conductivity')    # для отображения проводимости
    # draw_graph(G, edge_label_attr='length')          # для отображения длины

if __name__ == '__main__':
    main()