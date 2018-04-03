import Helpers

# Put this data into the files, separation per locker size
instance_path_vehicle = "instances/hybrid/vehicles"
instance_path_request = "instances/hybrid/requests"
instance_path_network = "instances/hybrid/networks"
result_path_json = "instances/json/"

logs_path = "solution_logs/"

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

instances_dic = Helpers.load_json(instances_path)

network_instances = instances_dic["network"]
vehicle_instances = instances_dic["vehicle"]
request_instances = instances_dic["request"]
all_result_path = instances_dic["result_path"]

# LABELS
labels_networks = list(network_instances.keys())[0:-2]
labels_vehicles = list(vehicle_instances.keys())[0:2]
labels_requests = list(request_instances.keys())

# FROM VEHICLES
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

discount_passenger = 0.002