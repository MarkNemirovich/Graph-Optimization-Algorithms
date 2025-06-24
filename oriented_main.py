# main.py
import time
from oriented_graph import create_graph, draw_graph
from oriented_PPA import physarum_algorithm
from oriented_ACO import aco_algorithm
# from oriented_DJA import dijkstra_algorithm
# from oriented_ASTAR import astar_algorithm
import general_graph as gen

def time_counter(G, algo, algo_name):
    start_time = time.time()
    new_g = algo(G, gen.demand_data, gen.effective_distance_func, gen.EPSILON)
    end_time = time.time()
    result = gen.check(new_g)
    print(f"For {algo_name} execution time: {end_time - start_time:.4f}s provides result: {result} ")
    return new_g, result

def main():
    G = create_graph()
    
    aco_G, aco_G_correct, aco_G_time = time_counter(G.copy(), aco_algorithm, 'ant colony algorithm')
    ppa_G, ppa_G_correct, ppa_G_time = time_counter(G.copy(), physarum_algorithm, 'physarum algorithm')
    # dja_G, dja_G_correct, dja_G_time = time_counter(G.copy(), dijkstra_algorithm, 'dijkstra algorithm')
    # astar_G, astar_G_correct, astar_G_time = time_counter(G.copy(), astar_algorithm, 'astar algorithm')

    draw_graph(aco_G, edge_label_attr='flow', title='ant colony algorithm', solution = aco_G_correct, time = aco_G_time)
    draw_graph(ppa_G, edge_label_attr='flow', title='physarum algorithm', solution = ppa_G_correct, time = ppa_G_time)
    # draw_graph(dja_G, edge_label_attr='flow', title='dijkstra algorithm', solution = dja_G_correct, time = dja_G_time)
    # draw_graph(astar_G, edge_label_attr='flow', title='astar algorithm', solution = astar_G_correct, time = astar_G_time)


if __name__ == '__main__':
    main()