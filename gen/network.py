from config import network_tuples,network_instances
from gen.map import *


def get_network_tuples_not_tested():
        # Set of test cases to be generated
    gen_set = set()
    # Loop all vehicle test cases and store those not yet
    # tested to set gen_set
    # Example of request name: delft-the-netherlands_subnetworks_S010_SUB_02
    for nw_name in network_tuples:
        nw_path = instance_path_network + nw_name + ".json"
        if not os.path.isfile(nw_path):
            test_case = nw_name.split("_")
            reg = test_case[0]
            sub = test_case[1]
            spr = int(test_case[2][1:]) / 100
            zon = test_case[3]
            zon = (int(zon[1:]) if zon[0] == "Z" else 0)
            t = int(test_case[4])
            gen_set.add((reg, sub, spr, zon, t))
        else:
            print("Request", nw_name, "already exists.")
    return gen_set


def generate_network_instances():
    
    save_fig = network_instances["SAVE_FIG"]
    show_seeds = network_instances["SHOW_SEEDS"]
    
    print("Generating network instances...")
    not_tested = get_network_tuples_not_tested()
    # For all networks not yet tested
    for reg, sub, spr, zon, t in not_tested:
        print("GENERATING: ", reg, sub, spr, zon, t)

        file_name = get_file_name(reg)
        #G = download_network(region=region, network_type="drive")
        # Loading network
        # G = load_network("delft_the_netherlands.graphml")
        G = None
        network_name = '{0}.graphml'.format(file_name)

        # If regions was already downloaded
        if os.path.exists(root + network_name):
            print("Loading network '", network_name, "'...")
            G = load_network(filename=network_name, folder=root)
        else:
            print("Downloading network '", network_name, "'...")
            G = download_network(region=reg, network_type="drive")
            print("Graph downloaded:", G.graph["name"])

        # Get largest connected component from graph G
        largest_cc = get_largest_connected_component(G)

        print("Largest component:", len(largest_cc), "/", len(G.nodes()))

        # Get subgraph from G containing only the nodes in largest connected components
        strongly_connected_G = get_subgraph_from_nodes(G, largest_cc)

        # Create zone
        if sub == "zones":

            # Get zone
            Z = get_zoned_network(strongly_connected_G,
                                  mode="autonomous",
                                  n_zones=zon,
                                  percentage=spr)

            # File name
            file_name = get_instance_file_name(
                sub, t, Z.graph["name"], spr, zon)

            # Save img for final zone
            save_pic(network=Z,
                     save_fig=save_fig,
                     show_seeds=show_seeds,
                     file_name=file_name)

            # Save zone
            save_graph_data(
                Z, file_name=file_name, path=instance_path_network)

        # Create subnetwork
        elif sub == "subnetworks":
            Z = create_subnetwork(strongly_connected_G,
                                  mode="autonomous",
                                  percentage=spr)
            # File name
            file_name = get_instance_file_name(
                sub, t, Z.graph["name"], spr)

            # Save img for final zone
            save_pic(network=Z,
                     save_fig=save_fig,
                     show_seeds=show_seeds,
                     file_name=file_name)

            # Save subnetwork
            save_graph_data(Z, file_name=file_name,
                            path=instance_path_network)

