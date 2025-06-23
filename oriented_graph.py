import networkx as nx
import random
import matplotlib.pyplot as plt

# Создаёт граф с узлами разных типов (поставщики, распределительные центры, розничные точки)
# и рёбрами с начальными значениями потока (flow = 0).
def create_graph(suppliers_nodes_list, dc_nodes_list, retail_nodes_list, edgelist):
    G = nx.DiGraph()
    G.add_nodes_from(suppliers_nodes_list, type='supplier')
    G.add_nodes_from(dc_nodes_list, type='dc')
    G.add_nodes_from(retail_nodes_list, type='retail')
    G.add_edges_from(edgelist, flow=0)
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
                'prev_conductivity': 0,
                'length': 1
            })

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
def draw_graph(G, edge_label_attr='flow'):
    fig, ax = plt.subplots(figsize=(16, 8))
    
    # Группируем узлы по типам
    suppliers = [n for n, d in G.nodes(data=True) if d.get('type') == 'supplier']
    dcs = [n for n, d in G.nodes(data=True) if d.get('type') == 'dc']
    retails = [n for n, d in G.nodes(data=True) if d.get('type') == 'retail']

    pos = {}
    pos.update(spread(suppliers, y=2.0, margin=0.01))
    pos.update(spread(dcs, y=0.5, shift=2))
    pos.update(spread(retails, y=0.0, margin=0.02))

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
    }
    nx.draw_networkx_edge_labels(G, pos, edge_labels=edge_labels, ax=ax, font_size=8)

    ax.set_title(f"Graph with edge labels: {edge_label_attr}", fontsize=14)
    plt.tight_layout()
    plt.show()
