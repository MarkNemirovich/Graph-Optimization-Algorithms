import networkx as nx
import numpy as np
from random import choices
from oriented_graph import create_subgraphs

# ---------------------- параметры -----------------------------
alpha = 1
beta  = 2
rho   = 0.10
Q_const = 100

num_ants = 1        # меньше муравьёв
iterations = 1          # <<< SPEED-UP  (было 100)
TOP_RATIO  = 0.30        # сколько лучших муравьёв усиливаем
STAGNATE   = 1          # стоп, если нет улучшения N эпох
# --------------------------------------------------------------


def init_feromones(graphs):
    """ставим pheromone и сразу кешируем эвристику eta=1/length."""
    for g in graphs:
        supplier = g.graph['s_id']
        demand_nodes = g.nodes[supplier]['demand'].keys()

        for u, v, d in g.edges(data=True):
            if u == supplier and v in demand_nodes:
                d['pheromone'] = 5.0
            else:
                d['pheromone'] = 1.0 + np.random.rand() * 0.1
            d['eta'] = 1.0 / d['length'] if d['length'] > 0 else 1.0
            d.setdefault('flow', 0.0)      # чтобы дальше не проверять


def calculate_total_flow(G, graphs):
    for edge in G.edges:
        G.edges[edge]['flow'] = 0.0
    for g in graphs:
        for u, v, d in g.edges(data=True):
            if d['flow'] > 0:
                G.edges[u, v]['flow'] += d['flow']
    return G


def aco_algorithm(G, demand_data, effective_distance_function, epsilon):
    graphs = create_subgraphs(G, demand_data)
    init_feromones(graphs)

    best_solutions = {g.graph['s_id']: {'cost': float('inf'), 'solution': {}}
                      for g in graphs}

    best_global   = float('inf')   # для критерия стагнации
    stagnation_it = 0

    for it in range(iterations):
        total_epoch_cost = 0.0

        for graph in graphs:
            supplier = graph.graph['s_id']
            demand   = graph.nodes[supplier]['demand']

            # --- динамически подбираем число муравьёв -----------------
            # num_ants = min(len([d for d in demand.values() if d > 0]) + 5, 5)
            # ----------------------------------------------------------

            all_paths, all_costs = [], []

            for _ in range(num_ants):
                ant_paths = {}
                approx_cost = 0.0     # считаем только по длинам

                for target, required_flow in demand.items():
                    if required_flow == 0:
                        continue
                    path = construct_path(graph, supplier, target)
                    if not path:
                        continue
                    ant_paths[target] = path

                    path_len = sum(
                        graph.edges[path[i], path[i + 1]]['length']
                        for i in range(len(path) - 1)
                    )
                    approx_cost += path_len * required_flow

                all_paths.append(ant_paths)
                all_costs.append(approx_cost)

            # -- выбираем top-k лучших по approx_cost -------------------
            k = max(1, int(TOP_RATIO * len(all_costs)))
            top_idx = np.argsort(all_costs)[:k]
            # -----------------------------------------------------------

            # пересчитываем «точную» цену для top-k и усиливаем
            evaporate_pheromones(graph)
            for idx in top_idx:
                ant_paths = all_paths[idx]
                exact_cost = 0.0
                for target, path in ant_paths.items():
                    required_flow = demand[target]
                    flow_sum = 0.0
                    for i in range(len(path) - 1):
                        u, v = path[i], path[i + 1]
                        flow_sum += effective_distance_function(
                            graph.edges[u, v]['flow']
                        )
                    exact_cost += flow_sum * required_flow

                reinforce_pheromones(graph, ant_paths, exact_cost)
                total_epoch_cost += exact_cost

                # запоминаем лучшее решение
                if exact_cost < best_solutions[supplier]['cost']:
                    best_solutions[supplier]['cost'] = exact_cost
                    best_solutions[supplier]['solution'] = ant_paths

        # ---------- критерий раннего выхода ----------------------------
        if total_epoch_cost < best_global - 1e-3:
            best_global   = total_epoch_cost
            stagnation_it = 0
        else:
            stagnation_it += 1
            if stagnation_it >= STAGNATE or best_global < epsilon:
                break
        # ----------------------------------------------------------------

    # --- применяем лучшие найденные пути к потокам ----------------------
    for graph in graphs:
        supplier = graph.graph['s_id']
        demand   = graph.nodes[supplier]['demand']
        best_sol = best_solutions[supplier]['solution']

        for target, path in best_sol.items():
            req = demand[target]
            for i in range(len(path) - 1):
                u, v = path[i], path[i + 1]
                graph.edges[u, v]['flow'] += req

    return calculate_total_flow(G, graphs)


def construct_path(graph, start, end, retries=3):
    """использует кешированную эвристику edge['eta']."""
    for _ in range(retries):
        path = [start]
        visited, current = {start}, start

        while current != end:
            neighbors = [n for n in graph.neighbors(current)
                         if n not in visited and graph.has_edge(current, n)]
            if not neighbors:
                break
            weights = []
            for n in neighbors:
                d = graph.edges[current, n]
                weights.append((d['pheromone'] ** alpha) * (d['eta'] ** beta))

            next_node = choices(neighbors, weights)[0]
            path.append(next_node)
            visited.add(next_node)
            current = next_node

        if current == end:
            return path

    try:
        return nx.shortest_path(graph, start, end, weight='length')
    except nx.NetworkXNoPath:
        return None


def evaporate_pheromones(graph):
    for _, _, d in graph.edges(data=True):
        d['pheromone'] *= (1 - rho)


def reinforce_pheromones(graph, paths_dict, cost):
    if cost == 0:
        return
    for path in paths_dict.values():
        for i in range(len(path) - 1):
            u, v = path[i], path[i + 1]
            graph.edges[u, v]['pheromone'] += Q_const / cost
