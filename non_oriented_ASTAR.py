# non_oriented_astar.py
import math
from collections import defaultdict
import networkx as nx

def astar_algorithm(G, demand_data, effective_distance_func, EPSILON, get_subgraphs=False):
    # Инициализация потоков
    for u, v in G.edges():
        G.edges[u, v]['flow'] = 0.0
    
    # Автоматическая расстановка позиций
    if not all('pos' in G.nodes[n] for n in G.nodes):
        suppliers = [n for n in G.nodes if G.nodes[n]['type'] == 'supplier']
        retailers = [n for n in G.nodes if G.nodes[n]['type'] == 'retail']
        dcs = [n for n in G.nodes if G.nodes[n]['type'] == 'dc']
        
        pos = {}
        for i, node in enumerate(suppliers):
            pos[node] = (0, i)
        for i, node in enumerate(retailers):
            pos[node] = (2, i/2)
        for i, node in enumerate(dcs):
            pos[node] = (1, i/3)
        
        nx.set_node_attributes(G, pos, 'pos')

    # Эвристическая функция
    def heuristic(u, v):
        return math.dist(G.nodes[u]['pos'], G.nodes[v]['pos'])

    # Словарь для отслеживания выполненных поставок
    fulfilled = defaultdict(lambda: defaultdict(float))
    
    # Основной алгоритм (один проход)
    for supplier, demands in demand_data.items():
        for retail_node, volume in demands.items():
            if volume <= 0:
                continue
            
            # Находим оптимальный путь
            try:
                path = nx.astar_path(
                    G,
                    source=supplier,
                    target=retail_node,
                    weight=lambda u, v, d: effective_distance_func(d['flow']),
                    heuristic=heuristic
                )
                
                # Добавляем ровно требуемый объем
                for i in range(len(path)-1):
                    u, v = path[i], path[i+1]
                    G.edges[u, v]['flow'] += float(volume)
                
                # Отмечаем выполненный спрос
                fulfilled[supplier][retail_node] += volume
                
            except nx.NetworkXNoPath:
                print(f"Путь не найден: {supplier} -> {retail_node}")
                continue

    return G