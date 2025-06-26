from sympy import symbols, diff, lambdify 
from non_oriented_graph import create_subgraphs

# Рассчитывает давление в каждом узле на основе связей и спроса (или предложения) с учётом проводимости рёбер.
# Для каждого узла вычисляется давление с использованием системы уравнений, аналогичной уравнению Пуассона,
# где давление зависит от связей с соседями и спроса/предложения.
def calculate_node_pressures(g):
    # Перебор узлов в подграфе g: node: текущий узел.
    # type - тип узла (например, supplier, retail или другие типы, например, dc — распределительные центры).
    nodes = g._nodes
    for node in g._node_list:
        equation_right = g._rhs[node]
        numerator = 0
        denominator = 0
        # Для каждого соседа:
        # Числитель рассчитывается как сумма произведений проводимости ребра,
        # делённой на длину ребра, и давления на соседнем узле:
        # Знаменатель — это сумма значений проводимости рёбер, делённой на их длину для всех соседей:
        for neighbour, data in g[node].items():
            w = data['conductivity'] / data['length']
            numerator   += w * nodes[neighbour]['pressure']
            denominator += w
        if denominator == 0:
            nodes[node]['pressure'] = 0  # или пропустить узел
        else:
            nodes[node]['pressure'] = (numerator - equation_right) / denominator

# Обновляет значения потока и проводимости для рёбер графа.
# Поток между двумя узлами пропорционален разности их давлений,
# а проводимость рёбер обновляется с учётом текущего потока.
def update_flow_and_conductivity(g):
    nodes = g._nodes
    edata = g._edata
    for i, j in g._edge_list:
        data = edata[i, j]
        # Поток через ребро между узлами 𝑖 и 𝑗 рассчитывается с учётом разницы их давлений:
        # Где: conductivity — проводимость рёбер, которая влияет на способность передавать поток,
        # length — длина ребра, которая может быть метафорой для "стоимости" или "удобства" пути,
        # pressure_i и pressure_j — давление в узлах 𝑖 и 𝑗, которые связаны этим ребром.
        pressure_diff = nodes[i]['pressure'] - nodes[j]['pressure']
        flow = data['conductivity'] / data['length'] * pressure_diff
        edata[i, j]['flow'] = flow
        prev = data['conductivity']
        edata[i, j]['prev_conductivity'] = prev
        edata[i, j]['conductivity'] = (prev + abs(flow)) / 2

# Подсчитывает общий поток по всему графу, суммируя потоки, вычисленные на уровне подграфов.
# Это позволяет обновить потоки на уровне всего графа с учётом всех локальных решений.
def calculate_total_flow(G, graphs):
    for edge in G.edges:
        G.edges[edge]['flow'] = 0
    for g in graphs:
        for i, j, flow in g.edges.data('flow'):
            if flow > 0:
                G.edges[i, j]['flow'] += flow


# Обновляет длину рёбер с учётом потока и функции эффективного расстояния E(Q).
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
            diff  += abs(d['conductivity'] - d['prev_conductivity'])
            total += d['prev_conductivity']
    return diff / (total + 1e-12) < tol

def _unpack_graph(g):
    # списки узлов и рёбер
    g._node_list = list(g.nodes())
    g._edge_list = list(g.edges())
    g._nodes     = g.nodes      # быстрая ссылка
    g._edata     = g.edges

    # --------- вычисляем правую часть b_i один раз -----------
    rhs = {}
    s_id = g.graph['s_id']      # «свой» поставщик для retail-узлов
    for node in g._node_list:
        ntype = g._nodes[node]['type']
        if ntype == 'supplier':
            rhs[node] = -sum(g._nodes[node]['demand'].values())
        elif ntype == 'retail':
            rhs[node] = g._nodes[s_id]['demand'].get(node, 0.0)
        else:
            rhs[node] = 0
    g._rhs = rhs            # кэш

def _refresh_cache(g):
    """пересчитать списки после удаления рёбер"""
    g._edge_list = list(g.edges())
    g._edata     = g.edges

# Алгоритм выполняет несколько итераций, в каждой из которых рассчитывает давление в узлах,
# обновляет потоки и проводимости рёбер, а затем обновляет длины рёбер.
def physarum_algorithm(G, demand_data, effective_distance_function, epsilon):
    graphs = create_subgraphs(G, demand_data)
    for g in graphs:
        _unpack_graph(g)
    # Создаём символьную переменную Q для функции E(Q), которая будет использоваться для вычисления расстояния.
    # Функция E(Q) используется для расчёта расстояния с учётом потока, а её производная помогает учитывать изменения в длине рёбер.
    # Вычисляем производную функции E(Q) по Q. Это даст нам информацию о том, как функция E(Q) изменяется
    # при изменении потока (Q). Производная будет использоваться для уточнения длины рёбер в зависимости от потока.
    Q = symbols('Q')
    E_sym  = effective_distance_function(Q)
    dE_sym = diff(E_sym, Q)
    # lambdify → превращаем в быстрые NumPy-функции
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
            # print(f"PPA converged in {iter_num} iterations")
            break
        
        if (iter_num+1) % check_every == 0:
                # 1. собираем список удаляемых рёбер
                edges_to_remove = [(i, j) for i, j in list(G.edges)
                                if G.edges[i, j]['flow'] < 1]

                if edges_to_remove:
                    # 2. удаляем из исходного графа
                    G.remove_edges_from(edges_to_remove)

                    # 3. удаляем из подграфов и обновляем кэш
                    for g in graphs:
                        g.remove_edges_from([e for e in edges_to_remove if g.has_edge(*e)])
                        _refresh_cache(g)                       #  <-- главное!

                    # print(f"Iteration {iter_num}: removed {len(edges_to_remove)} edges")
        
    return G