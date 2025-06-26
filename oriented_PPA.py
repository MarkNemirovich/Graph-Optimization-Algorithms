from sympy import symbols, diff, lambdify
from oriented_graph import create_subgraphs
from itertools import chain

def calculate_node_pressures(g):
    """
    Решаем уравнение Σ w_ij (p_i - p_j) = b_i
    по всем соседям j независимо от ориентации ребра.
    """
    nodes = g._nodes
    for node in g._node_list:
        b_i = g._rhs[node]          # правая часть
        num = 0.0
        den = 0.0

        # объединяем предшественников и последователей
        for nbr in set(chain(g.predecessors(node), g.successors(node))):
            # корректно берём атрибуты для (nbr,node) или (node,nbr)
            data = g[nbr][node] if g.has_edge(nbr, node) else g[node][nbr]
            w = data['conductivity'] / data['length']
            num += w * nodes[nbr]['pressure']
            den += w

        # если у узла нет рёбер, оставляем давление 0
        nodes[node]['pressure'] = 0.0 if den == 0 else (num - b_i) / den

def update_flow_and_conductivity(g):
    nodes = g._nodes
    edata = g._edata
    for i, j in g._edge_list:
        data = edata[i, j]
        pressure_diff = nodes[i]['pressure'] - nodes[j]['pressure']
        flow = data['conductivity'] / data['length'] * pressure_diff
        edata[i, j]['flow'] = flow
        prev = data['conductivity']
        edata[i, j]['prev_conductivity'] = prev
        edata[i, j]['conductivity'] = (prev + abs(flow)) / 2

def calculate_total_flow(G, graphs):
    for edge in G.edges:
        G.edges[edge]['flow'] = 0
    for g in graphs:
        for i, j, flow in g.edges.data('flow'):
            # if flow > 0:
            G.edges[i, j]['flow'] += flow

def update_edge_length(G, g, E_func, dE_func):
    edata = g._edata
    for i, j in g._edge_list:
        data = edata[i, j]
        flow = G.edges[i, j]['flow']
        edata[i, j]['length'] = (data['length'] + E_func(flow) + data['flow'] * dE_func(flow)) / 2

def term_criteria(graphs, tol):
    diff, total = 0.0, 0.0
    for g in graphs:
        for i, j, d in g.edges(data=True):
            diff += abs(d['conductivity'] - d['prev_conductivity'])
            total += d['prev_conductivity']
    return diff / (total + 1e-12) < tol

def _unpack_graph(g):
    g._node_list = list(g.nodes())
    g._edge_list = list(g.edges())
    g._nodes     = g.nodes
    g._edata     = g.edges
    rhs = {}
    s_id = g.graph['s_id']
    for node in g._node_list:
        ntype = g._nodes[node]['type']
        if ntype == 'supplier':
            rhs[node] = -sum(g._nodes[node]['demand'].values())
        elif ntype == 'retail':
            rhs[node] = g._nodes[s_id]['demand'].get(node, 0.0)
        else:
            rhs[node] = 0
    g._rhs = rhs

def _refresh_cache(g):
    g._edge_list = list(g.edges())
    g._edata     = g.edges

def physarum_algorithm(G, demand_data, effective_distance_function, epsilon):
    graphs = create_subgraphs(G, demand_data)
    for g in graphs:
        _unpack_graph(g)

    Q = symbols('Q')
    E_sym  = effective_distance_function(Q)
    dE_sym = diff(E_sym, Q)
    E_func  = lambdify(Q, E_sym,  'numpy')
    dE_func = lambdify(Q, dE_sym, 'numpy')

    max_iterations = 100
    check_every = 10

    for iter_num in range(max_iterations):
        for g in graphs:
            calculate_node_pressures(g)
            update_flow_and_conductivity(g)

        calculate_total_flow(G, graphs)

        for g in graphs:
            update_edge_length(G, g, E_func, dE_func)

        if term_criteria(graphs, epsilon):
            print(f"PPA converged in {iter_num} iterations")
            break

        if (iter_num + 1) % check_every == 0:
            edges_to_remove = [(i, j) for i, j in list(G.edges)
                               if G.edges[i, j]['flow'] < 1]

            if edges_to_remove:
                G.remove_edges_from(edges_to_remove)
                for g in graphs:
                    g.remove_edges_from([e for e in edges_to_remove if g.has_edge(*e)])
                    _refresh_cache(g)
                print(f"Iteration {iter_num}: removed {len(edges_to_remove)} edges")
        

    return G
