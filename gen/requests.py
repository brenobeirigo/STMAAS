from config import req_horizon, start_revealing, request_tuples, req_demand_dist_mode, req_demand_limit, req_interval, req_n_requests, req_sl_share, req_trips_distance
from config import os
from gen.map import load_dist_dic, load_network, literal_eval, choice
from datetime import datetime, timedelta
import random
import numpy as np
from model.Compartment import CompartmentHuman


def getRandomCompartments(list_of_compartments):
    number = random.randint(1, len(list_of_compartments))
    selected = []
    while(len(selected) is not number):
        el = random.choice(list_of_compartments)
        if(el not in selected):
            selected.append(el)
    return selected


def genRequests(instance_path):

    print("Extracting data from NY...")
    n_requests = DaoHybrid.r_info["#REQUESTS"]
    request_comp_pf = DaoHybrid.r_info["H_F_SHARE"]
    parcel_spatial_distribution = DaoHybrid.r_info["SPATIAL_DIST"]
    interval_between_requests = DaoHybrid.r_info["INTERVAL"]
    trips_distance = DaoHybrid.r_info["TRIPS_DIST"]
    occupancy_levels = DaoHybrid.r_info["OCCUPANCY_LEVELS"]
    demand_limit = DaoHybrid.r_info["DEMAND_LIMIT"]
    nature_requests = DaoHybrid.r_info["NATURE"]

    pk_delay_p = 180
    dl_delay_p = 600
    pk_delay_f = 3600
    dl_delay_f = 18000

    # extraction_interval = ('2015-02-14 18:00:00', '2015-02-14 18:59:59')
    extraction_interval = ('2015-02-14 13:00:00', '2015-02-14 13:59:59')

    for td in trips_distance.keys():  # 4
        for r in n_requests:  # 0 OK --- 32
            max_distance = trips_distance[td][1]
            min_distance = trips_distance[td][0]
            max_amount = r
            list_of_requests = GenTestCase.extract_data_nyc(GenTestCase.source,
                                                            extraction_interval,
                                                            min_distance,
                                                            max_distance,
                                                            max_amount)

            for ibr in interval_between_requests.keys():  # 3
                min_interval = interval_between_requests[ibr][0]
                max_interval = interval_between_requests[ibr][1]

                start_date = datetime.strptime(
                    DaoHybrid.start_revealing, '%Y-%m-%d %H:%M:%S')

                # pprint.pprint(list_of_requests)
                for j in nature_requests:  # JOINT OR DISJOINT
                    for rc in request_comp_pf.keys():  # 1 OK --- 3_1_4
                        for sd in parcel_spatial_distribution:  # 2 OK
                            for ol in occupancy_levels.keys():  # 5 OK --- HIGH(>half)
                                for k, comp in [(k, demand_limit[k]) for k in demand_limit.keys()]:
                                    # instance_name = "nReq({0:02})_composition({1})_spatialDis({2})_interval({3})_distance({4})_occupancy({5})_demand_limit({6}).csv".format(
                                    instance_name = "{0:02}_{1}_{2}_{3}_{4}_{5}_{6}_{7}.csv".format(
                                        r, rc, sd, ibr, td, ol, k, j)

                                    print("wtf", instance_name)
                                    offset_cumulative = timedelta(
                                        seconds=0)

                                    csv_label = "revealing,pickup_x,pickup_y,dropoff_x,dropoff_y,order,pickup_lateness,delivery_lateness,id\n"

                                    with open(instance_path + instance_name, 'w') as file:
                                        file.write(csv_label)

                                    for i, e in enumerate(list_of_requests):

                                        # Set rand interval
                                        rand_offset = random.randint(
                                            min_interval, max_interval)
                                        offset = timedelta(
                                            seconds=rand_offset)
                                        offset_cumulative += offset
                                        revealing_time = start_date + offset_cumulative

                                        # Final list of compartments in request
                                        comp_chosen = []

                                        if j is "JOINT":
                                            comp_chosen = GenTestCase.getRandomCompartments(
                                                comp["H"])+GenTestCase.getRandomCompartments(comp["F"])
                                            # Joint requests have people maximum delays
                                            pk_delay = pk_delay_p
                                            dl_delay = dl_delay_p

                                        elif j is "DISJOINT":
                                            type_commodity = "H"
                                            pk_delay = pk_delay_p
                                            dl_delay = dl_delay_p
                                            comp_chosen = GenTestCase.getRandomCompartments(
                                                comp["H"])

                                            if i+1 > request_comp_pf[rc][0] * r:
                                                type_commodity = "F"
                                                pk_delay = pk_delay_f
                                                dl_delay = dl_delay_f
                                                comp_chosen = GenTestCase.getRandomCompartments(
                                                    comp["F"])

                                        e["demand"] = "/".join(str(c.get_random_copy(
                                            occupancy_levels[ol][0], occupancy_levels[ol][1])) for c in comp_chosen)
                                        csv_data = "{0},{1:.6f},{2:.6f},{3:.6f},{4:.6f},{5},{6},{7}".format(
                                            revealing_time.strftime(
                                                '%Y-%m-%d %H:%M'),
                                            float(e["pickup_longitude"]),
                                            float(e["pickup_latitude"]),
                                            float(e["dropoff_longitude"]),
                                            float(e["dropoff_latitude"]),
                                            e["demand"],
                                            pk_delay,
                                            dl_delay)

                                        with open(instance_path
                                                    + instance_name, 'a') as file:
                                            file.write(csv_data+"\n")

                                        print(csv_data)
                                    # print(csv_response)

