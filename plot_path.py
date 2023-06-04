import json
import os
import pandas as pd


def visual_result(traj, save_path, f, type_style="MultiLineString"):
    """
    Args:
        list traj
        String path
        String type_style(Multipoint, LineString, Point)
    Returns:
        .json
    """
    path = os.path.join(save_path, f)
    if os.path.exists(path):
        os.remove(path)
    with open(path, "w") as f:
        if type_style == 'LineString':
            json.dump(geo_json_generate(traj, type_style), f)
        elif type_style == 'Multipoint':
            json.dump(geo_json_generate_multipoint(traj, type_style), f)


def geo_json_generate(link_wkts, type_style="LineString"):
    res = {
        "type": "FeatureCollection",
        "features": []
    }
    for i, item in enumerate(link_wkts):
        t = {
            "type": "Feature",
            "geometry": {
                "type": type_style, "coordinates": item[0]
            },
            "properties": {
                'path_id': item[1],
                'criteria': item[2],
            }
        }
        res["features"].append(t)
    return res


def geo_json_generate_multipoint(link_wkts, type_style="LineString"):
    res = {
        "type": "FeatureCollection",
        "features": []
    }
    for i, item in enumerate(link_wkts):
        for j in range(len(item[0])):
            t = {
                "type": "Feature",
                "geometry": {
                    "type": type_style, "coordinates": [item[0][j]]
                },
                "properties": {
                    'path_id': item[1],
                    'criteria': item[2],
                }
            }
            res["features"].append(t)
    return res


def vis_trajs(G, paths, save_path, filename, mode='LineString'):
    path_list = []
    for path_id, (path, criteria) in enumerate(paths):
        coors = []
        for pt_osmid in path:
            lat, lng = G.nodes[pt_osmid]['y'], G.nodes[pt_osmid]['x']
            coors.append([lng, lat])
        path_list.append([coors, path_id, criteria])
    visfilename_point = f"{filename}_point.json"
    visfilename_line = f"{filename}_line.json"
    if mode == 'Multipoint':
        visual_result(path_list, save_path, visfilename_point, 'Multipoint')
    else:
        visual_result(path_list, save_path, visfilename_line, 'LineString')


if __name__ == "__main__":
    save_path = './save_plot_path'
    filename = 'DD201101001197'
    file_path = '/Volumes/T7/Where_Stop/new_traj_preprocess.csv'
    data = pd.read_csv(file_path)
    data = data[data['plan_no'] == 'DD201101001197']
    vis_trajs(data, save_path, filename, mode='Multipoint')
