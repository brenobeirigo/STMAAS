# New network info
import osmnx as ox
import os.path
import pprint
import matplotlib.pyplot as plt
import numpy as np
import networkx as nx
from networkx import NetworkXError
from IPython.display import IFrame
from random import choice
import itertools
from collections import defaultdict
from ast import literal_eval
import Node
from copy import deepcopy
# -*- coding: utf-8 -*-
import json

width_img = 15
height_img = 10
show_img = False
dpi_img = 300
root = "data/network/"
subfolder = "network/"
instance_path_network = "instances/hybrid/networks/"

"""By default, the size of the new presentation in PowerPoint, 
is currently a widescreen type presentation, 13.333 inch by 7.5 inch.
Mostly you will have 96 dots per inch (dpi) on your screen settings,
so this means that a default PowerPoint presentation has a resolution
of 1280 by 720 pixels.

"""  # Make it work for Python 2+3 and with Unicode
import io
try:
    to_unicode = unicode
except NameError:
    to_unicode = str

# Mode colors
mode_colors = {"conventional": {"color": "gray", "width": 1, "nsize": 1},
               "autonomous": {"color": "red", "width": 1.5, "nsize": 1, "nsize_seed": 30},
               "transfer": {"color": "blue", "width": 1, "nsize": 1}}

vehicle_modes = ["autonomous", "conventional", "dual"]


def get_graph_from_place(place, network_type):
    return ox.graph_from_place(place, network_type=network_type)

def save_network(G, file_name, folder):
    print("Saving network at ", file_name,"...")
    print("Graph name: ",G.graph["name"])
    ox.save_graphml(G, filename=file_name, folder=folder)

def load_network(filename, folder=None):
    if filename.find(".graphml") < 0:
        filename = filename + ".graphml"
    return ox.load_graphml(filename=filename, folder=folder)

def get_boxed_graph(location_point, distance):
    return ox.graph_from_point(location_point, distance=distance)

def clean_nodes_by_degree(G, degree):
    """Remove all nodes of G in which degree (inbound+outbound)
    is equals to degree.

    Arguments:
        G {networkx} -- Graph
        degree {int} -- Target degree to be removed
    """

    nodes = list(G.nodes())
    print(" - Size BEFORE removal:", len(nodes))

    for n in nodes:
        if G.degree(n) == degree:
            G.remove_node(n)

    nodes = list(G.nodes())
    print(" - Size AFTER removal:", len(nodes))

def remove_edges(G, m):
    """ Remove all edges different than mode m.

    Arguments:
        G {networkx} -- Street network
        m {string} -- Driving mode to be removed
    """
    # Get list of edges
    edges = list(G.edges())
    print(" - Size BEFORE removal:", len(edges))
    
    # List of edges to be removed
    edge_removal_list = list()

    # For all edges e
    for e in edges:
        
        # Get list of edges between two nodes
        parallel_edges = list(G[e[0]][e[1]].values())

        # For each edge between two nodes
        for a in parallel_edges:
            # If edge type is is different than mode m
            if a['mode_edge'] != m:
                edge_removal_list.append((e[0], e[1]))

    # Remove all edges different then mode m
    G.remove_edges_from(edge_removal_list)
    node_removal_list = list()

    # Remove all nodes left disconnected (degree = 0)
    for n in G.nodes():
        if G.degree(n) == 0:
            node_removal_list.append(n)

    # Remove all nodes with degree = 0
    G.remove_nodes_from(node_removal_list)

    # New list of edges
    edges = list(G.edges())
    print(" - Size AFTER removal:", len(edges)) #, edges)

    """if len(G.edges()) > 0:
        # Save intermediate network
        save_pic(network=G, seeds=[], save_fig=True,
                 file_name=G.graph["name"]+m)"""

    if len(G.edges()) == 0:
        print("NETWORK OF TYPE \"", m, "\" HAS NO EDGES.")

def save_dist_dic(data, file_name):
    # Write JSON file
    print("Saving distances at \"",file_name,"\"...")
    with io.open(file_name, 'w', encoding='utf8') as outfile:
        str_ = json.dumps(data,
                          indent=4, sort_keys=True,
                          separators=(',', ': '), ensure_ascii=False)
        outfile.write(to_unicode(str_))

