# algorithm_utils.py
import networkx as nx
from sympy import symbols, diff

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
        # Учитываем как входящие, так и исходящие рёбра
        for neighbour in set(g.predecessors(node)).union(g.successors(node)):
            if (neighbour, node) in g.edges:  # Входящее ребро
                data = g.edges[neighbour, node]
                numerator += data['conductivity'] / data['length'] * g.nodes[neighbour]['pressure']
                denominator += data['conductivity'] / data['length']
            if (node, neighbour) in g.edges:  # Исходящее ребро
                data = g.edges[node, neighbour]
                numerator += data['conductivity'] / data['length'] * g.nodes[neighbour]['pressure']
                denominator += data['conductivity'] / data['length']
        if denominator != 0:
            g.nodes[node]['pressure'] = (numerator - equation_right) / denominator
        else:
            g.nodes[node]['pressure'] = 0

# Обновляет значения потока и проводимости для рёбер графа.
# Поток между двумя узлами пропорционален разности их давлений,
# а проводимость рёбер обновляется с учётом текущего потока.
def update_flow_and_conductivity(g):
    # Перебирает все рёбра в графе g, где i и j — это узлы (концы ребра), а data — это словарь с атрибутами рёбер.
    # Атрибуты рёбер включают такие параметры, как flow, conductivity, length и другие.
    for i, j in g.edges:
        # Поток через ребро между узлами 𝑖 и 𝑗 рассчитывается с учётом разницы их давлений:
        # Давление в узлах рассчитывается ранее, в функции calculate_node_pressures.
        # Где: conductivity — проводимость рёбер, которая влияет на способность передавать поток,
        # length — длина ребра, которая может быть метафорой для "стоимости" или "удобства" пути,
        # pressure_i и pressure_j — давление в узлах 𝑖 и 𝑗, которые связаны этим ребром.
        flow = g.edges[i, j]['conductivity'] / g.edges[i, j]['length'] * (g.nodes[i]['pressure'] - g.nodes[j]['pressure'])
        # Округляем поток до целого
        g.edges[i, j]['flow'] = round(flow)
    # После того как поток был обновлён, проводимость рёбер также обновляется:
    # prev_conductivity сохраняет предыдущее значение проводимости.
    # Это важно для вычислений в следующих итерациях, чтобы отслеживать изменения в проводимости рёбер.
    # conductivity обновляется как среднее значение между текущей проводимостью и абсолютным значением потока:
    # Это моделирует усиление проводимости для рёбер, через которые проходит больший поток,
    # и ослабление проводимости для рёбер с малым потоком. Иными словами, рёбра,
    # через которые течет больше вещества (или потока), становятся "легче" для прохождения в будущем,
    # а те, через которые поток мал, становятся "труднее".
    for i, j, data in g.edges.data():
        g.edges[i, j]['prev_conductivity'] = g.edges[i, j]['conductivity']
        g.edges[i, j]['conductivity'] = (g.edges[i, j]['conductivity'] + abs(g.edges[i, j]['flow'])) / 2

# Подсчитывает общий поток по всему графу, суммируя потоки, вычисленные на уровне подграфов.
# Это позволяет обновить потоки на уровне всего графа с учётом всех локальных решений.
def calculate_total_flow(G, graphs):
    # Этот шаг сбрасывает значения потока для всех рёбер в основном графе 𝐺.
    # Вначале потоки на рёбрах устанавливаются в 0,
    # чтобы обеспечить корректный пересчёт потоков на следующем этапе.
    for edge in G.edges:
        G.edges[edge]['flow'] = 0
    # Здесь происходит суммирование потоков по каждому подграфу:
    # Для каждого подграфа перебираются рёбра и извлекаются потоки.
    # В g.edges.data('flow') возвращается список всех рёбер в подграфе с их атрибутами,
    # и в частности — значением потока, сохранённым в атрибуте 'flow'.
    for g in graphs:
        for i, j, flow in g.edges.data('flow'):
            if flow > 0:
            # Для каждого ребра в подграфе поток добавляется к соответствующему ребру в основном графе 𝐺 с помощью:
                G.edges[i, j]['flow'] += flow


