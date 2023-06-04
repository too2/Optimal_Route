class POI:
    def __init__(self, lng, lat, node_id):
        self.lng = lng
        self.lat = lat
        self.node_id = node_id  # 该POI所在的节点ID


class Path:
    def __init__(self, node):
        self.nodes = node  # 路径包含的节点列表
        self.leng = 0  # 路径的长度

    def add(self, node, ans_poi_dist_dict, p):
        self.nodes.append(node)
        if len(self.nodes) < 2:
            self.leng += ans_poi_dist_dict[(p.node_id, self.nodes[-1].node_id)]
        else:
            self.leng += ans_poi_dist_dict[(self.nodes[-2].node_id, self.nodes[-1].node_id)]

    def pop(self, ans_poi_dist_dict, p):
        if len(self.nodes) < 2:
            self.leng -= ans_poi_dist_dict[(p.node_id, self.nodes[-1].node_id)]
        else:
            self.leng -= ans_poi_dist_dict[(self.nodes[-2].node_id, self.nodes[-1].node_id)]
        self.nodes.pop()