def load_dist_dic(path):
    if path.find(".json") < 0:
        path = path + ".json"

    # Read JSON file
    with open(path) as data_file:
        data_loaded = json.load(data_file)
    return data_loaded

def get_random_nodes(G, n):
    """Select "n" random nodes from G.

    Arguments:
        G {networkx} -- Graph
        n {int} ------- Number of random nodes to be selected

    Returns:
        set ----------- Set of random nodes
    """

    nodes = list(G.nodes())
    random_nodes = set()
    while len(random_nodes) < n:
        random_node = choice(nodes)
        random_nodes.add(random_node)
    return random_nodes

def create_subnetwork(G, mode, percentage=0, target_nodes=None):
    print("Creating subnetworks (",len(G.nodes()),")...")
    def get_nodes_sp(G, target):
        """Get the shortest path between all pairs in target
           nodes. If the length of the target node is 1, return
           the own target.
        
        Arguments:
            G {networkx} -- Graph
            target {set} -- Target nodes to form subnetworks
        
        Returns:
            set -- Shortest paths between all target nodes.
                   Assign "mode" to all G edges connecting
                   shortest paths.
        """
        
        # Target node is always in the subnetwork
        subnetwork_nodes = set(target)

        # All pairs in the "target" set will have their shortest paths
        # integrated to the final subnetwork
        pairs = list(itertools.permutations(list(target), 2))
        
        print("Number of subnetwork OD pairs:", len(pairs))
        # Connect each pair in target nodes
        for p in pairs:
            # If network does not have a path between nodes
            if not nx.has_path(G, p[0], p[1]):
                print("TEM QUE TER!@!!!!!!!!!!!!!!!!!!")
                continue

            # Get all nodes featured in the shortest path between OD
            sp = nx.shortest_path(G, p[0], p[1])

            # For each OD pair in the shortest path
            for i in range(0, len(sp)-1):
                
                # Add pair to the subnetwork
                subnetwork_nodes.add(sp[i])
                subnetwork_nodes.add(sp[i+1])
                
                # Loop all edges between a pair (parallel)
                # to assign the mode
                for edge in G[sp[i]][sp[i+1]].values():
                    edge['mode_edge'] = mode
        
        return subnetwork_nodes

    """Create a subnetwork in G.
       If percentage > 0, connects percentage*G.nodes() nodes
       of the graph using the shortest paths between pairs.
       If percentage = 0, the nodes in the set "target_nodes"
       are connected instead.

    Arguments:
        G {networkx} -------- Strongly connected graph 

    Keyword Arguments:
        percentage {float} -- Percentage of nodes that will be connected
                              in the graph (default: {0})
        target_nodes {set} -- Set of nodes that will be connected.
                              Warning: the nodes of the set are guaranted to
                              be connected since G is strongly connected.
                              (default: {None})
        mode {string} ------- Mode of subnetwork.
    Returns:
        set ----------------- Nodes belonging to the subnetwork.
    """
    print("CREATING SUBNETWORKS...")
    
    # Redefine G
    G = deepcopy(G)

    # Edges are all conventional from start
    nx.set_edge_attributes(G, "conventional", 'mode_edge')

    # Nodes are all transfer from start
    nx.set_node_attributes(G, "transfer", "mode_node")

    # Target nodes to be connected
    target = target_nodes

    # Nodes of G
    nodes = list(G.nodes())

    min_num_nodes = len(nodes)*percentage
    starting_nodes = 2
    
    # Subnetwork nodes from shortest paths
    subnetwork_nodes = None

    # Create random set of target nodes according to percentage.
    if percentage > 0:
        print("Creating a ", min_num_nodes," nodes subnetwork...")

        while True:
            target = get_random_nodes(G, starting_nodes)
            print("Number of seeds:", len(target))

            # Final set of nodes belonging to the subnetwork
            subnetwork_nodes = get_nodes_sp(G,target)

            largest_cc = get_nodes_from_largest_components(G, subnetwork_nodes, target)
            
            print("largest_cc (",len(largest_cc),") / subnetworks (", len(subnetwork_nodes),") / (", min_num_nodes,")")
            
            
            
            # If the percentage of nodes was achieved
            if(len(subnetwork_nodes) >= min_num_nodes):
                break
            
            starting_nodes = starting_nodes + 1
        G.graph["seeds"] = str(target)

        # Show the result
        print("Setting subnetwork nodes...")
        set_nodes_from_mode(G)
        

        return G

    else:
        print("Getting SP nodes from target set",target,"(",len(target),")")
        G.graph["seeds"] = str(target)
        # Uses the set of target nodes to create a subnetwork
        subnetwork_nodes = get_nodes_sp(G, target)
        return subnetwork_nodes

