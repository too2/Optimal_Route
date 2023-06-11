import osmnx as ox
import networkx as nx
import time
from objclass import Path, POI


def gsp_simple(G, type_seq, poi_num, poi_invert_index):
    """
    GSP算法的简单实现
    :param G: 路网
    :param p: 起点
    :param type_seq: 类型序列
    :param poi_num: 每种类型的POI数量最大值
    :param poi_invert_index: poi倒排索引
    :return:
    """
    matrix = [[0 for _ in range(poi_num)] for _ in range(len(type_seq))]
    path = [[0 for _ in range(poi_num)] for _ in range(len(type_seq))]  # 记录路径
    for i, poi_type in enumerate(type_seq):
        if i == 0:  # 起点
            continue
        for j, poi in enumerate(poi_invert_index[poi_type]):
            min_dist = float('inf')
            for k in range(len(poi_invert_index[type_seq[i - 1]])):
                curr_dist = matrix[i - 1][j] + nx.shortest_path_length(G,
                            poi_invert_index[type_seq[i - 1]][k].node_id,
                            poi.node_id, weight='length')
                if curr_dist < min_dist:
                    min_dist = curr_dist
                    path[i][j] = (i-1, k)
            matrix[i][j] = min_dist
    return matrix, path


def construct_path(path):
    i, j = path[-1][0][0], path[-1][0][1]
    new_path = []
    while i != 0 or j != 0:
        new_path.append((i, j))
        i, j = path[i][j]
    return new_path[::-1]


if __name__ == "__main__":
    t0 = time.time()
    # G = ox.io.load_graphml('/Volumes/T7/TDCT/保存路网/shandong.graphml')
    G = ox.graph_from_bbox(37.79, 37.78, -122.41, -122.43, network_type='drive')
    # ox.io.save_graph_geopackage(G, '/Volumes/T7/TDCT/保存路网/测试路网/test_map.gpkg', directed=True)
    t1 = time.time()
    print('加载路网：', t1 - t0, 's')
    # ox.io.save_graphml(G, '/Volumes/T7/TDCT/保存路网/shandong_attr.graphml')
    # G = ox.io.load_graphml('/Volumes/T7/TDCT/保存路网/shandong_attr.graphml')
    print(len(G.nodes))
    print(len(G.edges))

    type_poi = ['start', 'rest', 'gas', 'restaurant', 'destination']
    type_osmid = {'start': [65292734], 'rest': [65350764, 65333839, 65317951], 'gas': [276546819, 65352457, 2351399563],
                  'restaurant': [65317957, 65334133, 65352330], 'destination': [65343958]}
    #
    #
    #
    poi_invert_index = {}
    for poi_type, osmid in type_osmid.items():
        for node_id in osmid:
            poi = POI(G.nodes[node_id]['x'], G.nodes[node_id]['y'], node_id)
            poi_invert_index.setdefault(poi_type, []).append(poi)
    t0 = time.time()
    # p_osmid = 65292734  # 起点
    # poi_p = POI(G.nodes[p_osmid]['x'], G.nodes[p_osmid]['y'], p_osmid)
    poi_num = 1
    for poi_list in poi_invert_index.values():
        if poi_num < len(poi_list):
            poi_num = len(poi_list)
    matrix, path = gsp_simple(G, type_poi, poi_num, poi_invert_index)
    print(matrix)
    print('____________________')
    print(path)
    print('____________________')
    print(construct_path(path))
    t1 = time.time()
    print('花费耗时', t1 - t0, 's')






