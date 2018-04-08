from manip import json as manip_json
from manip.filename import *
from manip.testcase import *
import os
from datetime import datetime

start_revealing = '2017-10-10 00:00'
start_revealing_t = datetime.strptime(
    '2017-10-10 00:00:00', '%Y-%m-%d %H:%M:%S')
start_revealing_tstamp = start_revealing_t.timestamp()

# Put this data into the files, separation per locker size
instance_path_vehicle = "instances/hybrid/vehicles"
instance_path_request = "instances/hybrid/requests"
instance_path_network = "instances/hybrid/networks"
result_path_json = "instances/json/"

logs_path = "output/solution_logs/"

# INPUT PARAMETERS
# PARAMETERS
time_limit = 600
# Address of visualization
url_solution_GUI = "http://localhost/requestGen/solutionGUI.html"

# Where json responses are saved for exibition
#json_result_path = "C:/Servers/htdocs/requestGen/jsonResponse/"
json_result_path = "D:/SERVERS/xampp/htdocs/requestGen/jsonResponse/dual/"

# Fare, Fare per distance and category of the locker
lockers_info_path = "data/config/config_lockers.csv"

instances_path = "C:/STMAAS_CONFIG/input.json"

# Where map images are saved
images_path = "output/images/"

# ILP model
debug_path = "output/ilp/debug.lp"

print("Creating instances dic...")
instances_dic = manip_json.load_json(instances_path)

network_instances = instances_dic["network"]
vehicle_instances = instances_dic["vehicle"]
request_instances = instances_dic["request"]

req_n_requests = request_instances["#REQUESTS"] 
req_trips_distance = request_instances["TRIPS_DIST"]
req_sl_share = request_instances["SL_SHARE"]
req_interval = request_instances["INTERVAL"]
req_horizon = request_instances["TIME_HORIZON"]
req_demand_dist_mode = request_instances["DEMAND_DIST_MODE"]
req_demand_limit =  request_instances["DEMAND_LIMIT"]

all_result_path = instances_dic["result_path"]

# LABELS
labels_networks = list(network_instances.keys())[0:-2]
labels_vehicles = list(vehicle_instances.keys())[0:2]
labels_requests = list(request_instances.keys())

# from model.VehicleS
vehicle_modes_short = ["A", "C", "D"]



labels_sol = ["OVERALL_OCCUPANCY",
              "OPERATING_VEHICLES",
              "PROFIT",
              "REQUESTS_REVENUE",
              "OPERATIONAL_COSTS",
              "SOL_GAP",
              "NUM_VARS",
              "NUM_CONSTRS",
              "OBJ_BOUND",
              "OBJ_VAL",
              "NODE_COUNT",
              "SOL_COUNT",
              "ITER_COUNT",
              "PREPROCESS",
              "RUNTIME",
              "PATH_NETWORKS",
              "PATH_REQUESTS",
              "PATH_VEHICLES",
              "IMAGE",
              "LOG"]

# HEADER JSON OUTPUT
labels = labels_networks+labels_vehicles + labels_requests + vehicle_modes_short + labels_sol

# Should test cases be generated?
gen_test_cases = instances_dic["generate_test_cases"]

discount_passenger_s = 0.002

# Vary the vehicles attributes
# v ------- e.g. [10, 20, 30] (number of vehicles)
# c ------- e.g. [A4, A2, A1] (4 adult places, 2 adult places)
network_tuples = set([
    get_instance_file_name(st, i, get_file_name(r), p, nz)
    if st == "zones" else
    get_instance_file_name(st, i, get_file_name(r), p)
    for r in network_instances["REGION"]
    for p in network_instances["SPREAD"]
    for st in network_instances["SUBNETWORK_TYPES"]
    for i in range(1, network_instances["#TEST"] + 1)
    for nz in network_instances["#ZONES"]])

# Vary the vehicles attributes
# v ------- e.g. [10, 20, 30] (number of vehicles)
# c ------- e.g. [A4, A2, A1] (4 adult places, 2 adult places)
vehicle_tuples = ["{0:02}_{1}".format(v, c)
                    for v in vehicle_instances["#VEHICLES"]
                    for c in vehicle_instances["COMPARTMENTS DIV."]]


# Vary the requests attributes
# r -------- e.g. [30, 40, 50] (number of requests)
# td ------- e.g. ["0.5km-1km", "5km-10km"] (min-max distance between OD points)
# sl ------- e.g. ["S1, S2"] (S1 defines Service levels (delays, etc.) for customer classes A,B and C)
# ibr ------ e.g. ["05-10min", "01-05min"] (rate at which requests are revealed)
# d_mode --- e.g. ["D1", "D2"] (What is the demand share going from A to A, A to C, C to A and C to C)
# dl ------- e.g. ["A5"] (customers request from 1 to 5 adult compartments)
request_tuples = ["{0:02}_{1}_{2}_{3}_{4}_{5}".format(r, d_mode, sl, ibr, td, dl)
    for r in request_instances["#REQUESTS"] 
    for td in request_instances["TRIPS_DIST"]
    for sl in request_instances["SL_SHARE"]
    for ibr in request_instances["TIME_HORIZON"]
    for d_mode in request_instances["DEMAND_DIST_MODE"]
    for dl in request_instances["DEMAND_LIMIT"]]


all_tests = set([(path_instance_n, path_instance_v, path_instance_r)
                for path_instance_n in network_tuples
                for path_instance_v in vehicle_tuples
                for path_instance_r in request_tuples
                    if int(path_instance_v.split("_")[0])<=int(path_instance_r.split("_")[0])])

if not os.path.exists(all_result_path):
    # Does not exist OR
    with open(all_result_path, 'w') as file:
        file.write(",".join(labels))

tested_cases = get_tested_cases(all_result_path)


# NETWORK DATA

width_img = 15
height_img = 10
show_img = False
dpi_img = 300
root = "data/network/"
subfolder = "network/"
instance_path_network = "instances/hybrid/networks/"