def create_distance_data(G, modes=["autonomous", "conventional"]):
    """Calculate the shortest paths between all points.
    
    Arguments:
        G {networkx} -- Graph with zones/subnetworks
    
    Keyword Arguments:
        modes {list} -- What modes should be identified (default: {["autonomous", "conventional"]})
    
    Returns:
        dic -- Distance data
    """
    # if a key is not found in the dictionary, then instead
    # of a KeyError being thrown, a new entry is created
    dic = defaultdict(dict) #empty dict is created
    
    # For every driving mode present in the network
    for m in modes:
        print("Working on ", m, " network")
        
        # Create a copy of the network
        M = deepcopy(G)
        print("- Removing distinct edges...")
        
        # Remove all edges whose type is not m
        remove_edges(M, m)
        print("- Calculating shortest paths...")
        
        # Get distance of all possible OD pairs in M
        all_pairs_m = nx.all_pairs_dijkstra_path_length(M, None, "length")
        for o in all_pairs_m:
            dic[o[0]][m] = o[1]
    
    print("DUAL - Calculating shortest paths...")
    # Dual mode vehicles drive irrestrictably
    all_pairs = nx.all_pairs_dijkstra_path_length(G, None, "length")
    for o in all_pairs:
        #e.g.:"27082148": {"dual": {"27082148": 0,"44750651": 2964.1096261713997}}
        dic[o[0]]["dual"] = o[1]

    return dic

def set_nodes_from_mode(G, modes=["conventional", "autonomous"]):
    """  A node is considered a node from mode "m" if
    there is at least one inbound and one outbound arc
    of mode "m"

    What happens when a transfer node has inbound and outbound edges
    of different modes?

    Arguments:
        G {networkx} -- Street network
        m {string} -- Mode (e.g. autonomous)
    Returns:
        set -- Set of nodes of type "m"
    """
    print("# Setting up nodes...")
    # Dictionary of nodes associated to each node
    nodes_mode = dict()
    for m in modes:
        for o in G.nodes():
            # Node "o" starts as a node from type "o"
            o_mode_out = True
            o_mode_in = True
            # For all neighbors of node "o"
            successors = list(G.successors(o))
            predecessors = list(G.predecessors(o))

            #print(successors, predecessors)
            around = set()
            around.update(predecessors)
            around.update(successors)
            # print(around)

            for d in around:
                # If there are edges from "o" to "d"
                if G.has_edge(o, d):
                    # For every possible edge (might have parallel edges)
                    for e in G[o][d].values():
                        # If there is one edge of type "mode"
                        if e["mode_edge"] != m:
                            o_mode_out = False
                            break
                    # node is already not from mode "m"
                    if not o_mode_out:
                        break

                # If there are edges from "o" to "d"
                if G.has_edge(d, o):
                    # For every possible edge (might have parallel edges)
                    for e in G[d][o].values():
                        # If there is one edge of type "mode"
                        if e["mode_edge"] != m:
                            o_mode_in = False
                            break

                    # node is already not from mode "m"
                    if not o_mode_in:
                        break

            # If all edges connected to "o" are from "m"
            if o_mode_out and o_mode_in:
                G.node[o]["mode_node"] = m
                if m not in nodes_mode.keys():
                    nodes_mode[m] = set()
                nodes_mode[m].add(o)

    # Transfer nodes are all nodes that are neither autonomous nor
    # conventional
    transfer = set(G.nodes())

    """# Remove autonomous and conventional nodes of total set of nodes
    print("TRANSFER")
    for m,nodes in nodes_mode.items():
        transfer.difference_update(nodes)
    
    print("Graph:", len(G.nodes()))
    
    for t in transfer:
        
        successors = set(G.successors(t))
        inbound = [e["mode_edge"] for to in successors for e in G[t][to].values()]
        
        predecessors = set(G.predecessors(t))
        outbound = [e["mode_edge"] for fr in predecessors for e in G[fr][t].values()]

        inter = set(inbound).intersection(outbound)
   

        if len(inter) == 0:
            print("INTERSECTION", t," = ", inbound, outbound, intersection)
        
    for m,i in nodes_mode.items():
        print(m,len(i))
        print("TRANSFER = ",
              m,
              len(i),
              ":",
              len(transfer),
              "-",
              len(transfer.intersection(i)))"""

    # Save transfer nodes to key "transfer"
    nodes_mode["transfer"] = transfer

    # Save nodes per mode in G
    G.graph["mode_nodes"] = nodes_mode

