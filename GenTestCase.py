from DaoHybrid import *
from datetime import datetime, date, time, timedelta
from Compartment import *
import math
import random
import os
from collections import OrderedDict
from Network import *


class GenTestCase:
    # Earliest time possible
    start_revealing = '2017-10-10 00:00'
    start_revealing_t = datetime.strptime('2017-10-10 00:00:00', '%Y-%m-%d %H:%M:%S')
    start_revealing_tstamp = start_revealing_t.timestamp()

    code_mode = {"A":"autonomous", "C":"conventional", "D":"dual"}
    mode_code = {"autonomous":"A", "conventional":"C", "dual":"D"}

    network_instances = OrderedDict({
                        "REGION": ['Delft, The Netherlands'],
                        "SUBNETWORK_TYPES": ["zones", "subnetworks"],
                        "SPREAD": [0.1, 0.25, 0.50],
                        "#ZONES": [1,2,4,8],
                        "#TEST": 10,
                        "SAVE_FIG": True,
                        "SHOW_SEEDS": True
                        }) #, 'Amsterdam, The Netherlands'] #["New York, United States"] 0.1, 0.25, 0.50, 

    r_info_dual_mode = OrderedDict({
                          
                          "#REQUESTS": [20],

                          "DEMAND_DIST_MODE": {"D1":{("autonomous", "autonomous"):0.2,
                                                     ("autonomous", "conventional"):0.3,
                                                     ("conventional", "autonomous"):0.3,
                                                     ("conventional", "conventional"):0.2}},
                           
                          "SL_SHARE": {"S1":{"C":{"request_share":0.2, "overall_sl":0.7,"pk_delay":300, "trip_delay":600},
                                             "B":{"request_share":0.6, "overall_sl":0.8,"pk_delay":180, "trip_delay":300},
                                             "A":{"request_share":0.2, "overall_sl":0.9,"pk_delay":120, "trip_delay":0}}},

                          "INTERVAL": {"05-10min": (300, 600)},
                          
                          "TRIPS_DIST": {"0.1km-10km": (100, 10000)},
                          
                          "DEMAND_LIMIT": {("A5"): {"H": [CompartmentHuman("A", 5)]}}})
                                                       
    v_info_dual = OrderedDict({"#VEHICLES": [20],
                               "COMPARTMENTS DIV.": {"A5": [CompartmentHuman("A", 5)]},
                               "MODE_INFO":{"autonomous":{"fixed_cost":20000, "var_cost":0.001},
                                              "dual":{"fixed_cost":15000, "var_cost":0.002},
                                      "conventional":{"fixed_cost":10000, "var_cost":0.001}}})
                               
    vehicle_tuples = None
    request_tuples = None
    network_tuples = None


    @classmethod
    def gen_network_tuples(cls):
        #Vary the vehicles attributes
        # v ------- e.g. [10, 20, 30] (number of vehicles)
        # c ------- e.g. [A4, A2, A1] (4 adult places, 2 adult places)
        cls.network_tuples = set([
        get_instance_file_name(st, i, get_file_name(r), p, nz)
        if st == "zones" else
        get_instance_file_name(st, i, get_file_name(r), p)    
        for r in cls.network_instances["REGION"]
        for p in cls.network_instances["SPREAD"]
        for st in cls.network_instances["SUBNETWORK_TYPES"]
        for i in range(1, cls.network_instances["#TEST"]+1)
        for nz in cls.network_instances["#ZONES"]])
        
    @classmethod
    def gen_vehicles_tuples(cls):

        #Vary the vehicles attributes
        # v ------- e.g. [10, 20, 30] (number of vehicles)
        # c ------- e.g. [A4, A2, A1] (4 adult places, 2 adult places)
        cls.vehicle_tuples = ["{0:02}_{1}".format(v, c)
        for v in cls.v_info_dual["#VEHICLES"]
        for c in cls.v_info_dual["COMPARTMENTS DIV."]]

    @classmethod
    def gen_requests_tuples(cls):        
        
        # Vary the requests attributes
        # r -------- e.g. [30, 40, 50] (number of requests)
        # td ------- e.g. ["0.5km-1km", "5km-10km"] (min-max distance between OD points)
        # sl ------- e.g. ["S1, S2"] (S1 defines Service levels (delays, etc.) for customer classes A,B and C)
        # ibr ------ e.g. ["05-10min", "01-05min"] (rate at which requests are revealed)
        # d_mode --- e.g. ["D1", "D2"] (What is the demand share going from A to A, A to C, C to A and C to C)
        # dl ------- e.g. ["A5"] (customers request from 1 to 5 adult compartments)
        cls.request_tuples = ["{0:02}_{1}_{2}_{3}_{4}_{5}".format(r, d_mode, sl, ibr, td, dl)
        for r in cls.r_info_dual_mode["#REQUESTS"] 
        for td in cls.r_info_dual_mode["TRIPS_DIST"]
        for sl in cls.r_info_dual_mode["SL_SHARE"]
        for ibr in cls.r_info_dual_mode["INTERVAL"]
        for d_mode in cls.r_info_dual_mode["DEMAND_DIST_MODE"]
        for dl in cls.r_info_dual_mode["DEMAND_LIMIT"]]

    source = 'E:/yellow_tripdata_2015-02.csv'

    """
    ### ALL HEADERS FROM NYC ##############################
        headers_requests = ['VendorID',
                        'tpep_pickup_datetime',
                        'tpep_dropoff_datetime',
                        'passenger_count',
                        'trip_distance',
                        'pickup_longitude',
                        'pickup_latitude',
                        'RatecodeID',
                        'store_and_fwd_flag',
                        'dropoff_longitude',
                        'dropoff_latitude',
                        'payment_type',
                        'fare_amount',
                        'extra',
                        'mta_tax',
                        'tip_amount',
                        'tolls_amount',
                        'improvement_surcharge',
                        'total_amount']
    #######################################################
    """

    headers_requests = ['tpep_pickup_datetime',
                        'pickup_longitude',
                        'pickup_latitude',
                        'dropoff_longitude',
                        'dropoff_latitude',
                        'passenger_count',
                        'trip_distance']

    headers_vehicles = ['pickup_longitude',
                        'pickup_latitude']

    @staticmethod
    def getRandomCompartments(list_of_compartments):
        amount = randint(1, len(list_of_compartments))
        selected = []
        while(len(selected) is not amount):
            el = random.choice(list_of_compartments)
            if(el not in selected):
                selected.append(el)
        return selected


    @staticmethod
    def genVehicles2(path_vehicles, network_path):

        print("Creating vehicle instances...",  GenTestCase.vehicle_tuples
        )
            
        n_vehicles = GenTestCase.v_info_dual["#VEHICLES"]
        compartments = GenTestCase.v_info_dual["COMPARTMENTS DIV."]

        min_distance = 0
        max_distance = 100000

        # Set of test cases to be generated
        gen_set = set()
        # Loop all vehicle test cases and store those not yet
        # tested to set gen_set
        for v_k in GenTestCase.vehicle_tuples:
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

            for c in compartments[k]:
                labels.append(c.get_label())
                values.append(c.get_amount())

            name_instance = "{0:02}_{1}.csv".format(v, k)

            csv_label = "Model,Type,Available_at,Latitude,Longitude,Origin_id,Autonomy," + \
                ",".join(labels)+"\n"

            with open(path_vehicles +"/"+ name_instance, 'w') as file:
                file.write(csv_label)

            for e in list_of_vehicles_origins:

                str_id = k + "_" + GenTestCase.mode_code[e["type"]]

                #print("Generating vehicles:", str_id)

                loads_v = ",".join([str(v) for v in values])

                csv_response = "{0},{1},{2},{3:.6f},{4:.6f},{5},{6},{7}\n".format(str_id, e["type"], GenTestCase.start_revealing, float(
                    e["origin_longitude"]), float(e["origin_latitude"]), e['origin_id'], 8, loads_v )
                #print(csv_response)

                with open(path_vehicles +"/"+ name_instance, 'a') as file:
                    file.write(csv_response)

    @staticmethod
    def genVehicles(instance_path):
        print("Creating vehicle instances...")

        n_vehicles = GenTestCase.v_info["#VEHICLES"]
        # Heterogeneus and regular vehicles
        fleet_composition = GenTestCase.v_info["FLEET COMPOSITION"]
        compartments = GenTestCase.v_info["COMPARTMENTS DIV."]

        min_distance = 0
        max_distance = 1

        # extraction_interval = ('2015-02-14 17:00:00', '2015-02-14 17:59:59')
        extraction_interval = ('2015-02-14 12:00:00', '2015-02-14 12:59:59')

        # 2017-09-13 19:49,4.881191,52.370715,4.870891,52.369457,A=2,180,600

        for v in n_vehicles:  # 6
            max_amount = v
            list_of_requests = GenTestCase.extract_data_nyc(GenTestCase.source,
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
                            labelHuman.append(c.get_label())
                            valueHuman.append(str(c.get_amount()))
                        else:
                            labelFreight.append(c.get_label())
                            valueFreight.append(str(c.get_amount()))

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

                        csv_response = "{0},{1},{2:.6f},{3:.6f},{4},{5}\n".format(str_id, GenTestCase.start_revealing, float(
                            e["pickup_longitude"]), float(e["pickup_latitude"]), 8, str_amount)
                        print(csv_response)

                        with open(instance_path + name_instance, 'a') as file:
                            file.write(csv_response)

    @staticmethod
    def genRequests(instance_path):

        print("Extracting data from NY...")
        n_requests = GenTestCase.r_info["#REQUESTS"]
        request_comp_pf = GenTestCase.r_info["H_F_SHARE"]
        parcel_spatial_distribution = GenTestCase.r_info["SPATIAL_DIST"]
        interval_between_requests = GenTestCase.r_info["INTERVAL"]
        trips_distance = GenTestCase.r_info["TRIPS_DIST"]
        occupancy_levels = GenTestCase.r_info["OCCUPANCY_LEVELS"]
        demand_limit = GenTestCase.r_info["DEMAND_LIMIT"]
        nature_requests = GenTestCase.r_info["NATURE"]

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
                        GenTestCase.start_revealing, '%Y-%m-%d %H:%M:%S')

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
                                            rand_offset = randint(
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

    @staticmethod
    def genRequests2(path_requests, network_path):
        print("Generating dual-mode demand...")
        n_requests = GenTestCase.r_info_dual_mode["#REQUESTS"]
        interval_between_requests = GenTestCase.r_info_dual_mode["INTERVAL"]
        trips_distance = GenTestCase.r_info_dual_mode["TRIPS_DIST"]
        demand_limit = GenTestCase.r_info_dual_mode["DEMAND_LIMIT"]
        demand_dist_mode = GenTestCase.r_info_dual_mode["DEMAND_DIST_MODE"]
        service_level_share = GenTestCase.r_info_dual_mode["SL_SHARE"]

        # Set of test cases to be generated
        gen_set = set()
        # Loop all vehicle test cases and store those not yet
        # tested to set gen_set
        # Example of request name: 10_D1_S1_05-10min-0.5km-1km_A5
        for req_name in GenTestCase.request_tuples:
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
        for nr, d_mode, sl, ibr, td, k in gen_set:
            
            # Set max traveled distances
            max_distance = trips_distance[td][1]
            min_distance = trips_distance[td][0]    
            
            # Set demand distribution (A->A, A->C, etc.)
            distr = demand_dist_mode[d_mode]
            
            # Generate requests coordinates
            list_of_requests = gen_od_data(
                                min_distance = min_distance,
                                max_distance = max_distance,
                                n_of_requests = nr,
                                demand_dist_mode = distr,
                                network_path = network_path)

            print ("len:", len(list_of_requests))
            
            # Set intervals
            min_interval = interval_between_requests[ibr][0]
            max_interval = interval_between_requests[ibr][1]
            
            # Format start date
            start_date = datetime.strptime(GenTestCase.start_revealing,
                                            '%Y-%m-%d %H:%M')
            
            # Set compartments
            #{"S1":{"C":{"request_share":0.2, "overall_sl":0.7,"pk_delay":1600, "trip_delay":1600},
                #       "B":{"request_share":0.6, "overall_sl":0.8,"pk_delay":1300, "trip_delay":1300},
                #       "A":{"request_share":0.2, "overall_sl":0.9,"pk_delay":1180, "trip_delay":1180}}}})
            comp = demand_limit[k]
                                
            # Set instance name
            instance_name = "{0:02}_{1}_{2}_{3}_{4}_{5}.csv".format(
                nr, d_mode, sl, ibr, td, k)


            sl_request_list = list()
            #{"C":{"request_share":2, "overall_sl":0.7,"pk_delay":1600, "trip_delay":1600},
            # "B":{"request_share":6, "overall_sl":0.8,"pk_delay":1300, "trip_delay":1300},
            # "A":{"request_share":2, "overall_sl":0.9,"pk_delay":1180, "trip_delay":1180}}}})
            for sl_label in service_level_share[sl].keys():
                print("Service level:", sl_label)
                pk_delay = service_level_share[sl][sl_label]["pk_delay"]
                trip_delay = service_level_share[sl][sl_label]["trip_delay"]
                request_share = int(service_level_share[sl][sl_label]["request_share"]*nr)
                label_list = [(sl_label,pk_delay,trip_delay)] * request_share
                sl_request_list.extend(label_list)
            
            #print("sl label:", sl_request_list)

            print("Instance name:", instance_name)
            offset_cumulative = timedelta(seconds=0)
            
            # Create label
            csv_label = "revealing,pickup_x,pickup_y,dropoff_x,dropoff_y,order,pickup_lateness,delivery_lateness,pk_node_id,dl_node_id,sl_class,id\n"

            # Write label to file
            with open(path_requests +"/"+ instance_name, 'w') as file:
                file.write(csv_label)


            for i, e in enumerate(list_of_requests):

                # Set rand interval
                rand_offset = randint(min_interval, max_interval)
                offset = timedelta(seconds=rand_offset)
                offset_cumulative += offset
                revealing_time = start_date + offset_cumulative

                # Final list of compartments in request
                comp_chosen = GenTestCase.getRandomCompartments(comp["H"])

                e["demand"] = "/".join(str(c.get_random_copy()) for c in comp_chosen)
                csv_data = "{0},{1:.6f},{2:.6f},{3:.6f},{4:.6f},{5},{6},{7},{8},{9},{10},".format(
                    revealing_time.strftime('%Y-%m-%d %H:%M'),
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
                    
                with open(path_requests +"/"+
                            instance_name, 'a') as file:
                    file.write(csv_data+"\n")

                print(csv_data)

    @staticmethod
    def genAllTestCases(instance_path_vehicle,
                        instance_path_request,
                        instance_path_network):
        print("Starting test case generation...")
    
        print("   Generating networks...")

        print(GenTestCase.get_network_tuples_not_tested(instance_path_network))

        #GenTestCase.generate_network_instances(instance_path_network)
        GenTestCase.gen_network_tuples()
        
        for nw in GenTestCase.network_tuples:
            
            network_path = instance_path_network + "/" + nw
            
            print("   Generating requests for network {0}...".format(nw + ".graphml"))
            # Store request data for network nw
            folder_r_nw = instance_path_request + "/" + nw
            if not os.path.exists(folder_r_nw):
                os.makedirs(folder_r_nw)

            GenTestCase.genRequests2(path_requests = folder_r_nw,
                                    network_path = network_path)

            print("   Generating vehicles for network {0}...".format(nw + ".graphml"))
            # Store vehicle data for network nw
            folder_v_nw = instance_path_vehicle+ "/" + nw
            if not os.path.exists(folder_v_nw):
                os.makedirs(folder_v_nw)

            GenTestCase.genVehicles2(path_vehicles = folder_v_nw,
                                    network_path = network_path)
    #def __init__(self):
        #GenTestCase.genRequests2("data/")
        #GenTestCase.genVehicles2("data/")
        #print("ibr", ibr, "i", i, type_commodity, e)
    """
    extraction_intervals = [('2015-02-14 18:00:00', '2015-02-14 18:59:59')]

        print("Extracting data from NY...")
        source = 'E:/yellow_tripdata_2015-02.csv'

        for ibr in interval_between_requests.keys():  # 3
            for td in trips_distance.keys():  # 4
                for r in n_requests:  # 0 OK --- 32
                    max_distance = trips_distance[td][1]
                    min_distance = trips_distance[td][0]
                    max_amount = r
                    list_of_requests = self.extract_data_nyc(source,
                                          extraction_intervals,
                                          headers_requests,
                                          min_distance,
                                          max_distance,
                                          max_amount,
                                          interval_between_requests[ibr][0],
                                          interval_between_requests[ibr][1],
                                          GenTestCase.start_revealing)
                    
                    # pprint.pprint(list_of_requests)

                    for rc in request_comp_pf.keys():  # 1 OK --- 3_1_4
                        for sd in parcel_spatial_distribution:  # 2 OK
                            for ol in occupancy_levels.keys():  # 5 OK --- HIGH(>half)
                                
                                instance_name = "nReq({0:02})_composition({1})_spatialDis({2})_interval({3})_distance({4})_occupancy({5}).csv".format(r, rc, sd, ibr, td, ol)
                                                                    
                                for fc in fleet_composition:  # 7 OK --- HET
                                    # print("compart", compartments.keys())
                                    # 8 OK --- {'H': [A=5], 'F': [XL=5, L=10]}
                                    
                                        
                                    for comp in [compartments[k] for k in compartments.keys() if k[0] == fc]:
                                        
                                        wtf = "nReq({0:02})_composition({1})_spatialDis({2})_interval({3})_distance({4})_occupancy({5})_fleetComp({6})_compartments({7}).csv".format(r, rc, sd, ibr, td, ol, fc, comp)
                                        print(instance_name)
                                        print("wtf", wtf)
                                        for i,e in enumerate(list_of_requests): #range(1, r + 1):
                                            
                                            type_commodity = "H"
                                            if i > request_comp_pf[rc][0] * r:
                                                type_commodity = "F"
                                            array_comp = []
                                            
                                            for c in comp[type_commodity]:
                                                array_comp.append(c.get_random_copy(occupancy_levels[ol][0], occupancy_levels[ol][1]))
                                            
                                            # Makeup demand
                                            demand = "/".join(str(c) for c in array_comp)
                                            # Save demand in request object
                                            e["demand"] = demand
                                            
                                            csv_response = "{0},{1},{2},{3},{4},{5}\n".format(
                                                r, rc, sd, ibr, td, ol)

                                            #with open(instance_path
                                             + "output.csv", 'a') as file:
                                            #    file.write(csv_response)

                                        


                                            #print("ibr", ibr, "i", i, type_commodity, e)"""

    def getRowNYC(row):
        # Dictionary of data
        info = {}

        index = 0
        info['VendorID'] = row[index]
        index += 1

        info['tpep_pickup_datetime'] = datetime.strptime(
            row[index], '%Y-%m-%d %H:%M:%S')

        index += 1
        info['tpep_dropoff_datetime'] = datetime.strptime(
            row[index], '%Y-%m-%d %H:%M:%S')

        index += 1
        info['passenger_count'] = int(row[index])

        index += 1
        info['trip_distance'] = float(row[index])

        index += 1
        info['pickup_longitude'] = row[index]

        index += 1
        info['pickup_latitude'] = row[index]

        index += 1
        info['ratecode_id'] = row[index]

        index += 1
        info['store_and_fwd_flag'] = row[index]

        index += 1
        info['dropoff_longitude'] = row[index]

        index += 1
        info['dropoff_latitude'] = row[index]

        index += 1
        info['payment_type'] = row[index]

        index += 1
        info['fare_amount'] = row[index]

        index += 1
        info['extra'] = row[index]

        index += 1
        info['mta_tax'] = row[index]

        index += 1
        info['tip_amount'] = float(row[index])

        index += 1
        info['tolls_amount'] = row[index]

        index += 1
        info['improvement_surcharge'] = row[index]

        index += 1
        info['total_amount'] = row[index]

        return info

    def isValidRow(info, min_distance, max_distance):
        if float(info['pickup_longitude']) == 0 \
                or float(info['pickup_latitude']) == 0 \
                or float(info['dropoff_longitude']) == 0 \
                or float(info['dropoff_latitude']) == 0 \
                or info['trip_distance'] <= 0 \
                or info['trip_distance'] < min_distance \
                or info['trip_distance'] > max_distance:
            return False
        else:
            return True

    @staticmethod
    def get_network_tuples_not_tested(path_instances):
        # Set of test cases to be generated
        gen_set = set()
        # Loop all vehicle test cases and store those not yet
        # tested to set gen_set
        # Example of request name: delft-the-netherlands_subnetworks_S010_SUB_02
        for nw_name in GenTestCase.network_tuples:
            nw_path =  path_instances +"/" + nw_name +".csv"
            print("Checking request ", nw_path)
            if not os.path.isfile(nw_path):
                test_case = nw_name.split("_")
                reg = test_case[0]
                sub = test_case[1]
                spr = int(test_case[2][1:])/100
                zon = test_case[3]
                zon = (int(zon[1:]) if zon[0]=="Z" else 0)
                t = int(test_case[4])
                gen_set.add((reg,sub,spr,zon,t))
            else:
                print("Request", req_path, "already exists.")
        
        return gen_set

    @staticmethod
    def generate_network_instances(path_instances):
        regions = GenTestCase.network_instances["REGION"]
        save_fig = GenTestCase.network_instances["SAVE_FIG"]
        show_seeds = GenTestCase.network_instances["SHOW_SEEDS"]
        subnetwork_types = GenTestCase.network_instances["SUBNETWORK_TYPES"]
        spread = GenTestCase.network_instances["SPREAD"]
        n_of_instances = GenTestCase.network_instances["#TEST"]
        n_zones = GenTestCase.network_instances["#ZONES"]

        for r in regions:
            file_name = get_file_name(r)
            #G = download_network(region=region, network_type="drive")
            # Loading network
            # G = load_network("delft_the_netherlands.graphml")
            G = None
            network_name = '{0}.graphml'.format(file_name)
            
            # If regions was already downloaded
            if os.path.exists(root+network_name):
                print("Loading network '", network_name,"'...")
                G = load_network(filename=network_name, folder=root)
            else:
                print("Downloading network '", network_name,"'...")
                G = download_network(region=r, network_type="drive")
                print("Graph downloaded:", G.graph["name"])
            
            
            # Get largest connected component from graph G
            largest_cc = get_largest_connected_component(G)
            print("Largest component:", len(largest_cc),"/",len(G.nodes()))

            # Get subgraph from G containing only the nodes in largest connected components
            strongly_connected_G = get_subgraph_from_nodes(G, largest_cc)
            
            for p in spread:
                for i in range(1, n_of_instances+1):
                    for st in subnetwork_types:
                        # Create zone
                        if st == "zones":
                        
                            # For each number of zones
                            for nz in n_zones:

                                # Get zone
                                Z = get_zoned_network(strongly_connected_G,
                                            mode = "autonomous",
                                            n_zones = nz,
                                            percentage = p)
                                
                                # File name
                                file_name = get_instance_file_name(st, i, Z.graph["name"], p, nz)
                                
                                # Save img for final zone
                                save_pic(network=Z,
                                    save_fig=save_fig,
                                    show_seeds=show_seeds,
                                    file_name=file_name)

                                # Save zone
                                save_graph_data(Z, file_name=file_name, path=path_instances)

                        # Create subnetwork
                        elif st == "subnetworks":
                            Z = create_subnetwork(strongly_connected_G,
                                            mode="autonomous",
                                            percentage=p)
                            # File name
                            file_name = get_instance_file_name(st, i, Z.graph["name"], p)

                            # Save img for final zone
                            save_pic(network=Z,
                                    save_fig=save_fig,
                                    show_seeds=show_seeds,
                                    file_name=file_name)
                            
                            # Save subnetwork
                            save_graph_data(Z, file_name=file_name, path=path_instances)


        
    @staticmethod
    def extract_data_nyc(origin_file_path,
                         window,
                         min_distance,
                         max_distance,
                         max_amount):

        list_of_requests = list()

        # Data dictionary
        # http://www.nyc.gov/html/tlc/downloads/pdf/data_dictionary_trip_records_yellow.pdf

        try:
            # Try opening csv file
            with open(origin_file_path) as f:
                reader = csv.reader(f)

                # Get header in first line
                header = next(reader)

                dict_time_windows = {}

                from_datetime = datetime.strptime(
                    window[0], '%Y-%m-%d %H:%M:%S')
                to_datetime = datetime.strptime(window[1], '%Y-%m-%d %H:%M:%S')

                # Create viable paths for files
                dateA = from_datetime.strftime('%Y_%m_%d_%Hh%Mm%Ss')
                dateB = to_datetime.strftime('%Y_%m_%d_%Hh%Mm%Ss')

                amount = 0

                for row in reader:

                    # Separate row in dictionary
                    info = GenTestCase.getRowNYC(row)

                    # If data in row is valid (not zero, correct distances)
                    if not GenTestCase.isValidRow(info, min_distance, max_distance):
                        continue

                    # If amount of lines saved for window surpasses
                    # allowed amount, window is completely processed
                    if amount >= max_amount:
                        break

                    # If demand line is inside the time window
                    if info['tpep_pickup_datetime'] >= from_datetime \
                            and info['tpep_pickup_datetime'] <= to_datetime:

                        # Increment amount of lines in window
                        amount += 1

                        req = {'pickup_longitude': info['pickup_longitude'],
                               'pickup_latitude': info['pickup_latitude'],
                               'dropoff_longitude': info['dropoff_longitude'],
                               'dropoff_latitude': info['dropoff_latitude'],
                               'trip_distance': info['trip_distance']}

                        list_of_requests.append(req)

                return list_of_requests

        except IOError as e:
            # Does not exist OR no read permissions
            print("Unable to open file + " + str(e))
            return {}

        """
        compartments = [("HET", "A=5_XL=5"),
                        ("HET", "A=5_XL=1_L=4_M=8"),
                        ("REG", "A=10_XL=10"),
                        ("REG", "A=10_XL=2_L=8_M=16")]
        """

        """
        compartments = [("HET", "A=5_XL=5"),
                        ("HET", "A=5_XL=1_L=4_M=8"),
                        ("REG", "A=10_XL=10"),
                        ("REG", "A=10_XL=2_L=8_M=16")]
        compartments = {("HET", "A=5_XL=5"): {"H": [Compartment("A", 5)], "F": [Compartment("XL", 5), Compartment("L", 10)]},
                        ("REG", "A=10_XL=10"): {"H": [Compartment("A", 10)], "F": [Compartment("XL", 10)]}}

        
        compartments = {("HET", "A=5-XL=5"): {"H": [CompartmentHuman("A", 5)], "F": [CompartmentFreight("XL", 5)]},
                        ("HET", "A=5-XL=5-L=3"): {"H": [CompartmentHuman("A", 5)], "F": [CompartmentFreight("XL", 5), CompartmentFreight("L", 5)]},
                        ("REG", "A=10-XL=10"): {"H": [CompartmentHuman("A", 10)], "F": [CompartmentFreight("XL", 10)]}}
        """
        """
        compartments = [("HET", "05A_05XL"),
                        ("HET", "05A_01XL_08L"),
                        ("HET", "05A_01XL_04L_08M"),
                        ("REG", "10A_10XL"),
                        ("REG", "10A_02XL_16L"),
                        ("REG", "10A_02XL_08L_16M")]

        """

        """
        extraction_intervals = [('2015-02-14 00:00:00', '2015-02-20 23:59:59'),
                                ('2015-02-14 00:00:00', '2015-02-14 23:59:59'),
                                ('2015-02-14 00:00:00', '2015-02-14 11:59:59'),
                                ('2015-02-14 12:00:00', '2015-02-14 23:59:59'),
                                ('2015-02-14 00:00:00', '2015-02-14 00:59:59'),
                                ('2015-02-14 01:00:00', '2015-02-14 01:59:59'),
                                ('2015-02-14 02:00:00', '2015-02-14 02:59:59'),
                                ('2015-02-14 03:00:00', '2015-02-14 03:59:59'),
                                ('2015-02-14 04:00:00', '2015-02-14 04:59:59'),
                                ('2015-02-14 05:00:00', '2015-02-14 05:59:59'),
                                ('2015-02-14 06:00:00', '2015-02-14 06:59:59'),
                                ('2015-02-14 07:00:00', '2015-02-14 07:59:59'),
                                ('2015-02-14 08:00:00', '2015-02-14 08:59:59'),
                                ('2015-02-14 09:00:00', '2015-02-14 09:59:59'),
                                ('2015-02-14 10:00:00', '2015-02-14 10:59:59'),
                                ('2015-02-14 11:00:00', '2015-02-14 11:59:59'),
                                ('2015-02-14 12:00:00', '2015-02-14 12:59:59'),
                                ('2015-02-14 13:00:00', '2015-02-14 13:59:59'),
                                ('2015-02-14 14:00:00', '2015-02-14 14:59:59'),
                                ('2015-02-14 15:00:00', '2015-02-14 15:59:59'),
                                ('2015-02-14 16:00:00', '2015-02-14 16:59:59'),
                                ('2015-02-14 17:00:00', '2015-02-14 17:59:59'),
                                ('2015-02-14 18:00:00', '2015-02-14 18:59:59'),
                                ('2015-02-14 19:00:00', '2015-02-14 19:59:59'),
                                ('2015-02-14 20:00:00', '2015-02-14 20:59:59'),
                                ('2015-02-14 21:00:00', '2015-02-14 21:59:59'),
                                ('2015-02-14 22:00:00', '2015-02-14 22:59:59'),
                                ('2015-02-14 23:00:00', '2015-02-14 23:59:59')]
        """
        """
        with open(instance_path
 + "output.csv", 'a') as file:
            file.write(",".join(labels) + "\n")

        with open(instance_path
 + "outputREQ.csv", 'a') as file:
            file.write(",".join(req_labels) + "\n")

        for r in n_requests:  # 0
            for rc in request_comp_pf.keys():  # 1
                for sd in parcel_spatial_distribution:  # 2
                    for ibr in interval_between_requests:  # 3
                        for td in trips_distance.keys():  # 4
                            for ol in occupancy_levels.keys():  # 5
                                csv_response = "{0},{1},{2},{3},{4},{5}\n".format(
                                    r, rc, sd, ibr, td, ol)
                                with open(instance_path
                         + "outputREQ.csv", 'a') as file:
                                    file.write(csv_response)
                                print(
                                    "R{0:02}({1}-{2}_I{3}_D{4})_{5}.csv".format(r, rc, sd, ibr, td, ol))

        # 2017-09-13 19:49,4.881191,52.370715,4.870891,52.369457,A=2,180,600
        """
        """
        line = "2017-09-13 19:49,4.881191,52.370715,4.870891,52.369457"
        for r in n_requests:  # 0
            for rc in request_comp_pf.keys():  # 1
                request_comp_pf[rc]
                for sd in parcel_spatial_distribution:  # 2
                    for ibr in interval_between_requests:  # 3
                        for td in trips_distance:  # 4
                            for ol in occupancy_levels.keys():  # 5
                                for v in n_vehicles:  # 6
                                    for fc in fleet_composition:  # 7
                                        for comp in [b for (a, b) in compartments.keys() if a == fc]:  # 8

                                            comp_obj = Compartment.get_random_request(
                                                comp, "_", "=", occupancy_levels[ol][0], occupancy_levels[ol][1])
                                            print("Comp_obj:", comp_obj)
                                            csv_response = "{0},{1},{2},{3},{4},{5},{6},{7},{8}\n".format(
                                                r, request_comp_pf[rc], sd, ibr, td, ol, v, fc, comp)
                                            with open(instance_path
                                     + "output.csv", 'a') as file:
                                                file.write(csv_response)
                                            print("R{0:02}({1}-{2}_I{3}_D{4}_COMP{5})_{6:02}({7}_{8}).csv".format(
                                                r, request_comp_pf[rc], sd, ibr, td, ol, v, fc, comp))

        """
        """line = "2017-09-13 19:49,4.881191,52.370715,4.870891,52.369457"
        cont = 0

        """
        """extraction_intervals = [['2015-02-14 17:55:00', '2015-02-14 17:59:59'],
                                ['2015-02-14 18:00:00', '2015-02-14 18:59:59']]
        """


"""
def extract_data_nyc(self,
                     origin_file_path,
                     time_window,
                     headers_requests,
                     min_distance,
                     max_distance,
                     max_amount):

    requests_list = []

    # Data dictionary
    # http://www.nyc.gov/html/tlc/downloads/pdf/data_dictionary_trip_records_yellow.pdf
    path = ""
    # Get the path from the origin file to save the extracted excerpt
    if origin_file_path.find("/") >= 0:
        path = origin_file_path.split("/")[0] + "/ExtractedNYC/"
    try:
        unfineshed_windows = [frozenset(window) for window in time_window]
        sys.stdout.flush()
        # Try opening csv file
        with open(origin_file_path) as f:
            reader = csv.reader(f)

            # Get header in first line
            header = next(reader)

            dict_time_windows = {}
            amount = dict()
            for window in time_window:
                from_datetime = datetime.strptime(
                    window[0], '%Y-%m-%d %H:%M:%S')
                to_datetime = datetime.strptime(
                    window[1], '%Y-%m-%d %H:%M:%S')

                # Create viable paths for files
                dateA = from_datetime.strftime('%Y_%m_%d_%Hh%Mm%Ss')
                dateB = to_datetime.strftime('%Y_%m_%d_%Hh%Mm%Ss')

                # Path of the cut file
                cut_file_path = path + dateA + "_" + dateB + ".csv"

                dict_time_windows[frozenset(window)] = (
                    from_datetime, to_datetime, cut_file_path)

                amount[frozenset(window)] = 0

                # Write header
                with open(cut_file_path, "a") as cut_file:
                    line = ""
                    for k in headers_requests:
                        line += k + ","

                    line = line[0:-1]
                    cut_file.write(line + "\n")

            for row in reader:
                # If all windows' data were created
                if len(unfineshed_windows) is 0:
                    break
                # Dictionary of data
                info = self.getRowNYC(row)
                if float(info['pickup_longitude']) == 0 \
                        or float(info['pickup_latitude']) == 0 \
                        or float(info['dropoff_longitude']) == 0 \
                        or float(info['dropoff_latitude']) == 0\
                        or info['trip_distance'] <= 0\
                        or info['trip_distance'] < min_distance\
                        or info['trip_distance'] > max_distance:
                    continue

                for window in dict_time_windows.keys():
                    # If window's values were all added, skip
                    # adding more values
                    if window not in unfineshed_windows:
                        continue

                    # If amount of lines saved for window surpasses
                    # allowed amount, window is completely processed
                    if amount[window] > max_amount:
                        unfineshed_windows.remove(window)
                        continue

                    dateA = dict_time_windows[window][0]
                    dateB = dict_time_windows[window][1]

                    # If demand line is inside the time window
                    if info['tpep_pickup_datetime'] >= dateA \
                            and info['tpep_pickup_datetime'] <= dateB:

                        # Increment amount of lines in window
                        amount[window] += 1

                        cut_file_path = dict_time_windows[window][2]

                        with open(cut_file_path, "a") as cut_file:
                            line = ""
                            # Only save lines from predetermined headers
                            for k in headers_requests:
                                line += str(str(info[k]) + ",")
                                # Each window has its own counter

                            line = line[0:-1] + '\n'
                            cut_file.write(line)

    except IOError as e:
        # Does not exist OR no read permissions
        print("Unable to open file + " + str(e))
        return {}
"""

#print("Start generation!")
#a = GenTestCase()
#GenTestCase.generate_network_instances("instances/hybrid/networks")