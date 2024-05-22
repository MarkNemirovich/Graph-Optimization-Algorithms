import networkx as nx
import random
from math import e
from sympy import symbols, diff
import time
import matplotlib.pyplot as plt


def create_graph(suppliers_nodes_list, dc_nodes_list, retail_nodes_list, edgelist):
    G = nx.Graph()
    G.add_nodes_from(suppliers_nodes_list, type='supplier')
    G.add_nodes_from(dc_nodes_list, type='dc')
    G.add_nodes_from(retail_nodes_list, type='retail')
    G.add_edges_from(edgelist, flow=0)
    return G

def create_subgraphs(G: nx.Graph, demand_data):
    graphs = []
    dc_and_retail = []
    suppliers = []
    for node, atr in G.nodes(data='type'):
        if atr in ('dc', 'retail'):
            dc_and_retail.append(node)
        else:
            suppliers.append(node)
    for supplier in suppliers:
        g = nx.subgraph(G, [supplier] + dc_and_retail).copy()
        g.graph["s_id"] = supplier
        g.nodes[supplier]['demand'] = demand_data[supplier]
        for i, j in g.edges:
            g.edges[i, j]['flow'] = 0
            g.edges[i, j]['conductivity'] = random.uniform(1e-6, 1)
            g.edges[i, j]['prev_conductivity'] = 0
            g.edges[i, j]['length'] = 1
        for node in g.nodes:
            g.nodes[node]['pressure'] = 0
        graphs.append(g)
    return graphs


def calculate_node_pressures(g: nx.Graph):
    for node, type in g.nodes(data='type'):
        if type == 'supplier':
            equation_right = -sum(g.nodes[node]['demand'].values())
        elif type == 'retail':
            equation_right = g.nodes[g.graph['s_id']]['demand'][node]
        else:
            equation_right = 0
        numerator = 0
        denominator = 0
        for neighbour, data in g[node].items():
            numerator += data['conductivity'] / data['length'] * g.nodes[neighbour]['pressure']
            denominator += data['conductivity'] / data['length']
        g.nodes[node]['pressure'] = (numerator - equation_right) / denominator



def update_flow_and_conductivity(g: nx.Graph):
    for i, j, data in g.edges.data():
        g.edges[i, j]['flow'] = data['conductivity'] / data['length'] * (g.nodes[i]['pressure'] - g.nodes[j]['pressure'])
    for i, j, data in g.edges.data():
        g.edges[i, j]['prev_conductivity'] = data['conductivity']
        g.edges[i, j]['conductivity'] = (data['conductivity'] + abs(data['flow'])) / 2


def calculate_total_flow(G: nx.Graph, graphs):
    for edge in G.edges:
        G.edges[edge]['flow'] = 0
    for g in graphs:
        for i, j, flow in g.edges.data('flow'):
            G.edges[i, j]['flow'] += flow


def update_edge_length(G: nx.Graph, g: nx.Graph, E):
    Q = symbols('Q')
    dE = diff(E(Q), Q)
    for i, j, data in g.edges.data():
        g.edges[i, j]['length'] = (data['length'] + E(G.edges[i, j]['flow']) + data['flow'] * dE.subs(Q, G.edges[i, j]['flow'])) / 2


def calculate_term_criteria(graphs):
    total_diff = 0
    for g in graphs:
        for i, j, data in g.edges.data():
            total_diff += abs(data['conductivity'] - data['prev_conductivity'])
    return total_diff


def physarum_algorithm(G, demand_data, effective_distance_function, epsilon, get_subgraphs=False):
    graphs = create_subgraphs(G, demand_data)
    termination_criteria_met = False
    while not termination_criteria_met:
        for graph in graphs:
            calculate_node_pressures(graph)
            update_flow_and_conductivity(graph)
        calculate_total_flow(G, graphs)
        for graph in graphs:
            update_edge_length(G, graph, effective_distance_function)
        termination_criteria_met = calculate_term_criteria(graphs) <= epsilon
    if get_subgraphs:
        return graphs


if __name__ == '__main__':

    #random.seed(42)

    # Graph from first Instance

    # suppliers_nodes_list = [1, 2, 3]
    # dc_nodes_list = [4, 5]
    # retail_nodes_list = [6, 7]
    # edgelist = [(1, 4), (1, 5), (2, 4), (2, 5), (3, 5), (4, 6), (4, 7), (5, 7), (5, 6)]
    # demand_data = {1 : {6 : 2, 7 : 1},
    #                2 : {6 : 1, 7 : 1},
    #                3 : {6 : 0, 7 : 8}}
    # effective_distance_func = lambda Q : 5 + 3 * e ** (-0.3 * Q)
    # EPSILON = 0.01



    # Graph from second Instance

    suppliers_nodes_list = [1, 2, 3]
    dc_nodes_list = [4, 5, 6, 7, 8, 9]
    retail_nodes_list = [10, 11, 12]
    edgelist = [(1, 4), (1, 5), (1, 6), (2, 4), (2, 5), (3, 5), (3, 9), (4, 7), (5, 6), (5, 7), (5, 8), (5, 9), (6, 10), (6, 11), (7, 10), (7, 11), (8, 12), (9, 11), (9, 12)]
    demand_data = {1 : {10 : 5, 11 : 12, 12 : 3},
                   2 : {10 : 8, 11 : 2, 12 : 6},
                   3 : {10 : 6, 11 : 6, 12: 12}}
    effective_distance_func = lambda Q : 5 + 3 * e ** (-0.3 * Q)
    EPSILON = 1e-2

    start_time = time.time()
    G = create_graph(suppliers_nodes_list, dc_nodes_list, retail_nodes_list, edgelist)
    graphs = physarum_algorithm(G, demand_data, effective_distance_func, EPSILON, get_subgraphs=True)
    end_time = time.time()
    print(f"Time of executing is {end_time - start_time}")

    for g in graphs:
        print(f"Subnetwork = {g.graph['s_id']}")
        print(sorted(g.edges.data('flow'), key=lambda x: x[2], reverse=True))
    print(sorted(G.edges.data('flow'), key=lambda x: x[2], reverse=True))
    edges_dr = []
    for u, v, flow in G.edges.data('flow'):
        print(f"link: {u, v}, ed = {effective_distance_func(flow)}")
        if flow >= 1: edges_dr.append((u,v))
    nx.draw_planar(nx.edge_subgraph(G, edges_dr), with_labels=True, font_weight='bold')
    plt.show()