def assign_modes(G, nodes, mode="autonomous"):
    """Assign mode "mode" to the edges between pairs of connected
       nodes (incidence matrix).

    Arguments:
        G {networkx} --- Graph
        nodes {set} ---- Nodes
        mode {string} -- [description]
    """

    # Get the incidence list for each node
    incidence_matrix = nx.to_dict_of_lists(G)
    # For each origin o in the set of current seeds
    for o in nodes:
        # Get the incidence matrix of each origin o in current seed
        d_list = set(incidence_matrix[o]).intersection(nodes)

        # For each destination d connected to the origin o
        for d in d_list:
            # From/to edge is changed to mode m. Since parallel edges
            # may exist, all possible edges are looped
            for e in G[o][d].values():
                e["mode_edge"] = mode

            # If existent, to/from edge is changed to mode m. Since
            # parallel edges may exist, all parallel edges are looped
            if G.has_edge(d, o):
                for e in G[d][o].values():
                    e['mode_edge'] = mode

def get_nodes_from_largest_components(G, zone_nodes, seeds):
    print("Get zoned subgraph:")
    zoned_subgraph = get_subgraph_from_nodes(G, zone_nodes)
    print("#nodes zoned subgraph:", len(zoned_subgraph.nodes())
    , "/", len(G.nodes()))

    # Get all components built around seeds
    components = get_largest_connected_components(zoned_subgraph, seeds)

    # Merge components
    nodes_from_components = set([n for c in components for n in c])

    print("Components: ",
                  [len(c) for c in components],
                  "(", len(nodes_from_components),")")

    return nodes_from_components

