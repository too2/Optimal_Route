import osmnx as ox
import networkx as nx
import pygeohash as pgh
import time
from heapq import heappop, heappush
from itertools import count
from plot_path import vis_trajs
import pickle


def add_road_attr(G):
    # 加上路段速度、通行时间和油耗
    G = ox.speed.add_edge_speeds(G)
    G = ox.speed.add_edge_travel_times(G)
    nodes, edges = ox.utils_graph.graph_to_gdfs(G)
    edges['fuel'] = (1600/edges['speed_kph']+73.8)*edges['length']/1000
    nx.set_edge_attributes(G, values=edges['fuel'], name='fuel')
    # 给路段加上POI属性
    with open('/Users/kxz/PycharmProjects/Where-Stop/new_model/ne.pickle', 'rb') as f:
        ne = pickle.load(f)
    with open('/Users/kxz/PycharmProjects/Where-Stop/new_model/poi_type.pickle', 'rb') as f:
        poi_type = pickle.load(f)
    ne_dict = {}
    for single_ne in ne:
        ne_dict[single_ne] = [0, 0, 0]
    poi_type_index = {'rest_area': 0, 'restaurant': 1, 'gas': 2}
    for single_ne, single_poi_type in zip(ne, poi_type):
        ne_dict[single_ne][poi_type_index[single_poi_type]] = 1
    edges['poi_type'] = edges.index.map(ne_dict)
    nx.set_edge_attributes(G, values=edges['poi_type'], name='poi_type')
    return G


class Path:
    def __init__(self, nodes, criteria):
        self.nodes = nodes  # 路径包含的节点列表
        self.criteria = criteria  # 路径的多个条件，当前为 'length', 'travel_time', 'fuel'


def update_paths(paths):
    new_paths = []
    for i in range(len(paths)):
        dominated_flag = False
        for j in range(len(paths)):
            if i != j and dominate_path(paths[j], paths[i]):
                dominated_flag = True
                break
        if not dominated_flag:
            new_paths.append(paths[i])
    return new_paths


def dominate_path(path1, path2):
    dominate_flag = False
    for i in range(len(path1.criteria)):
        if path1.criteria[i] > path2.criteria[i]:
            return False
        elif path1.criteria[i] < path2.criteria[i]:
            dominate_flag = True
    return dominate_flag


def _weight_function(G, weight):
    if G.is_multigraph():
        return lambda u, v, d: min(attr.get(weight, 1) for attr in d.values())
    return lambda u, v, data: data.get(weight, 1)


def print_paths(paths):
    paths_osmid = []
    for path in paths:
        print(path.nodes)
        paths_osmid.append([path.nodes, path.criteria])
    return paths_osmid


# 设置全局路径支配策略
def full_domin(curr_path, paths):
    flag = False
    for path in paths:
        for i in range(len(path.criteria)):
            flag = all([x > y for x, y in zip(curr_path.criteria, path.criteria)])
    return flag


# 设置部分路径支配
def part_domin(curr_path, p_domin):
    flag = False
    node = curr_path.nodes[-1]
    if node in p_domin:
        old_node_domin_criteria = p_domin[node]
        flag = all([x > y for x, y in zip(curr_path.criteria, old_node_domin_criteria)])
        if flag is True:
            return flag
        elif all([x < y for x, y in zip(curr_path.criteria, old_node_domin_criteria)]):
            p_domin[node] = curr_path.criteria
        else:
            return flag
    else:
        p_domin[node] = curr_path.criteria
        return flag


def find_skyline_path(G, ori_coord, dest_coord):
    G_succ = G._succ if G.is_directed() else G._adj

    push = heappush
    pop = heappop
    # fringe is heapq with 3-tuples (all_costs, c, path)
    # use the count c to avoid comparing nodes (may not be able to)
    c = count()
    fringe = []
    paths = []

    # 设置部分路径支配
    p_domin = {}

    # 创建一个初始路径，只包含起点
    # t0 = time.time()
    # start_node = ox.distance.nearest_nodes(G, *ori_coord)  # 根据编号找到起点节点
    # target_node = ox.distance.nearest_nodes(G, *dest_coord)
    # t1 = time.time()
    # print('查找节点耗时：', t1 - t0, 's')

    start_node = 295224575
    target_node = 65352330

    # 构造初始路径
    start_path = Path([start_node], [0, 0, 0])

    # 将初始路径加入队列
    push(fringe, (0, next(c), start_path))

    # 当队列不为空时循环
    while fringe:
        # 取出队列中的第一个节点
        (d, _, curr_path) = pop(fringe)
        # 如果当前节点是终点，则将当前路径加入结果列表，并更新结果列表
        curr_node = curr_path.nodes[-1]
        if curr_node == target_node:
            paths.append(curr_path)
            paths = update_paths(paths)
        # 否则，遍历当前节点连接的所有边
        else:
            for next_node in G_succ[curr_node]:
                # 如果下一个节点不在当前路径中，则创建一个新的路径，并更新其条件
                if next_node not in curr_path.nodes:
                    new_nodes = curr_path.nodes + [next_node]
                    new_criteria = []
                    for i, cost_name in enumerate(['length', 'travel_time', 'fuel']):
                        new_cost = curr_path.criteria[i] + float(G.edges[curr_node, next_node, 0][cost_name])
                        new_criteria.append(new_cost)
                    new_path = Path(new_nodes, new_criteria)
                    # 部分路径支配策略
                    if part_domin(new_path, p_domin) is True:
                        continue
                    # 全局路径支配策略
                    if full_domin(new_path, paths) is True:
                        continue
                    # 计算当前点到终点的估计下界
                    lat1, lng1 = G.nodes[next_node]['y'], G.nodes[next_node]['x']
                    lat2, lng2 = G.nodes[target_node]['y'], G.nodes[target_node]['x']
                    esti_lowest = ox.distance.great_circle_vec(lat1, lng1, lat2, lng2)*len(curr_path.criteria)
                    # 将新的路径加入队列
                    push(fringe, (sum(new_path.criteria)+esti_lowest, next(c), new_path))
    # 返回结果列表（可能为空）
    t2 = time.time()
    print('查找节点耗时：', t2 - t1, 's')
    return paths


def plot_line(G, paths):
    save_path = './save_plot_path'
    filename = 'path_' + str(paths[0][0][0]) + '_' + str(paths[0][0][-1])
    vis_trajs(G, paths, save_path, filename, mode='LineString')


if __name__ == "__main__":
    t0 = time.time()
    # G = ox.io.load_graphml('/Volumes/T7/TDCT/保存路网/shandong.graphml')
    G = ox.graph_from_bbox(37.79, 37.78, -122.41, -122.43, network_type='drive')
    t1 = time.time()
    print('加载路网：', t1-t0, 's')
    G = add_road_attr(G)
    t2 = time.time()
    print('添加边属性：', t2 - t1, 's')
    # ox.io.save_graphml(G, '/Volumes/T7/TDCT/保存路网/shandong_attr.graphml')
    # G = ox.io.load_graphml('/Volumes/T7/TDCT/保存路网/shandong_attr.graphml')
    print(len(G.nodes))
    print(len(G.edges))
    # ori_coord = (119.11608, 35.07043)
    # dest_coord = (119.42217, 35.36645)
    t0 = time.time()
    paths = find_skyline_path(G, None, None)
    t1 = time.time()
    paths_osmid = print_paths(paths)
    plot_line(G, paths_osmid)
    print(t1 - t0, 's')
