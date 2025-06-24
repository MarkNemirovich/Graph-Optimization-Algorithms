import networkx as nx
import random
import matplotlib.pyplot as plt
import general_graph as gen

# Создаёт граф с узлами разных типов (поставщики, распределительные центры, розничные точки)
# и рёбрами с начальными значениями потока (flow = 0).
def create_graph():
    G = nx.DiGraph()
    G.add_nodes_from(gen.suppliers_nodes_list, type='supplier')
    G.add_nodes_from(gen.dc_nodes_list, type='dc')
    G.add_nodes_from(gen.retail_nodes_list, type='retail')
    G.add_edges_from(gen.edgelist, flow=0)
    
    for u, v in G.edges:
        G.edges[u, v].update({
            'flow': 0,
            'pheromone': 1.0  # начальное значение феромона
        })
    return G

# Создаёт подграфы для каждого поставщика, который соединяется с распределительными центрами и розничными точками,
# и добавляет характеристики рёбер и узлов.
def create_subgraphs(G, demand_data):
    graphs = []
    suppliers = [n for n, t in G.nodes(data='type') if t == 'supplier']

    for supplier in suppliers:
        # Создаём пустой подграф
        g = nx.DiGraph()
        g.graph["s_id"] = supplier

        # Все узлы, достижимые из supplier по направлению рёбер
        reachable_nodes = nx.descendants(G, supplier)
        reachable_nodes.add(supplier)

        # Добавляем узлы
        for node in reachable_nodes:
            g.add_node(node, **G.nodes[node])
            g.nodes[node]['pressure'] = 0

        # Добавляем рёбра по направлению из исходного графа
        for u in reachable_nodes:
            for v in G.successors(u):
                if v in reachable_nodes:
                    g.add_edge(u, v, **G.edges[u, v])

        # Добавляем спрос
        g.nodes[supplier]['demand'] = demand_data.get(supplier, {})

        # Инициализация параметров рёбер
        for u, v in g.edges:
            g.edges[u, v].update({
                'flow': 0,
                'conductivity': random.uniform(1e-6, 1),
                'pheromone': G.edges[u, v].get('pheromone', 1.0),  # копия из оригинала
                'prev_conductivity': 0,
                'length': 1
            })

        graphs.append(g)

    return graphs

# Вывод графа
def draw_graph(G, edge_label_attr='flow', title = 'optimisation algorithm', solution = True, time = 0):
    fig, ax = plt.subplots(figsize=(16, 8))
    
    # Группируем узлы по типам
    suppliers = [n for n, d in G.nodes(data=True) if d.get('type') == 'supplier']
    dcs = [n for n, d in G.nodes(data=True) if d.get('type') == 'dc']
    retails = [n for n, d in G.nodes(data=True) if d.get('type') == 'retail']

    pos = {}
    pos.update(gen.spread(suppliers, y=2.0, margin=0.01))
    pos.update(gen.spread(dcs, y=0.5, shift=2))
    pos.update(gen.spread(retails, y=0.0, margin=0.02))

    # Цвета узлов
    node_colors = []
    for node, data in G.nodes(data=True):
        node_type = data.get('type')
        if node_type == 'supplier':
            node_colors.append('yellow')
        elif node_type == 'retail':
            node_colors.append('green')
        else:
            node_colors.append('gray')

    # Нарисовать узлы и подписи к ним
    nx.draw_networkx_nodes(G, pos, node_color=node_colors, ax=ax, node_size=300)
    nx.draw_networkx_labels(G, pos, ax=ax)

    # Рисуем все рёбра
    edges_to_draw = list(G.edges)

    nx.draw_networkx_edges(G, pos, ax=ax, edgelist=edges_to_draw, arrows=True, arrowstyle='->')

    # Подписи рёбер с выбранным атрибутом (flow, conductivity и т.п.)
    edge_labels = {
        (u, v): f"{d.get(edge_label_attr, 0):.2f}"
        for u, v, d in G.edges(data=True)
       if d.get(edge_label_attr, 0) >= 1
    }
    nx.draw_networkx_edge_labels(G, pos, edge_labels=edge_labels, ax=ax, font_size=8)

    ax.set_title(f"Oriented graph with edge labels: {edge_label_attr} for {title} provide {'correct' if solution else 'wrong'} solution for {time:.4f}", fontsize=14)
    plt.tight_layout()
    plt.show()