def get_zoned_network(G, mode="autonomous", n_zones=1, percentage=0):
    """
    Create "n_zones" areas of mode "mode". For each seed,
    the areas expands "degree" degrees.

    Arguments:
        G {networkx} -------- Strongly connected graph
        n_nodes {list} ------ Number of seeds, that is, the starting
                              nodes where the expansion begins.
        degree {integer} ---- How many hops surrounding the seed.
        percentage {float} -- Total percentage of nodes affected
                              by the expansion
        mode {string} ------- Driving mode of the zone
    """
    # Z will be the graph with the subnetworks
    # Create zoned graph
    Z = deepcopy(G)

    # Define graph name
    # Z.graph["name"] = '{0}_{1}'.format(Z.graph["name"], mode)

    # Edges are all conventional from start
    nx.set_edge_attributes(Z, "conventional", 'mode_edge')

    # Nodes are all transfer from start
    nx.set_node_attributes(Z, "transfer", "mode_node")

    print("CREATING ZONES...")
    
    # Get nodes
    nodes = list(Z.nodes())
    
    # Get the incidence list for each node
    incidence_matrix = nx.to_dict_of_lists(Z)
    
    # Set of "n_zones" nodes randomly chosen
    seeds = get_random_nodes(Z, n_zones)
    
    # Store the seeds in grap parameters
    Z.graph["seeds"] = str(seeds)
    
    # List of flooding origins, i.e. the starting points (seeds)
    # of each zone. The origins are updated at each iteration
    current_seeds = set(seeds)

    # Set of all nodes already added in the zone
    zone_nodes = set()

    # Minimum number of nodes in mode
    min_nodes_mode = int(percentage*len(Z.nodes()))

    # Index of expanded levels
    i = 0
    while True:
        i = i+1
        print("    Expanded level", i, "...")
        # Update the set of elements belonging to the zone
        zone_nodes.update(current_seeds)
        # Set of nodes sorrounding the nodes of o_list
        around_seeds = set()
        # For each origin o in the set of current seeds
        for o in current_seeds:
            # Get the incidence matrix of each origin o in current seed
            d_list = set(incidence_matrix[o])
            # Get the nodes surrounding "o" not yet expanded. The expanded
            # nodes are all in the "zone_nodes"
            around_o = d_list.difference(zone_nodes)
            # Update the set of seeds surrounding all "o"'s
            around_seeds.update(around_o)
        # The new set of seeds to be expanded is the set of all surrounding
        # nodes in the previously expanded current seeds
        current_seeds = set(around_seeds)

        # Merge components
        all_components = get_nodes_from_largest_components(Z, zone_nodes, seeds)
        
        print("Components:", len(all_components), min_nodes_mode)

        # If the number of elements in components reached the minimum
        # number of nodes
        if len(all_components) >= min_nodes_mode:

            print("Components are ready: "
                  , len(all_components)
                  , min_nodes_mode)
            
            # CONNECTING THE ZONES
            # Get all the points connecting the seeds (inclusive)
            seeds_subnetwork = create_subnetwork(Z, mode, target_nodes=seeds)

            # all_components = component nodes + seeds subnetwork
            all_components.update(seeds_subnetwork)

            # Assign mode to all edges connecting the nodes in "all_components"
            assign_modes(Z, all_components, mode)

            # After assigning autonomous edges, assign modes to nodes
            set_nodes_from_mode(Z)

            break

    return Z

def save_pic(**args):

    G = args["network"]
    if "seeds" in G.graph:
        seeds = list(literal_eval(G.graph["seeds"]))
    else:
        seeds = []
    save_fig = args["save_fig"]
    show_img = not save_fig
    file_name = args["file_name"]
    show_seeds = args["show_seeds"]

    print("len seeds", len(seeds))
    if len(seeds) == 0:
        fig, ax = ox.plot_graph(G, node_color="gray", node_edgecolor="gray", node_size=1, node_zorder=3,
                                edge_color="gray", show=show_img, edge_linewidth=1, edge_alpha=0.3, save=save_fig, file_format="png", filename=file_name, dpi=dpi_img, fig_height=height_img, fig_width=width_img)
        return

    # Save intermediate network
    ec = [mode_colors[data['mode_edge']]["color"] for u,
          v, key, data in G.edges(keys=True, data=True)]

    ew = [mode_colors[data['mode_edge']]["width"] for u,
          v, key, data in G.edges(keys=True, data=True)]

    ns = [30
          if n in seeds and show_seeds
          else mode_colors[G.node[n]["mode_node"]]["nsize"]
          for n in G.nodes()]

    nc = [mode_colors[G.node[n]["mode_node"]]["color"] for n in G.nodes()]

    fig, ax = ox.plot_graph(G, node_color=nc, node_edgecolor=nc, node_size=ns, node_zorder=3,
                            edge_color=ec, show=show_img, edge_linewidth=ew, edge_alpha=0.3, save=save_fig, file_format="png", filename=file_name, dpi=dpi_img, fig_height=height_img, fig_width=width_img)

def get_file_name(region):
    return region.lower().replace(" ", "-").replace(",", "")

def download_network(**args):
    region = args["region"]
    G = get_graph_from_place(region, args["network_type"])
    G.graph["name"] = get_file_name(region)
    print("Graph downloaded:", G.graph['name'])
    network_name = '{0}.graphml'.format(G.graph["name"])
    save_network(G, network_name, root)
    return G

