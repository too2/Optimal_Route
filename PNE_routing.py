import osmnx as ox
import networkx as nx
import pygeohash as pgh
import time
from heapq import heappop, heappush
from itertools import count
from plot_path import vis_trajs
import pickle
from objclass import Path, POI
import copy


def nearest_node(G, poi, type_poi, poi_invert_index, ans_poi_dist_dict):
    """
    找到离poi最近的类型为type_poi的节点
    :param G:
    :param poi:
    :param type_poi:
    :param poi_invert_index:
    :param ans_poi_dist: 存放两个POI之间的距离
    :return:
    """
    poi_dist_list = []  # 用来进行候选POI的排序
    source = poi.node_id
    for target_poi in poi_invert_index[type_poi]:
        target = target_poi.node_id
        if (source, target) not in ans_poi_dist_dict:
            dist = nx.shortest_path_length(G, source, target, weight='length')
            ans_poi_dist_dict[(source, target)] = dist
        else:
            dist = ans_poi_dist_dict[(source, target)]
        poi_dist_list.append((target_poi, dist))
    poi_dist_list.sort(key=lambda x: x[1])
    return poi_dist_list[0][0]


def next_nearest_node(G, poi_p, poi_n, type_poi, poi_invert_index, ans_poi_dist_dict):
    """
    找到离poi_p次近的类型为type_poi的节点
    :param G:
    :param poi_p:
    :param poi_n:
    :param type_poi:
    :param poi_invert_index:
    :param ans_poi_dist_dict:
    :return:
    """
    poi_dist_list = []  # 用来进行候选POI的排序
    source = poi_p.node_id
    for target_poi in poi_invert_index[type_poi]:
        target = target_poi.node_id
        if (source, target) not in ans_poi_dist_dict:
            dist = nx.shortest_path_length(G, source, target, weight='length')
            ans_poi_dist_dict[(source, target)] = dist
        else:
            dist = ans_poi_dist_dict[(source, target)]
        poi_dist_list.append((target_poi, dist))
    poi_dist_list.sort(key=lambda x: x[1])
    flag = False  # 判断是否遍历过poi_n
    for target_poi, dist in poi_dist_list:
        if target_poi.node_id == poi_n.node_id:
            flag = True
        elif flag and target_poi.node_id != poi_n.node_id:
            return target_poi
    return None

def pne(G, p, type_seq, poi_invert_index, ans_poi_dist_dict):
    push = heappush
    pop = heappop
    H = []
    path = Path([])
    q = nearest_node(G, p, type_seq[1], poi_invert_index, ans_poi_dist_dict)
    path.add(q, ans_poi_dist_dict, p)
    push(H, (path.leng, path))
    while len(path.nodes) < len(type_seq)-1:
        dist, PSR = pop(H)
        k = len(PSR.nodes)
        if k == len(type_seq)-1:
            return PSR
        else:
            P_k = PSR.nodes[-1]
            P_k_plus_1 = nearest_node(G, P_k, type_seq[k+1], poi_invert_index, ans_poi_dist_dict)
            PSR_ = copy.deepcopy(PSR)
            # source, target = P_k.node_id, P_k_plus_1.node_id
            # if (source, target) not in ans_poi_dist_dict:
            #     dist = nx.shortest_path_length(G, source, target, weight='length')
            #     ans_poi_dist_dict[(source, target)] = dist
            PSR_.add(P_k_plus_1, ans_poi_dist_dict, p)
            push(H, (PSR_.leng, PSR_))
            if k > 1:
                P_k_minus_1 = PSR.nodes[-2]
                P_k_ = next_nearest_node(G, P_k_minus_1, P_k, type_seq[k], poi_invert_index, ans_poi_dist_dict)
                if not P_k_:
                    continue
                PSR_ = copy.deepcopy(PSR)
                PSR_.pop(ans_poi_dist_dict, p)
                # source, target = P_k_minus_1.node_id, P_k.node_id
                # if (source, target) not in ans_poi_dist_dict:
                #     dist = nx.shortest_path_length(G, source, target, weight='length')
                #     ans_poi_dist_dict[(source, target)] = dist
                PSR_.add(P_k_, ans_poi_dist_dict, p)
            else:
                p1 = PSR.nodes[0]
                P_k_ = next_nearest_node(G, p, p1, type_seq[1], poi_invert_index, ans_poi_dist_dict)
                if not P_k_:
                    continue
                PSR_ = Path([])
                PSR_.add(P_k_, ans_poi_dist_dict, p)
            push(H, (PSR_.leng, PSR_))


if __name__ == "__main__":
    t0 = time.time()
    # G = ox.io.load_graphml('/Volumes/T7/TDCT/保存路网/shandong.graphml')
    G = ox.graph_from_bbox(37.79, 37.78, -122.41, -122.43, network_type='drive')
    # ox.io.save_graph_geopackage(G, '/Volumes/T7/TDCT/保存路网/测试路网/test_map.gpkg', directed=True)
    t1 = time.time()
    print('加载路网：', t1-t0, 's')
    # ox.io.save_graphml(G, '/Volumes/T7/TDCT/保存路网/shandong_attr.graphml')
    # G = ox.io.load_graphml('/Volumes/T7/TDCT/保存路网/shandong_attr.graphml')
    print(len(G.nodes))
    print(len(G.edges))

    type_poi = ['srart', 'rest', 'gas', 'restaurant', 'destination']
    type_osmid = {'rest': [65350764, 65333839, 65317951], 'gas': [276546819, 65352457, 2351399563],
                        'restaurant': [65317957, 65334133, 65352330], 'destination': [65343958]}
    #
    poi_invert_index = {}
    for poi_type, osmid in type_osmid.items():
        for node_id in osmid:
            poi = POI(G.nodes[node_id]['x'], G.nodes[node_id]['y'], node_id)
            poi_invert_index.setdefault(poi_type, []).append(poi)
    t0 = time.time()
    p_osmid = 65292734  # 起点
    poi_p = POI(G.nodes[p_osmid]['x'], G.nodes[p_osmid]['y'], p_osmid)
    ans_poi_dist_dict = {}
    pne(G, poi_p, type_poi, poi_invert_index, ans_poi_dist_dict)
    t1 = time.time()
    print('花费耗时', t1-t0, 's')