def genRequests2(path_requests, network_path):
    print("Generating dual-mode demand...")

    # Set of test cases to be generated
    gen_set = set()
    # Loop all vehicle test cases and store those not yet
    # tested to set gen_set
    # Example of request name: 10_D1_S1_05-10min-0.5km-1km_A5
    for req_name in request_tuples:
        req_path =  path_requests +"/" + req_name +".csv"
        print("Checking request ", req_path)
        if not os.path.isfile(req_path):
            test_case = req_name.split("_")
            gen_set.add((int(test_case[0]),
                                test_case[1],
                                test_case[2],
                                test_case[3],
                                test_case[4],
                                test_case[5]))
        else:
            print("Request", req_path, "already exists.")

    
    # Generate test cases not yet generated
    # nr     = Vary number of requests, e.g.: 8
    # td     = Vary trip distances, e.g.: "0.5km-1km": (500, 1000)
    # d_mode = Vary demand distribution (from->to), e.g.:
                # {"D1":{("autonomous", "autonomous"):2,
                #        ("autonomous", "conventional"):3,
                #        ("conventional", "autonomous"):3,
                #        ("conventional", "conventional"):2}},
    # ibr    = Vary interval between requests, e.g.:{"05-10min": (300, 600)}
    # k      = Vary compartments of vehicles {("A5"): {"H": [CompartmentHuman("A", 5)]}}
    # sl     = Vary service levels
    for nr, d_mode, sl, hor, td, k in gen_set:
        
        # Set max traveled distances
        max_distance = req_trips_distance[td][1]
        min_distance = req_trips_distance[td][0]    

        # Set demand distribution (A->A, A->C, etc.)
        distr = req_demand_dist_mode[d_mode]
        
        # Generate requests coordinates
        list_of_requests = gen_od_data(
                            min_distance = min_distance,
                            max_distance = max_distance,
                            n_of_requests = nr,
                            demand_dist_mode = distr,
                            network_path = network_path)

        print ("len:", len(list_of_requests))
        
        # Set intervals
        t_horizon = req_horizon[hor]
        print("T horizon:", t_horizon)
        
        # Format start date
        start_date = datetime.strptime(start_revealing,
                                        '%Y-%m-%d %H:%M')
        
        # Set compartments
        #{"S1":{"C":{"request_share":0.2, "overall_sl":0.7,"pk_delay":1600, "trip_delay":1600},
            #       "B":{"request_share":0.6, "overall_sl":0.8,"pk_delay":1300, "trip_delay":1300},
            #       "A":{"request_share":0.2, "overall_sl":0.9,"pk_delay":1180, "trip_delay":1180}}}})
        comp = req_demand_limit[k]
                            
        # Set instance name
        instance_name = "{0:02}_{1}_{2}_{3}_{4}_{5}.csv".format(
            nr, d_mode, sl, hor, td, k)


        sl_request_list = list()
        #{"C":{"request_share":2, "overall_sl":0.7,"pk_delay":1600, "trip_delay":1600},
        # "B":{"request_share":6, "overall_sl":0.8,"pk_delay":1300, "trip_delay":1300},
        # "A":{"request_share":2, "overall_sl":0.9,"pk_delay":1180, "trip_delay":1180}}}})
        for sl_label in req_sl_share[sl].keys():
            print("Service level:", sl_label)
            pk_delay = req_sl_share[sl][sl_label]["pk_delay"]
            trip_delay = req_sl_share[sl][sl_label]["trip_delay"]
            request_share = int(req_sl_share[sl][sl_label]["request_share"]*nr)
            label_list = [(sl_label,pk_delay,trip_delay)] * request_share
            sl_request_list.extend(label_list)
        
        #print("sl label:", sl_request_list)

        print("Instance name:", instance_name)
        
        # Create label
        csv_label = "revealing,pickup_x,pickup_y,dropoff_x,dropoff_y,order,pickup_lateness,delivery_lateness,pk_node_id,dl_node_id,sl_class,id\n"

        # Write label to file
        with open(path_requests +"/"+ instance_name, 'w') as file:
            file.write(csv_label)

        rand_offset = np.random.uniform(0, t_horizon, len(list_of_requests))

        for i, e in enumerate(list_of_requests):
            
            # Set rand interval
            offset = timedelta(seconds=int(rand_offset[i]))
            revealing_time = start_date + offset

            # Final list of compartments in request (as dictionaries)
            comp_chosen = getRandomCompartments(comp["H"])
            
            # List of compartments (as Compartment objects)
            comp_list = [CompartmentHuman(c["label_comp"], c["number_comp"]) for c in comp_chosen]

            # Generate random demand for each compartment (>=1)
            e["demand"] = "/".join(str(c.get_random_copy()) for c in comp_list)
            
            # Assemble request line
            csv_data = "{0},{1:.6f},{2:.6f},{3:.6f},{4:.6f},{5},{6},{7},{8},{9},{10},".format(
                revealing_time.strftime('%Y-%m-%d %H:%M:%S'),
                float(e["pickup_longitude"]),
                float(e["pickup_latitude"]),
                float(e["dropoff_longitude"]),
                float(e["dropoff_latitude"]),
                e["demand"],
                sl_request_list[i][1],
                sl_request_list[i][2],
                e["pickup_id"],
                e["dropoff_id"],
                sl_request_list[i][0])

            # Write request    
            with open(path_requests +"/"+
                        instance_name, 'a') as file:
                file.write(csv_data+"\n")

            print(csv_data)

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
    for r_from_to in demand_dist_mode:
        #e.g.: autonomous
        m_from = r_from_to["from"]
        #e.g.: conventional
        m_to = r_from_to["to"]
        # How many requests per configuration
        from_to_share = r_from_to["share"]
        
        # print("REQUEST FROM/TO REGION:", m_from, "-->", m_to, percentage_req_per_mode)

        # Suppose m_from = m_to, therefore a "m_to" vehicle
        # can carry out the transportation
        dist_mode = m_to
        
        # If modes of OD differ, the transportation can only be carried
        # out by a ### dual ### mode vehicle
        if m_from != m_to:
            dist_mode = "dual"
        
        # Total number of requests from region m_from to region m_to 
        n_req_mode = int(from_to_share * n_of_requests)


        print("req per mode:", n_req_mode)
        for i in range(0, n_req_mode):
            #print("from_to", from_node)
            #print("dist_keys", dist[from_node])

            while True:
                # Find random departure
                from_node = str(choice(list(mode_nodes[m_from])))

                # Seek a random destination for "from_node" that can
                # be reached using mode "m"
                to_node = str(choice(list(dist[from_node][dist_mode].keys())))

                # Get the distance between OD
                dist_from_to = dist[from_node][dist_mode][to_node]

                # Stop searching if adequate destination is found
                if to_node != from_node \
                and dist_from_to >= min_dist \
                and dist_from_to <= max_dist:
                    print(from_node, to_node, dist_from_to, min_dist, max_dist)
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
