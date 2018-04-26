from config import start_revealing, network_tuples, instance_path_network, instance_path_vehicle, vehicle_tuples, vehicle_modes, vehicle_instances, mode_code
from config import os
import gen.map as mp
from ast import literal_eval
from random import choice

def gen_v_instances_in_network(path_vehicles, network_path):

    print("Creating vehicle instances...",  vehicle_tuples)

    # Heterogeneus and regular vehicles
    compartments = vehicle_instances["COMPARTMENTS DIV."]

    # Set of test cases to be generated
    gen_set = set()
    # Loop all vehicle test cases and store those not yet
    # tested to set gen_set
    for v_k in vehicle_tuples:
        print("Checking", path_vehicles +"/" + v_k +".csv")
        if not os.path.isfile(path_vehicles +"/" + v_k +".csv"):
            test_case = v_k.split("_")
            gen_set.add((int(test_case[0]), test_case[1]))
        else:
            print(path_vehicles +"/" + v_k +".csv already exists.")
    
    # Generate test cases not yet generated
    for v, k in gen_set:

        # Get vehicles' origins
        list_of_vehicles_origins = gen_vehicle_data(n_of_vehicles = v,
                                                    network_path = network_path)
        labels = list()
        values = list()

        print("compartment:", compartments)
        for c in compartments[k]:
            labels.append(c["label_comp"])
            values.append(c["number_comp"])

        name_instance = "{0:02}_{1}.csv".format(v, k)

        csv_label = "Model,Type,Available_at,Latitude,Longitude,Origin_id,Autonomy," + \
            ",".join(labels)+"\n"

        with open(path_vehicles +"/"+ name_instance, 'w') as file:
            file.write(csv_label)

        for e in list_of_vehicles_origins:

            str_id = k + "_" + mode_code[e["type"]]

            #print("Generating vehicles:", str_id)

            loads_v = ",".join([str(v) for v in values])

            csv_response = "{0},{1},{2},{3:.6f},{4:.6f},{5},{6},{7}\n".format(str_id, e["type"], start_revealing, float(
                e["origin_longitude"]), float(e["origin_latitude"]), e['origin_id'], 8, loads_v )
            #print(csv_response)

            with open(path_vehicles +"/"+ name_instance, 'a') as file:
                file.write(csv_response)

def genVehicles(instance_path):
    print("Creating vehicle instances...")

    n_vehicles = DaoHybrid.v_info["#VEHICLES"]
    # Heterogeneus and regular vehicles
    fleet_composition = DaoHybrid.v_info["FLEET COMPOSITION"]
    compartments = DaoHybrid.v_info["COMPARTMENTS DIV."]

    min_distance = 0
    max_distance = 1

    # extraction_interval = ('2015-02-14 17:00:00', '2015-02-14 17:59:59')
    extraction_interval = ('2015-02-14 12:00:00', '2015-02-14 12:59:59')

    # 2017-09-13 19:49,4.881191,52.370715,4.870891,52.369457,A=2,180,600

    for v in n_vehicles:  # 6
        max_amount = v
        list_of_requests = GenTestCase.extract_data_nyc(source,
                                                        extraction_interval,
                                                        min_distance,
                                                        max_distance,
                                                        max_amount)

        for fc in fleet_composition:  # 7
            for a, b in [(a, b) for (a, b) in compartments.keys() if a == fc]:  # 8
                comp = compartments[(a, b)]
                labelHuman = []
                labelFreight = []
                valueHuman = []
                valueFreight = []

                for c in comp:
                    if isinstance(c, CompartmentHuman):
                        labelHuman.append(c.label)
                        valueHuman.append(str(c.amount))
                    else:
                        labelFreight.append(c.label)
                        valueFreight.append(str(c.amount))

                name_instance = "{0:02}_{1}_{2}.csv".format(v, a, b)

                csv_label = "Model,Available_at,Latitude,Longitude,Autonomy," + \
                    ",".join(labelHuman+labelFreight)+"\n"

                with open(instance_path + name_instance, 'w') as file:
                    file.write(csv_label)

                for i, e in enumerate(list_of_requests):

                    str_amount = ""
                    str_id = ""
                    if fc is "HET":
                        str_id = "1"
                        str_amount = ",".join(valueHuman+valueFreight)

                    elif fc is "REG":
                        str_id = "2"
                        if i >= v/2:
                            str_amount = ",".join(
                                (["0"]*len(valueHuman))+valueFreight)
                        else:
                            str_amount = ",".join(
                                valueHuman+(["0"]*len(valueFreight)))

                    csv_response = "{0},{1},{2:.6f},{3:.6f},{4},{5}\n".format(str_id, DaoHybrid.start_revealing, float(
                        e["pickup_longitude"]), float(e["pickup_latitude"]), 8, str_amount)
                    print(csv_response)

                    with open(instance_path + name_instance, 'a') as file:
                        file.write(csv_response)

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
        selected = list()
        max_per_elem = int(n/len(elements))
        # Rest of division
        remaining = n % len(elements)
        for e in elements:
            to_nodes = list(dist[str(e)][mode].keys())
            # print("to_nodes", to_nodes)
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
    network = mp.load_network(filename=network_path, folder=".")
    #dist = create_distance_data(network)
    dist = mp.load_dist_dic(network_path)
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

def gen_all():

    for nw in network_tuples:
        
        network_path = instance_path_network + "/" + nw

        print("   Generating vehicles for network {0}...".format(nw + ".graphml"))
        # Store vehicle data for network nw
        folder_v_nw = instance_path_vehicle+ "/" + nw
        if not os.path.exists(folder_v_nw):
            os.makedirs(folder_v_nw)

        gen_v_instances_in_network(path_vehicles = folder_v_nw,
                                network_path = network_path)