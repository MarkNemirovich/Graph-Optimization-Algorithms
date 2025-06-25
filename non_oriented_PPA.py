from sympy import symbols, diff, lambdify 
from non_oriented_graph import create_subgraphs

# Рассчитывает давление в каждом узле на основе связей и спроса (или предложения) с учётом проводимости рёбер.
# Для каждого узла вычисляется давление с использованием системы уравнений, аналогичной уравнению Пуассона,
# где давление зависит от связей с соседями и спроса/предложения.
def calculate_node_pressures(g):
    # Перебор узлов в подграфе g: node: текущий узел.
    # type - тип узла (например, supplier, retail или другие типы, например, dc — распределительные центры).
    for node, type in g.nodes(data='type'):
        # Для каждого узла вычисляется правый член уравнения для давления, в зависимости от типа узла:
        # Спрос каждого поставщика вычисляется как отрицательная сумма всех значений в словаре demand для этого узла.
        # Это нужно для того, чтобы учесть, что поставщик имеет отрицательный поток (он отдает товар).
        # Для розничной точки правый член уравнения — это спрос на товар от поставщика.
        # Извлекаем его требуемое количество товара для розничной точки.
        if type == 'supplier':
            equation_right = -sum(g.nodes[node]['demand'].values())
        elif type == 'retail':
            equation_right = g.nodes[g.graph['s_id']]['demand'][node]
        else:
            equation_right = 0
        numerator = 0
        denominator = 0
        # Для каждого соседа:
        # Числитель рассчитывается как сумма произведений проводимости ребра,
        # делённой на длину ребра, и давления на соседнем узле:
        # Знаменатель — это сумма значений проводимости рёбер, делённой на их длину для всех соседей:
        for neighbour, data in g[node].items():
            numerator += data['conductivity'] / data['length'] * g.nodes[neighbour]['pressure']
            denominator += data['conductivity'] / data['length']
        # Давление для узла обновляется как отношение числителя и знаменателя.
        # Это давление зависит от давления соседей, а также от спроса/предложения,
        # если узел является поставщиком или розничной точкой.
        g.nodes[node]['pressure'] = (numerator - equation_right) / denominator

# Обновляет значения потока и проводимости для рёбер графа.
# Поток между двумя узлами пропорционален разности их давлений,
# а проводимость рёбер обновляется с учётом текущего потока.
def update_flow_and_conductivity(g):
    # Перебирает все рёбра в графе g, где i и j — это узлы (концы ребра), а data — это словарь с атрибутами рёбер.
    for i, j, data in g.edges.data():
        # Поток через ребро между узлами 𝑖 и 𝑗 рассчитывается с учётом разницы их давлений:
        # Где: conductivity — проводимость рёбер, которая влияет на способность передавать поток,
        # length — длина ребра, которая может быть метафорой для "стоимости" или "удобства" пути,
        # pressure_i и pressure_j — давление в узлах 𝑖 и 𝑗, которые связаны этим ребром.
        pressure_diff = g.nodes[i]['pressure'] - g.nodes[j]['pressure']
        flow = data['conductivity'] / data['length'] * pressure_diff
        g.edges[i, j]['flow'] = flow
        prev = data['conductivity']
        g.edges[i, j]['prev_conductivity'] = prev
        g.edges[i, j]['conductivity'] = (prev + abs(flow)) / 2

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
    for i, j, data in g.edges.data():
        # Обновляем длину рёбер с учётом потока и функции эффективного расстояния E(Q).
        # data['length'] — это начальная длина ребра, которая будет скорректирована.
        # E(G.edges[i, j]['flow']) — это значение функции эффективного расстояния для текущего потока на ребре (i, j).
        # data['flow'] * dE.subs(Q, G.edges[i, j]['flow']) — это корректировка длины ребра на основе изменения потока,
        # используя производную функции E(Q), которая учитывает, как длина зависит от потока.
        flow = G.edges[i, j]['flow']
        g.edges[i, j]['length'] = (data['length'] + E_func(flow) + data['flow'] * dE_func(flow)) / 2

# Рассчитывает критерий остановки, основанный на разнице между текущей и предыдущей проводимостью рёбер.
def calculate_term_criteria(graphs):
    total_diff = 0
    total_diff = sum(
    abs(data['conductivity'] - data['prev_conductivity'])
    for g in graphs for _, _, data in g.edges(data=True)
)
    return total_diff

# Алгоритм выполняет несколько итераций, в каждой из которых рассчитывает давление в узлах,
# обновляет потоки и проводимости рёбер, а затем обновляет длины рёбер.
def physarum_algorithm(G, demand_data, effective_distance_function, epsilon):
    graphs = create_subgraphs(G, demand_data)
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
    while True:
        for g in graphs:
            calculate_node_pressures(g)
            update_flow_and_conductivity(g)

        calculate_total_flow(G, graphs)

        for g in graphs:
            update_edge_length(G, g, E_func, dE_func)

        if calculate_term_criteria(graphs) <= epsilon:
            break

    return G