# Обновляет длину рёбер с учётом потока и функции эффективного расстояния E(Q).
# Функция E(Q) используется для расчёта расстояния с учётом потока, а её производная помогает учитывать изменения в длине рёбер.
def update_edge_length(G, g, E):
    # Создаём символьную переменную Q для функции E(Q), которая будет использоваться для вычисления расстояния.
    Q = symbols('Q')
    # Вычисляем производную функции E(Q) по Q. Это даст нам информацию о том, как функция E(Q) изменяется
    # при изменении потока (Q). Производная будет использоваться для уточнения длины рёбер в зависимости от потока.
    dE = diff(E(Q), Q)
    # Перебираем все рёбра подграфа g
    for i, j, data in g.edges.data():
        # Обновляем длину рёбер с учётом потока и функции эффективного расстояния E(Q).
        # data['length'] — это начальная длина ребра, которая будет скорректирована.
        # E(G.edges[i, j]['flow']) — это значение функции эффективного расстояния для текущего потока на ребре (i, j).
        # data['flow'] * dE.subs(Q, G.edges[i, j]['flow']) — это корректировка длины ребра на основе изменения потока,
        # используя производную функции E(Q), которая учитывает, как длина зависит от потока.
        # В конце всё усредняется для более сбалансированного изменения длины.
        g.edges[i, j]['length'] = (data['length'] + E(G.edges[i, j]['flow']) + data['flow'] * dE.subs(Q, G.edges[i, j][
            'flow'])) / 2
        print(f"Final length on edge {i}->{j}: {g.edges[i, j]['length']:.6f}")
# Рассчитывает критерий остановки, основанный на разнице между текущей и предыдущей проводимостью рёбер.
# Это помогает определить, насколько алгоритм стабилизировался и достиг оптимального состояния.
def calculate_term_criteria(graphs):
    total_diff = 0
    for g in graphs:
        # g.edges.data() возвращает список всех рёбер в подграфе g с их атрибутами.
        # Каждый элемент этого списка представляет собой кортеж (i, j, data), где:
        # i и j — это узлы, которые соединяет ребро.
        # data — это словарь с атрибутами для рёбер: 'conductivity' (проводимость) и 'prev_conductivity' (предыдущая проводимость).
        for i, j, data in g.edges.data():
            total_diff += abs(data['conductivity'] - data['prev_conductivity'])
    return total_diff

# Реализует алгоритм слизевика для оптимизации транспортных потоков.
# Алгоритм выполняет несколько итераций, в каждой из которых рассчитывает давление в узлах,
# обновляет потоки и проводимости рёбер, а затем обновляет длины рёбер.
def physarum_algorithm(G, demand_data, effective_distance_function, epsilon, get_subgraphs=False, min_capacity = 0, check_every=10):
    graphs = create_subgraphs = __import__('restricted_graph').create_subgraphs
    graphs = create_subgraphs(G, demand_data)
    termination_criteria_met = False
    iteration = 0
    while not termination_criteria_met:
        for graph in graphs: # для каждого подграфа вычислить давление в узлах и обновить поток через ребра
            calculate_node_pressures(graph)
            update_flow_and_conductivity(graph)
        # Рассчитать потоки через ребра общего графа
        calculate_total_flow(G, graphs)
        for graph in graphs:
            # Обновление эффективной длины ребер
            update_edge_length(G, graph, effective_distance_function)
        termination_criteria_met = calculate_term_criteria(graphs) <= epsilon # условие завершения оптимизации
        iteration+=1
        
        if iteration % check_every == 0:
                edges_to_remove = []
                for i, j in list(G.edges):
                    flow = G.edges[i, j]['flow']
                    if flow < min_capacity:
                        edges_to_remove.append((i, j))
                for edge in edges_to_remove:
                    G.remove_edge(*edge)
                    # Удаляем ребра из подграфов тоже
                    for g in graphs:
                        if g.has_edge(*edge):
                            g.remove_edge(*edge)
                # Можно добавить перерасчет подграфов или лог для информации
                print(f"Iteration {iteration}: Removed {len(edges_to_remove)} edges due to capacity constraints")
        
        for i, j in G.edges:
            print(f"Iteration {iteration}. Final flow on edge {i}->{j}: {G.edges[i,j]['flow']:.6f}")
    if get_subgraphs:
        return graphs