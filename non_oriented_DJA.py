import networkx as nx
import math

def dijkstra_shortest_path_loops(G, source, target, weight_attr='weight'):
    dist = {i: math.inf for i in G.nodes}
    prev = {}
    visited = set()
    dist[source] = 0

    while True:
        i_min = None
        d_min = math.inf
        for i in G.nodes:
            if i not in visited and dist[i] < d_min:
                d_min = dist[i]
                i_min = i

        if i_min is None:
            break
        if i_min == target:
            break

        visited.add(i_min)

        for j in G.successors(i_min):
            if j in visited:
                continue
            weight = G.edges[i_min, j][weight_attr]
            alt = dist[i_min] + weight
            if alt < dist[j]:
                dist[j] = alt
                prev[j] = i_min

    if target not in prev and target != source:
        raise nx.NetworkXNoPath(f"No path between {source} and {target}")

    path = [target]
    while path[-1] != source:
        path.append(prev[path[-1]])
    path.reverse()
    return path


def dijkstra_algorithm(G, demand_data, effective_distance_func, EPSILON, get_subgraphs=False):
    for i, j in G.edges():
        G.edges[i, j]['flow'] = 0

    temp_G = nx.DiGraph()
    for i, j in G.edges():
        type_i = G.nodes[i]['type']
        type_j = G.nodes[j]['type']

        def add_dir(u, v):
            w = effective_distance_func(G.edges[u, v]['flow'])
            temp_G.add_edge(u, v, weight=w)

        if type_i == 'supplier' and type_j in ['dc', 'retail']:
            add_dir(i, j)
        elif type_j == 'supplier' and type_i in ['dc', 'retail']:
            add_dir(j, i)
        elif type_i == 'dc' and type_j == 'retail':
            add_dir(i, j)
        elif type_j == 'dc' and type_i == 'retail':
            add_dir(j, i)

    for supplier, retail_map in demand_data.items():
        remaining = sum(retail_map.values())

        for retail_node, volume in retail_map.items():
            if volume <= 0 or remaining <= 0:
                continue

            for i, j in temp_G.edges():
                if G.has_edge(i, j):
                    flow_edge = G.edges[i, j]
                else:
                    flow_edge = G.edges[j, i]
                temp_G.edges[i, j]['weight'] = effective_distance_func(flow_edge['flow'])

            try:
                path = dijkstra_shortest_path_loops(temp_G, supplier, retail_node, weight_attr='weight')
            except nx.NetworkXNoPath:
                print(f"Нет пути от поставщика {supplier} к точке {retail_node}")
                continue

            send_vol = min(volume, remaining)

            for i in range(len(path) - 1):
                u, v = path[i], path[i + 1]
                if G.has_edge(u, v):
                    G.edges[u, v]['flow'] += send_vol
                else:
                    G.edges[v, u]['flow'] += send_vol

            remaining -= send_vol

    return G