def save_graph_data(G, modes_list=["autonomous","conventional"], path=root, file_name=None):
    """Save distance data in root
    
    Arguments:
        G {networkx} -- Graph with zones/subnetworks
    
    Keyword Arguments:
        modes_list {list} -- Expected modes in graph (default: {["autonomous","conventional"]})
        path {string} -- Path of distance data (default: root)
    """
    # Get distance data
    distance_dic = create_distance_data(G, modes_list)
    if file_name == None:
        file_name = "distances_{0}".format(G.graph["name"])
    
    # Save distances FROM:{TO1:DIS1, TO2:DIS2, TO3:DIS3}
    save_dist_dic(distance_dic, path + "/" + file_name + ".json")
    
    print("Saving graph data ", file_name)
    # Save modified network
    save_network(G, file_name + ".graphml", path)

def gen_od_data(**args):
    print("Creating OD data...")

    n_of_requests = args["n_of_requests"]
    min_dist = args["min_distance"]
    max_dist = args["max_distance"]
    demand_dist_mode = args["demand_dist_mode"]
    network_path = args["network_path"]
    
    # Load network related data
    network = load_network(network_path, folder=".")
    # Load dist data from network
    dist = load_dist_dic(network_path)
    # Get dictionary of nodes per mode
    mode_nodes = dict(literal_eval(network.graph["mode_nodes"]))
    # Final list of requests
    list_of_requests = list()
    # Vary demand distribution, e.g.:
    #{("autonomous", "autonomous"):2,
    # ("autonomous", "conventional"):3,
    # ("conventional", "autonomous"):3,
    # ("conventional", "conventional"):2}}
    for r_from_to in demand_dist_mode.keys():
        
        m_from = r_from_to[0] #e.g.: autonomous
        m_to = r_from_to[1] #e.g.: conventional
        print("REQUEST FROM/TO REGION:", m_from, "-->", m_to)
        

        # Suppose m_from = m_to, therefore a "m_to" vehicle
        # can carry out the transportation
        dist_mode = m_to
        # If modes of OD differ, the transportation can only be carried
        # out by a ### dual ### mode vehicle
        if m_from != m_to:
            dist_mode = "dual"
        
        # How many requests per configuration
        req_per_mode = demand_dist_mode[r_from_to]
        print("req per mode:", req_per_mode)
        for i in range(0, req_per_mode):
            #print("from_to", from_node)
            #print("dist_keys", dist[from_node])

            while True:
                from_node = str(choice(list(mode_nodes[m_from])))

                # Seek a random destination for "from_node" that can
                # be reached using mode "m"
                to_node = str(choice(list(dist[from_node][dist_mode].keys())))

                # Get the distance between OD
                dist_from_to = dist[from_node][dist_mode][to_node]

                # Stop searching if adequate destination is found
                print(from_node, to_node, dist_from_to, min_dist, max_dist)
                if to_node != from_node \
                and dist_from_to >= min_dist \
                and dist_from_to <= max_dist:
                    break

            x_from = network.node[int(from_node)]["x"]
            y_from = network.node[int(from_node)]["y"]
            x_to = network.node[int(to_node)]["x"]
            y_to = network.node[int(to_node)]["y"]

            req = {'pickup_longitude': x_from,
                   'pickup_latitude': y_from,
                   'dropoff_longitude': x_to,
                   'dropoff_latitude': y_to,
                   'trip_distance': dist[from_node][dist_mode][to_node],
                   'pickup_id': from_node,
                   'dropoff_id': to_node}

            print(req)
            list_of_requests.append(req)

    return list_of_requests
    # for i in range inside_cv:

    # for i in range cv_av:

