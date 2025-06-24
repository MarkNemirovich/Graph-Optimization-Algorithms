from collections import defaultdict
import networkx as nx

def dijkstra_algorithm(G, demand_data, effective_distance_func, EPSILON, get_subgraphs=False):
    # Инициализация потоков
    for u, v in G.edges():
        G.edges[u, v]['flow'] = 0
    
    # Создаем направленный граф для поиска пути
    temp_G = nx.DiGraph()
    
    # Добавляем только разрешенные направления движения:
    for u, v in G.edges():
        u_type = G.nodes[u]['type']
        v_type = G.nodes[v]['type']
        
        # Разрешенные направления:
        if u_type == 'supplier' and v_type in ['dc', 'retail']:
            temp_G.add_edge(u, v, weight=effective_distance_func(G.edges[u, v]['flow']))
        elif v_type == 'supplier' and u_type in ['dc', 'retail']:
            temp_G.add_edge(v, u, weight=effective_distance_func(G.edges[u, v]['flow']))
        elif u_type == 'dc' and v_type == 'retail':
            temp_G.add_edge(u, v, weight=effective_distance_func(G.edges[u, v]['flow']))
        elif v_type == 'dc' and u_type == 'retail':
            temp_G.add_edge(v, u, weight=effective_distance_func(G.edges[u, v]['flow']))
    
    # Обрабатываем спрос для каждого поставщика
    for supplier in demand_data:
        # Считаем общий объем поставок от этого поставщика
        total_demand = sum(demand_data[supplier].values())
        remaining_volume = total_demand
        
        for retail_node in demand_data[supplier]:
            volume = demand_data[supplier][retail_node]
            if volume <= 0 or remaining_volume <= 0:
                continue
            
            # Обновляем веса в временном графе
            for u, v in temp_G.edges():
                if G.has_edge(u, v):
                    temp_G.edges[u, v]['weight'] = effective_distance_func(G.edges[u, v]['flow'])
                else:
                    temp_G.edges[u, v]['weight'] = effective_distance_func(G.edges[v, u]['flow'])
            
            # Находим кратчайший путь
            try:
                path = nx.shortest_path(temp_G, source=supplier, target=retail_node, weight='weight')
                
                # Определяем фактический объем с учетом оставшегося
                actual_volume = min(volume, remaining_volume)
                
                # Обновляем потоки в основном графе
                for i in range(len(path) - 1):
                    u, v = path[i], path[i+1]
                    if G.has_edge(u, v):
                        G.edges[u, v]['flow'] += actual_volume
                    else:
                        G.edges[v, u]['flow'] += actual_volume
                
                remaining_volume -= actual_volume
                        
            except nx.NetworkXNoPath:
                print(f"Нет пути от поставщика {supplier} к точке {retail_node}")
                continue
    
    return G