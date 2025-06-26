import networkx as nx
import numpy as np
from random import choices, random
from non_oriented_graph import create_subgraphs

# -------- constants ----------
ALPHA = 1
BETA  = 2
RHO   = 0.10
Q     = 100
MIN_PHER = 1e-4
NUM_ANTS = 15        # меньше муравьёв
ITER_MAX = 60        # и итераций
STALL_ITERS = 10     # ранний выход, если нет улучшений

# порядок «вперёд по цепочке поставок»
LEVEL = {'supplier': 0, 'dc': 1, 'retail': 2}

def init_feromones(graphs):
    for g in graphs:
        supplier = g.graph['s_id']
        demand_nodes = g.nodes[supplier]['demand'].keys()

        for u, v in g.edges:
            # Усиливаем феромон на ребре, если оно ведёт напрямую от поставщика к потребителю
            if (u == supplier and v in demand_nodes) or (v == supplier and u in demand_nodes):
                g.edges[u, v]['pheromone'] = 5.0  # усиленный феромон
            else:
                g.edges[u, v]['pheromone'] = 1.0 + np.random.rand() * 0.1  # базовый феромон немного случайный

# Подсчитывает общий поток по всему графу, суммируя потоки, вычисленные на уровне подграфов.
# Это позволяет обновить потоки на уровне всего графа с учётом всех локальных решений.
def calculate_total_flow(G, graphs):
    for edge in G.edges:
        G.edges[edge]['flow'] = 0
    for g in graphs:
        for i, j, flow in g.edges.data('flow'):
            if flow > 0:
                G.edges[i, j]['flow'] += flow
    return G
                
def aco_algorithm(G, demand_data, effective_distance_function, epsilon):
    graphs = create_subgraphs(G, demand_data)
    init_feromones(graphs)    
    
    # Словарь для хранения лучших решений по каждому графу
    best_solutions = {g.graph['s_id']: {'cost': float('inf'), 'solution': {}, 'graph': g} for g in graphs}
    prev_cost = 0
    for it in range(iterations):
        total_g_cost = 0
        for graph in graphs:
            supplier = graph.graph['s_id']
            demand = graph.nodes[supplier]['demand']
            all_paths = []
            all_costs = []

            for _ in range(num_ants):
                ant_paths = {}
                total_cost = 0

                for target, required_flow in demand.items():
                    if required_flow == 0:
                        continue
                    path = construct_path(graph, supplier, target)
                    if not path:
                        continue
                    ant_paths[target] = path

                    flow_sum = 0
                    for i in range(len(path) - 1):
                        u, v = path[i], path[i + 1]
                        flow_sum += effective_distance_function(graph.edges[u, v]['flow'])
                    total_cost += flow_sum * required_flow

                all_paths.append(ant_paths)
                all_costs.append(total_cost)

                # Проверяем, что все потребители обслужены
                required_targets = {target for target, req in demand.items() if req > 0}
                if required_targets.issubset(ant_paths.keys()):
                    if total_cost < best_solutions[supplier]['cost']:
                        best_solutions[supplier]['cost'] = total_cost
                        best_solutions[supplier]['solution'] = ant_paths
            
            total_g_cost += sum(all_costs)   # суммируем ВСЕ стоимости
            # Обновление феромонов после всех муравьёв
            evaporate_pheromones(graph)
            reinforce_pheromones(graph, all_paths, all_costs)
            
        # print(f"Iteration {it+1}/{iterations}. Total cost: {total_g_cost}")
        if abs(prev_cost - total_g_cost) <= epsilon:
            break
        prev_cost = total_g_cost

    # Применение лучших решений
    for graph in graphs:
        supplier = graph.graph['s_id']
        best_solution = best_solutions[supplier]['solution']
        demand = graph.nodes[supplier]['demand']

        required_targets = {target for target, req in demand.items() if req > 0}
        if not best_solution or not required_targets.issubset(best_solution.keys()):
            print(f"WARNING: No complete solution found for supplier {supplier}")
            continue

        for target, path in best_solution.items():
            demand_val = demand[target]
            for i in range(len(path) - 1):
                u, v = path[i], path[i + 1]
                graph.edges[u, v]['flow'] += demand_val

    return calculate_total_flow(G, graphs)


def construct_path(graph, start, end, retries=3):
    max_len = len(graph)
    for _ in range(retries):
        path, visited = [start], {start}
        current = start
        while current != end and len(path) < max_len:
            neighbors = [n for n in graph.neighbors(current) if n not in visited]
            if not neighbors:
                break
            weights = [
                (graph.edges[current, n]['pheromone'] ** alpha) *
                ((1 / graph.edges[current, n]['length']) ** beta)
                for n in neighbors
            ]
            try:
                next_node = choices(neighbors, weights)[0]
            except ValueError:
                next_node = random.choice(neighbors)

            current = next_node            # ← ОБЯЗАТЕЛЬНО
            path.append(current)
            visited.add(current)

        if current == end:
            return path
    return None

def evaporate_pheromones(graph):
    for u, v in graph.edges:
        graph.edges[u, v]['pheromone'] = max(MIN_PHER, graph.edges[u, v]['pheromone'] * (1 - rho))


def reinforce_pheromones(graph, paths_list, costs_list):
    for paths, cost in zip(paths_list, costs_list):
        if cost == 0:
            continue
        for path in paths.values():
            for i in range(len(path) - 1):
                u, v = path[i], path[i + 1]
                delta = Q_const / max(cost, 1e-3)   # клиппинг
                graph.edges[u, v]['pheromone'] += delta