def gen_vehicle_data(**args):
    """
    Receive number of vehicles per zone (A, C, D)
    Distribute the number of vehicles over the zones
      1 - Dual: Scattered over the whole map
      2 - Conventional: Scattered over conventional area
      3 - Autonomous: Equaly divided among disjointed zones
        * Divide number of vehicles per number of seeds
        * Choose origins around the seeds

    Arguments:
        n_of_vehicles -- Number of vehicles origins per mode
        network_path -- File path of network
        distances_path -- File path of the distances between points in network
        scattered [bool] -- Vehicles are scattered or centralized?

    Returns:
        list_of_vehicles -- A list containing vehicles origins dictionaries (lat,long, id and type)
    """

    print("Creating VEHICLES data...")

    def get_n_random_points(n, list_of_points):
        selected = list()
        for i in range(0, n):
            selected.append(str(choice(list(list_of_points))))
        return selected

    def get_n_random_points_around_elements(n, elements, mode):
        """[summary]
        
        Arguments:
            n {[type]} -- [description]
            elements {[type]} -- [description]
            mode {[type]} -- [description]
        
        Returns:
            [type] -- [description]
        """

        selected = list()
        max_per_elem = int(n/len(elements))
        # Rest of division
        remaining = n % len(elements)
        for e in elements:
            to_nodes = list(dist[str(e)][mode].keys())
            print("to_nodes", to_nodes)
            # Equally distribute the remaining nodes
            # (when rest of division is not zero) among the elements
            n = max_per_elem
            if remaining > 0:
                remaining = remaining - 1
                n = n + 1
            selected.extend(get_n_random_points(n, to_nodes))
        return selected

    n_of_vehicles = args["n_of_vehicles"]
    network_path = args["network_path"]
        
    # Load network related data
    network = load_network(filename=network_path, folder=".")
    #dist = create_distance_data(network)
    dist = load_dist_dic(network_path)

    mode_nodes = dict(literal_eval(network.graph["mode_nodes"]))
    origin_nodes = dict()
    for mode in vehicle_modes:

        if mode == "conventional":
            origin_nodes[mode] = get_n_random_points(
                n_of_vehicles, mode_nodes[mode])

        elif mode == "dual":
            origin_nodes[mode] = get_n_random_points(
                n_of_vehicles, network.nodes())

        # Vehicles are equally distributed around AVs generating seeds
        elif mode == "autonomous":
            seeds = list(literal_eval(network.graph["seeds"]))
            origin_nodes[mode] = get_n_random_points_around_elements(
                n_of_vehicles, seeds, mode)

    # Define list of vehicles origins
    list_of_vehicles = list()

    # Create a detailed vehicle origin for each node
    for m, nodes_from_m in origin_nodes.items():
        for n in nodes_from_m:
            x = network.node[int(n)]["x"]
            y = network.node[int(n)]["y"]
            o = {'origin_longitude': x,
                 'origin_latitude': y,
                 'origin_id': n,
                 'type': m}

            print(o)
            list_of_vehicles.append(o)
    return list_of_vehicles

def get_largest_connected_components(G, nodes):
    """Return the largest strongly connected component of graph G.
    Only components containing at least one element in nodes
    are returd

    Arguments:
        G {networkx} -- Graph

    Returns:
        list of sets -- List of strongly connected components containing
                        at least one of the elements in nodes.
    """
    # List of strongly connected components
    final_components = list()

    # Get all strongly components of graph G
    components = [c for c in sorted(
        nx.strongly_connected_components(G), key=len, reverse=True)]
    # For each component
    for c in components:

        # If at least one common element with "nodes" is found
        if len(c.intersection(nodes)) > 0:
            # Component is valid, and can be added to the final list
            final_components.append(c)

    print("Components / Selected components:",
          [len(c) for c in components], "/", [len(c) for c in final_components])
    return final_components

def get_largest_connected_component(G):
    """Return the largest strongly connected component of graph G.

    Arguments:
        G {networkx} -- Graph

    Returns:
        set -- Set of nodes pertaining to the component
    """

    largest_cc = max(nx.strongly_connected_components(G), key=len)
    s_connected_component = [len(c) for c in sorted(
        nx.strongly_connected_components(G), key=len, reverse=True)]
    print("Strongly connected:", s_connected_component)
    return set(largest_cc)

