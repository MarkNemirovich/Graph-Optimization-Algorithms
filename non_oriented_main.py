# main.py
import time
from non_oriented_graph import create_graph, draw_graph
from non_oriented_PPA import physarum_algorithm
from non_oriented_ACO import aco_algorithm
from non_oriented_DJA import dijkstra_algorithm
from non_oriented_ASTAR import astar_algorithm
    
def check(G, right_answer):
    node_types = dict(G.nodes(data='type'))

    supplier_total_flow = {}
    consumer_total_flow = {}

    for u, v, data in G.edges(data=True):
        flow = data.get('flow', 0)

        # Считаем исходящие потоки от поставщиков
        if node_types.get(u) == 'supplier':
            supplier_total_flow[u] = supplier_total_flow.get(u, 0) + flow
        elif node_types.get(v) == 'supplier':
            supplier_total_flow[v] = supplier_total_flow.get(v, 0) + flow

        # Считаем входящие потоки в получателей
        if node_types.get(u) == 'retail':
            consumer_total_flow[u] = consumer_total_flow.get(u, 0) + flow
        elif node_types.get(v) == 'retail':
            consumer_total_flow[v] = consumer_total_flow.get(v, 0) + flow

    # Проверка по поставщикам
    for supplier, consumer_dict in right_answer.items():
        expected_total = sum(consumer_dict.values())
        actual_total = round(supplier_total_flow.get(supplier, 0))
        if actual_total != expected_total:
            print(f"Mismatch for supplier {supplier}: expected {expected_total}, got {actual_total}")
            return False

    # Проверка по потребителям
    # Сначала суммируем ожидаемые значения для каждого получателя
    expected_consumer_totals = {}
    for consumer_dict in right_answer.values():
        for consumer, flow in consumer_dict.items():
            expected_consumer_totals[consumer] = expected_consumer_totals.get(consumer, 0) + flow

    for consumer, expected_flow in expected_consumer_totals.items():
        actual_flow = round(consumer_total_flow.get(consumer, 0))
        if actual_flow != expected_flow:
            print(f"Mismatch for consumer {consumer}: expected {expected_flow}, got {actual_flow}")
            return False

    print("Flow check passed.")
    return True


def time_counter(G, algo, algo_name, demand_data, effective_distance_func, EPSILON):
    start_time = time.time()
    new_g = algo(G, demand_data, effective_distance_func, EPSILON)
    end_time = time.time()
    result = check(new_g, demand_data)
    print(f"For {algo_name} execution time: {end_time - start_time:.4f}s provides result: {result} ")
    return new_g, result

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
        (1, 8), (3, 9)
    ]
    demand_data = {
        1: {8:5, 9:12},
        2: {8:16, 9:0},
        3: {8:6, 9:6}
    }
    effective_distance_func = lambda Q: 5 + 3 * (2.718281828**(-0.3 * Q))
    EPSILON = 1e-2

    G = create_graph(suppliers_nodes_list, dc_nodes_list, retail_nodes_list, edgelist)   
     
    aco_G, aco_G_correct = time_counter(G.copy(), aco_algorithm, 'ant colony algorithm', demand_data, effective_distance_func, EPSILON)
    ppa_G, ppa_G_correct = time_counter(G.copy(), physarum_algorithm, 'physarum algorithm', demand_data, effective_distance_func, EPSILON)
    dja_G, dja_G_correct = time_counter(G.copy(), dijkstra_algorithm, 'dijkstra algorithm', demand_data, effective_distance_func, EPSILON)
    astar_G, astar_G_correct = time_counter(G.copy(), astar_algorithm, 'astar algorithm', demand_data, effective_distance_func, EPSILON)


    draw_graph(aco_G, edge_label_attr='flow', title='ant colony algorithm', solution = aco_G_correct)            # для отображения потока
    draw_graph(ppa_G, edge_label_attr='flow', title='physarum algorithm', solution = ppa_G_correct)            # для отображения потока
    draw_graph(dja_G, edge_label_attr='flow', title='dijkstra algorithm', solution = dja_G_correct)            # для отображения потока
    draw_graph(astar_G, edge_label_attr='flow', title='astar algorithm', solution = astar_G_correct)            # для отображения потока


if __name__ == '__main__':
    main()