import networkx as nx
import random
import matplotlib.pyplot as plt

# Создаёт граф с узлами разных типов (поставщики, распределительные центры, розничные точки)
# и рёбрами с начальными значениями потока (flow = 0).
def create_graph(suppliers_nodes_list, dc_nodes_list, retail_nodes_list, edgelist):
    G = nx.Graph()
    G.add_nodes_from(suppliers_nodes_list, type='supplier')
    G.add_nodes_from(dc_nodes_list, type='dc')
    G.add_nodes_from(retail_nodes_list, type='retail')
    G.add_edges_from(edgelist, flow=0)
    
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
    dc_and_retail = [n for n, t in G.nodes(data='type') if t in ('dc', 'retail')]
    suppliers = [n for n, t in G.nodes(data='type') if t == 'supplier']
    for supplier in suppliers:
        g = nx.subgraph(G, [supplier] + dc_and_retail).copy()
        g.graph["s_id"] = supplier
        g.nodes[supplier]['demand'] = demand_data[supplier]
        for i, j in g.edges:
            g.edges[i, j].update({
                'flow': 0,
                'conductivity': random.uniform(1e-6, 1),
                'pheromone': G.edges[i, j].get('pheromone', 1.0),  # копия из оригинала
                'prev_conductivity': 0,
                'length': 1
            })
        for node in g.nodes:
            g.nodes[node]['pressure'] = 0
        graphs.append(g)
    return graphs

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

# Вывод графа
def draw_graph(G, edge_label_attr='flow', title = 'optimisation algorithm', solution = True):
    fig, ax = plt.subplots(figsize=(16, 8))
    
    # Группируем узлы по типам
    suppliers = [n for n, d in G.nodes(data=True) if d.get('type') == 'supplier']
    dcs = [n for n, d in G.nodes(data=True) if d.get('type') == 'dc']
    retails = [n for n, d in G.nodes(data=True) if d.get('type') == 'retail']


    pos = {}
    pos.update(spread(suppliers, y=2.0, margin= 0.01))  # верх
    pos.update(spread(dcs, y=0.5, shift = 2))        # середина
    pos.update(spread(retails, y=0.0, margin= 0.02))    # низ

    # Определим цвета по типу узла
    node_colors = []
    for node in G.nodes(data=True):
        node_type = node[1].get('type')
        if node_type == 'supplier':
            node_colors.append('yellow')
        elif node_type == 'retail':
            node_colors.append('green')
        else:
            node_colors.append('gray')

    # Оставляем только рёбра с flow >= 1
    edges_to_draw = [
        (u, v) for u, v, d in G.edges(data=True)
     #   if d.get(edge_label_attr, 0) >= 1
    ]

    # Рисуем узлы и рёбра
    nx.draw(G, pos, with_labels=True, node_color=node_colors, edge_color='gray',
            edgelist=edges_to_draw, ax=ax)

    # Подписи рёбер с уменьшенным шрифтом
    edge_labels = {
        (u, v): f"{d[edge_label_attr]:.2f}"
        for u, v, d in G.edges(data=True)
       if d.get(edge_label_attr, 0) >= 1
    }
    nx.draw_networkx_edge_labels(
        G, pos, edge_labels=edge_labels, ax=ax, font_size=8
    )

    ax.set_title(f"Non-oriented graph with edge labels: {edge_label_attr} for {title} provide {'correct' if solution else 'wrong'} solution", fontsize=14)
    plt.tight_layout()
    plt.show()