def get_instance_file_name(nw_type,i,graph,p,n_zones=0):
    # File name
    file_name = ""
    if n_zones == 0:
        file_name = "{0}_{1}_S{2:03}_SUB_{3:02}".format(graph,
                            nw_type,
                            int(100*p),
                            i)
    else:
        file_name = "{0}_{1}_S{2:03}_Z{3:02}_{4:02}".format(graph,
                            nw_type,
                            int(100*p),
                            n_zones,
                            i)
    return file_name

def get_subgraph_from_nodes(G, nodes):
    """Return the subgraph of G containing only the nodes
       in "nodes", i.e., G.nodes() - intersection - nodes

    
    Arguments:
        G {networkx} -- Graph
        nodes {set} -- Set of nodes in the subgraph.
    
    Returns:
        networkx -- Graph containing only nodes in "nodes"
    """
    # Get nodes to be discarded
    discarded_nodes = set(G.nodes()).difference(nodes)
    subgraph = deepcopy(G)
    # Remove nodes
    subgraph.remove_nodes_from(discarded_nodes)
    return subgraph

#generate_network_instances()
#G = get_boxed_graph(origin_point,200)
#region = 'Delft, The Netherlands'

# gen_vehicle_data(n_of_vehicles=20)
#region = 'Amsterdam, The Netherlands'
# Downloading network
#G = download_network(region=region, network_type="drive")


# Loading network
# G = load_network("delft_the_netherlands.graphml")
# G = load_network("amsterdam_the_netherlands.graphml")

#save_pic(network=G, save_fig=False, file_name="final_network")
#save_pic(network=strongly_connected_G, save_fig=False, file_name="final_network")
#nodes = create_subnetwork(strongly_connected_G, "autonomous", percentage=0.005)          

# Show loaded network
#save_pic(network=G, save_fig=False, file_name="final_network")

# Create and save zoned network
#Z = create_zoned_network(G, 4, 15, "autonomous")

# Load network
#L = load_network("data/network/delft_the_netherlands_autonomous.graphml")
#L = load_network("data/network/amsterdam_the_netherlands_autonomous.graphml")

# Show picture
#save_pic(network=L, save_fig=False, file_name="final_network")

# Save the distanc
# e data
#gen_distance_data(L, ["conventional", "autonomous"])

#distances = load_dist_dic("data/network/distances_delft_the_netherlands_autonomous.json")

#print("distances", distances)
# Generate OD data
#gen_od_data(network=L, dist=distances, inside_av=3, inside_cv=3, av_cv=2, cv_av=2, n_requests=10)

# pprint.pprint(load_dist_dic(distance_file_name))
#clean_nodes_by_degree(G, 1)


# pprint.pprint(load_dist_dic(distance_file_name))
# for i in [0.005, 0.01, 0.05, 0.10]:
#print("Percentage: ", i)
#create_het_network(G, i)

# G=nx.path_graph(5)

# Get nearest point in map - #https://github.com/gboeing/osmnx/issues/71

# Set edge atribute (conventional, autonomous, etc)
#       https://networkx.github.io/documentation/networkx-1.10/reference/generated/networkx.classes.function.set_edge_attributes.html
#       https://stackoverflow.com/questions/26691442/add-new-attribute-to-an-edge-in-networkx

# Restrict paths nx
#       https://gis.stackexchange.com/questions/16453/how-to-restrict-or-block-certain-paths-in-networkx-graphs

# SHORTEST PATHS
#       https://networkx.github.io/documentation/networkx-1.10/reference/algorithms.shortest_paths.html


"""origin_node = ox.get_nearest_node(G, origin_point)  # Aula
destination_node = ox.get_nearest_node(G, destination_point)
d3_node = ox.get_nearest_node(G, d3)
nx.set_edge_attributes(G, 'conventional', "mode")
route1 = nx.shortest_path(G, origin_node, destination_node)
ox.plot_graph_route(G,
                    route1,
                    origin_point=origin_point,
                    destination_point=destination_point)"""


# plot the street network with folium
#graph_map = ox.plot_graph_folium(G, route)


# save as html file then display map as an iframe
#filepath = 'data/graph.html'
# graph_map.save(filepath)
#IFrame(filepath, width=600, height=500)
