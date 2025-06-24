# main.py
import time
from oriented_graph import create_graph, draw_graph
from oriented_PPA import physarum_algorithm
from oriented_ACO import aco_algorithm
# from oriented_DJA import dijkstra_algorithm
# from oriented_ASTAR import astar_algorithm
def time_counter(G, algo, algo_name, demand_data, effective_distance_func, EPSILON):
    start_time = time.time()
    new_g = algo(G, demand_data, effective_distance_func, EPSILON)
    end_time = time.time()
    print(f"For {algo_name} execution time: {end_time - start_time:.4f}s")
    return new_g

def main():
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

    G = create_graph(suppliers_nodes_list, dc_nodes_list, retail_nodes_list, edgelist)    
    
    aco_G = time_counter(G.copy(), aco_algorithm, 'ant colony algorithm', demand_data, effective_distance_func, EPSILON)
    ppa_G = time_counter(G.copy(), physarum_algorithm, 'physarum algorithm', demand_data, effective_distance_func, EPSILON)
    # dja_G = time_counter(G.copy(), dijkstra_algorithm, 'dijkstra algorithm', demand_data, effective_distance_func, EPSILON)
    # astar_G = time_counter(G.copy(), astar_algorithm, 'astar algorithm', demand_data, effective_distance_func, EPSILON)    


    draw_graph(aco_G, edge_label_attr='flow', title='ant colony algorithm')            # для отображения потока
    draw_graph(ppa_G, edge_label_attr='flow', title='physarum algorithm')            # для отображения потока
    # draw_graph(dja_G, edge_label_attr='flow', title='dijkstra algorithm')            # для отображения потока
    # draw_graph(astar_G, edge_label_attr='flow', title='astar algorithm')            # для отображения потока


if __name__ == '__main__':
    main()