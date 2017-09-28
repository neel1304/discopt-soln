#!/usr/bin/python3
# -*- coding: utf-8 -*-

from psutil import cpu_count
from gurobipy import *
import networkx as nx
# import numpy as np
# import cvxopt
# import cvxopt.glpk
# cvxopt.glpk.options['msg_lev'] = 'GLP_MSG_OFF'
# cvxopt.glpk.options['tm_lim'] = 100 * 10 ** 3 #ms
# cvxopt.glpk.options['mip_gap'] = 0.25 #

# python2.x only
# import constraint as cstrt

def solve_it(input_data):
    # Modify this code to run your optimization algorithm

    # parse the input
    lines = input_data.split('\n')

    first_line = lines[0].split()
    node_count = int(first_line[0])
    edge_count = int(first_line[1])

    edges = []
    for i in range(1, edge_count + 1):
        line = lines[i]
        parts = line.split()
        edges.append((int(parts[0]), int(parts[1])))

    # trivial solution
    # every node has its own color
    # ==========
    # solution = range(0, node_count)

    # greedy solution
    # n < 100 --> largest first greedy
    # n >= 100 --> independent set greedy
    # ==========
    # if node_count < 100:
    #     solution = greedy(node_count,
    #                       edges,
    #                       strategy=nx.coloring.strategy_largest_first)
    # else:
    #     solution = greedy(node_count,
    #                       edges,
    #                       strategy=nx.coloring.strategy_independent_set)

    # MIP solution using Gurobi
    # slow but optimal
    # ==========
    # print("V =", node_count)
    # print("E =", len(edges))
    solution = mip_gurobi(node_count, edges)

    # prepare the solution in the specified output format
    output_data = str(max(solution) + 1) + ' ' + str(0) + '\n'
    output_data += ' '.join(map(str, solution))

    return output_data


def mip_gurobi(node_count, edges, verbose=False, num_threads=None):
    m = Model("graph_coloring")
    m.setParam('OutputFlag', verbose)
    if num_threads:
        m.setParam("Threads", num_threads)
    else:
        m.setParam("Threads", cpu_count())

    colors = m.addVars(node_count, vtype=GRB.BINARY, name="colors")
    nodes = m.addVars(node_count, node_count, vtype=GRB.BINARY, name="assignments")
    # node[(node_idx, color_idx)]

    m.setObjective(quicksum(colors), GRB.MINIMIZE)

    # each node has only one color
    m.addConstrs((nodes.sum(i, "*") == 1
                  for i in range(node_count)),
                 name="eq1")

    # only color in use can be assigned ot nodes
    m.addConstrs((nodes[(i, k)] - colors[k] <= 0
                  for i in range(node_count)
                  for k in range(node_count)),
                 name="ieq2")

    # vertices sharing one edge have different colors
    m.addConstrs((nodes[(edge[0], k)] + nodes[(edge[1], k)] <= 1
                  for edge in edges
                  for k in range(node_count)),
                 name="ieq3")

    # color index should be as low as possible
    m.addConstrs((colors[i] - colors[i + 1] >= 0
                  for i in range(node_count - 1)),
                 name="ieq4")

    # more nodes should be assigned to color with lower index
    m.addConstrs((colors[i] * nodes.sum("*", i) - colors[i + 1] * nodes.sum("*", i + 1) >= 0
                  for i in range(node_count - 1)),
                 name="ieq5")

    m.update()
    m.optimize()

    isol = [int(var.x) for var in m.getVars()]
    soln = [j for i in range(node_count) for j in range(node_count)
            if isol[node_count + node_count * i + j] == 1]
    return soln


def greedy(node_count, edges, strategy):
    G = nx.Graph()
    G.add_nodes_from(range(node_count))
    G.add_edges_from(edges)
    coloring = nx.coloring.greedy_color(G=G, strategy=strategy)
    return list(coloring.values())


if __name__ == '__main__':
    import sys
    if len(sys.argv) > 1:
        file_location = sys.argv[1].strip()
        with open(file_location, 'r') as input_data_file:
            input_data = input_data_file.read()
        print(solve_it(input_data))
    else:
        print('This test requires an input file.  Please select one from the data directory. (i.e. python solver.py ./data/gc_4_1)')

