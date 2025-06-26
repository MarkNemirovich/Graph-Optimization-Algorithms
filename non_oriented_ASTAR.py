import math
from collections import defaultdict
import networkx as nx


# ---------- «голый» A* на циклах ------------------------------------
def astar_shortest_path_loops(G, source, target, heuristic, effective_distance_func):
    open_set = {source}                       # вершины, которые нужно обработать
    came_from = {}                            # j ← i (предок j – это i)
    g_score = {i: math.inf for i in G.nodes}  # стоимость пути source → i
    f_score = {i: math.inf for i in G.nodes}  # g + heuristic

    g_score[source] = 0.0
    f_score[source] = heuristic(source, target)

    while open_set:
        # 1. выбираем i с минимальным f_score
        current = None
        current_f = math.inf
        for i in open_set:                     # <- i
            if f_score[i] < current_f:
                current_f = f_score[i]
                current = i

        if current == target:                  # найден кратчайший путь
            path = [current]
            while path[-1] in came_from:
                path.append(came_from[path[-1]])
            path.reverse()
            return path

        open_set.remove(current)

        # 2. релаксация рёбер current → j
        neighbours = G.successors(current) if G.is_directed() else G.neighbors(current)
        for j in neighbours:                   # <- j
            tentative_g = g_score[current] + effective_distance_func(G.edges[current, j]['flow'])
            if tentative_g < g_score[j]:
                came_from[j] = current
                g_score[j] = tentative_g
                f_score[j] = tentative_g + heuristic(j, target)
                open_set.add(j)

    raise nx.NetworkXNoPath(f"No path between {source} and {target}")


def astar_algorithm(G, demand_data, effective_distance_func, EPSILON, get_subgraphs=False):
    # 1. обнуляем потоки на рёбрах
    for i, j in G.edges():                     # <- i, j
        G.edges[i, j]['flow'] = 0.0

    # 2. расставляем координаты, если их нет (для эвристики)
    if not all('pos' in G.nodes[i] for i in G.nodes):           # <- i
        suppliers = [i for i in G.nodes if G.nodes[i]['type'] == 'supplier']
        retailers = [i for i in G.nodes if G.nodes[i]['type'] == 'retail']
        dcs       = [i for i in G.nodes if G.nodes[i]['type'] == 'dc']

        pos = {}
        for i, node in enumerate(suppliers):
            pos[node] = (0, i)
        for i, node in enumerate(retailers):
            pos[node] = (2, i / 2)
        for i, node in enumerate(dcs):
            pos[node] = (1, i / 3)

        nx.set_node_attributes(G, pos, 'pos')

    # 3. эвристика – евклидово расстояние между координатами
    def heuristic(i, j):
        return math.dist(G.nodes[i]['pos'], G.nodes[j]['pos'])

    fulfilled = defaultdict(lambda: defaultdict(float))

    # 4. один проход: обслуживаем все пары спроса
    for supplier, retail_map in demand_data.items():             # <- supplier ≡ i
        for retail_node, volume in retail_map.items():           # <- retail_node ≡ j
            if volume <= 0:
                continue

            # 4.1. ищем кратчайший путь A*
            try:
                path = astar_shortest_path_loops(G, supplier, retail_node,
                                                 heuristic, effective_distance_func)
            except nx.NetworkXNoPath:
                print(f"Путь не найден: {supplier} -> {retail_node}")
                continue

            # 4.2. добавляем поток вдоль найденного пути
            for k in range(len(path) - 1):
                i, j = path[k], path[k + 1]                     # <- i, j
                if G.has_edge(i, j):
                    G.edges[i, j]['flow'] += float(volume)
                else:                                           # обратное направление
                    G.edges[j, i]['flow'] += float(volume)

            fulfilled[supplier][retail_node] += volume

    return G
