import networkx as nx
import matplotlib.pyplot as plt
import random

# Узлы
suppliers_nodes_list = list(range(1,11))
dc_nodes_list = list(range(101, 111))
retail_nodes_list = list(range(1001, 1011))

# Рёбра
edgelist = []

# 1) Поставщики -> все DC
for supplier in suppliers_nodes_list:
    for dc in dc_nodes_list:
        edgelist.append((supplier, dc))

# 2) DC -> все DC (полносвязь с обоих направлений, кроме самих себя)
for i, dc1 in enumerate(dc_nodes_list):
    for dc2 in dc_nodes_list:
        if dc1 != dc2:
            edgelist.append((dc1, dc2))

# 3) DC -> все ритейлы
for dc in dc_nodes_list:
    for retail in retail_nodes_list:
        edgelist.append((dc, retail))

# Создаём ориентированный граф
G = nx.DiGraph()
G.add_nodes_from(suppliers_nodes_list + dc_nodes_list + retail_nodes_list)
G.add_edges_from(edgelist)

# --- Спрос (без рандома) ---
# Например, все поставщики требуют у всех ритейлов 10 единиц
demand_data = {}
for supplier in suppliers_nodes_list:
    demand_data[supplier] = {retail: random.randint(1, 100) for retail in retail_nodes_list}

# suppliers_nodes_list = [1, 2, 3, 4, 5, 6, 7]
# dc_nodes_list = [11, 12, 13]
# retail_nodes_list = [21, 22, 23, 24, 25]
# edgelist = [
#     (1, 11), (1, 12), (1, 21), (1, 22), (1, 23), (1, 24),
#     (2, 11), (2, 12), (2, 13), (2, 23), (2, 24), (2, 25),
#     (3, 11), (3, 12),
#     (4, 12), (4, 13),
#     (5, 13), (5, 24),
#     (6, 12), (6, 23), (6, 24), (6, 25),
#     (7, 21), (7, 25),
#     (11, 21), (11, 22), (11, 23),
#     (12, 22), (12, 23), (12, 24), (12, 25),
#     (13, 22), (13, 24)
# ]
# demand_data = {
#     1: {21:5, 22:12, 23:10, 24:15, 25:3},
#     2: {21:0, 22:6, 23:8, 24:5, 25:2},
#     3: {21:10, 22:0, 23:0, 24:20, 25:0},
#     4: {21:0, 22:5, 23:0, 24:0, 25:6},
#     5: {21:0, 22:6, 23:0, 24:4, 25:0},
#     6: {21:0, 22:7, 23:8, 24:3, 25:5},
#     7: {21:5, 22:0, 23:0, 24:0, 25:8}
# }

# # Для иллюстрации
# suppliers_nodes_list = [1, 2, 3]
# dc_nodes_list = [4, 5, 6, 7]
# retail_nodes_list = [8, 9]
# edgelist = [
#     (1, 4), (1, 5), (1, 6),
#     (2, 5), (2, 6), (2, 7),
#     (3, 5), (3, 7),
#     (4, 8), (4, 9),
#     (5, 8), (5, 9),
#     (6, 9), 
#     (7, 9),
#     (1, 8), (3, 9)
# ]
# demand_data = {
#     1: {8:5, 9:12},
#     2: {8:16, 9:0},
#     3: {8:6, 9:6}
# }

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
        if node_types.get(u) == 'supplier':          # u → ...
            supplier_total_flow[u] = supplier_total_flow.get(u, 0) + flow
        if node_types.get(v) == 'retail':            # ... → v
            consumer_total_flow[v] = consumer_total_flow.get(v, 0) + flow

    sum_supplier_error = 0.0
    sum_consumer_error = 0.0
    total_supplier_checks = 0
    total_consumer_checks = 0
    # Проверка по поставщикам
    for supplier, consumer_dict in demand_data.items():
        expected_total = sum(consumer_dict.values())
        actual_total = round(supplier_total_flow.get(supplier, 0))
        total_supplier_checks += 1
        if actual_total != expected_total:
            sum_supplier_error += abs(actual_total - expected_total)/expected_total
            # print(f"Mismatch for supplier {supplier}: expected {expected_total}, got {actual_total}")
            # return False

    # Проверка по потребителям
    # Сначала суммируем ожидаемые значения для каждого получателя
    expected_consumer_totals = {}
    for consumer_dict in demand_data.values():
        for consumer, flow in consumer_dict.items():
            expected_consumer_totals[consumer] = expected_consumer_totals.get(consumer, 0) + flow

    for consumer, expected_flow in expected_consumer_totals.items():
        actual_flow = round(consumer_total_flow.get(consumer, 0))
        total_consumer_checks += 1
        if actual_flow != expected_flow:
            sum_consumer_error += abs(actual_flow - expected_flow)/expected_flow
            # print(f"Mismatch for consumer {consumer}: expected {expected_flow}, got {actual_flow}")
            # return False
    persent_supplier = sum_supplier_error/total_supplier_checks*100
    persent_consumer = sum_consumer_error/total_consumer_checks*100
    print(f"Flow check passed with sum_supplier_error {persent_supplier:.3f} and sum_consumer_error {persent_consumer:.3f}.")
    return (persent_supplier + persent_consumer) == 0