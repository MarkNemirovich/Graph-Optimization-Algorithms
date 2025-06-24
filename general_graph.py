import networkx as nx
import matplotlib.pyplot as plt

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
EPSILON = 1e-3

# Функция для равномерного распределения по оси X
def spread(nodes, y, shift=1, margin=0.05):
    n = len(nodes)
    if n == 1:
        return {nodes[0]: (0.5, y)}  # Центрируем один узел
    return {
        node: (
            margin + i * (1 - 2 * margin) / (n - 1),  # равномерно отступаем от краёв
            y + 0.5 * ((i % shift) - 1)  # вертикальное "дрожание" при shift > 1
        )
        for i, node in enumerate(nodes)
    }

def check(G):
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
    for supplier, consumer_dict in demand_data.items():
        expected_total = sum(consumer_dict.values())
        actual_total = round(supplier_total_flow.get(supplier, 0))
        if actual_total != expected_total:
            print(f"Mismatch for supplier {supplier}: expected {expected_total}, got {actual_total}")
            return False

    # Проверка по потребителям
    # Сначала суммируем ожидаемые значения для каждого получателя
    expected_consumer_totals = {}
    for consumer_dict in demand_data.values():
        for consumer, flow in consumer_dict.items():
            expected_consumer_totals[consumer] = expected_consumer_totals.get(consumer, 0) + flow

    for consumer, expected_flow in expected_consumer_totals.items():
        actual_flow = round(consumer_total_flow.get(consumer, 0))
        if actual_flow != expected_flow:
            print(f"Mismatch for consumer {consumer}: expected {expected_flow}, got {actual_flow}")
            return False

    print("Flow check passed.")
    return True