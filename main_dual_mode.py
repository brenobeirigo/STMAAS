from DaoHybrid import *
from OptMethod import *
import json
import webbrowser
import math
from GenTestCase import *
import logging

# Create Logger
# https://www.blog.pythonlibrary.org/2012/08/02/python-101-an-intro-to-logging/
logger = logging.getLogger('main')
hdlr = logging.FileHandler('output.log', mode='w')
formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
hdlr.setFormatter(formatter)
logger.addHandler(hdlr)
logger.setLevel(logging.DEBUG)

# SERVICE COSTS
cost_per_s = 0.005  # $/s
discount_passenger = 0.2  # * (tt / st - 1)
# Put this data into the files, separation per locker size
instance_path_vehicle = "instances/hybrid/vehicles"
instance_path_request = "instances/hybrid/requests"
instance_path_network = "instances/hybrid/networks"
result_path_json = "instances/json/"
all_result_path = "results.csv"
gen_test_cases = True
# INPUT PARAMETERS
# PARAMETERS
time_limit = 1000000
# Address of visualization
url_solution_GUI = "http://localhost/requestGen/solutionGUI.html"
# Where json responses are saved for exibition
#json_result_path = "C:/Servers/htdocs/requestGen/jsonResponse/"
json_result_path = "D:/SERVERS/xampp/htdocs/requestGen/jsonResponse/dual/"

# Fare, Fare per distance and category of the locker
lockers_info_path = "data/config/config_lockers.csv"


# Generate test cases?
if gen_test_cases:
    GenTestCase.genAllTestCases(instance_path_vehicle,
                                instance_path_request,
                                instance_path_network)


# LABELS
labels_networks = list(GenTestCase.network_instances.keys())[0:-2]
labels_vehicles = list(GenTestCase.v_info_dual.keys())
labels_requests = list(GenTestCase.r_info_dual_mode.keys())
labels_sol = ["OVERALL_OCCUPANCY",
              "OPERATING_VEHICLES",
              "PROFIT",
              "REQUESTS_REVENUE",
              "OPERATIONAL_COSTS",
              "DETOUR_DISCOUNT",
              "SOL_GAP",
              "NUM_VARS",
              "NUM_CONSTRS",
              "OBJ_BOUND",
              "OBJ_VAL",
              "NODE_COUNT",
              "SOL_COUNT",
              "ITER_COUNT",
              "RUNTIME",
              "JSON",
              "LINK",
              "PATH_REQUESTS",
              "PATH_VEHICLES"]

# HEADER JSON OUTPUT
labels = labels_networks+labels_vehicles + labels_requests + labels_sol


def get_tested_cases(path):
    # SET OF CASE TESTS TO SKIP
    tested_cases = set()
    while True:
        try:
            # Try opening csv file
            with open(path, "r") as f:
                reader = csv.reader(f)
                header = next(reader)

                # For each data row
                for row in reader:
                    # Get instance identity
                    splitted = row[0:11]
                    tested_cases.add("_".join(splitted))
            return tested_cases

        except IOError as e:
                # Does not exist OR no read permissions
            print("Unable to read file... Creating", all_result_path)
            with open(all_result_path, 'w') as file:
                file.write(",".join(labels))

##############################################################################
##### Loop all instances #####################################################
##############################################################################


# Counter of instances tested
cont = 0

# Generate file names of network, requests and vehicles
GenTestCase.gen_network_tuples()
GenTestCase.gen_vehicles_tuples()
GenTestCase.gen_requests_tuples()

# Get all tested cases to avoid unecessary work
tested_cases = get_tested_cases(all_result_path)

for path_instance_n in GenTestCase.network_tuples:
    folder_v_nw = instance_path_vehicle+"/"+path_instance_n
    folder_r_nw = instance_path_request+"/"+path_instance_n
    
    # Vary the vehicles attributes
    for path_instance_v in GenTestCase.vehicle_tuples:
        # Vary the requests attributes
        for path_instance_r in GenTestCase.request_tuples:
            cont += 1
            instance_id = path_instance_n+"_V"+path_instance_v+"_R"+path_instance_r

            # Only not tested instances are saved
            if instance_id in tested_cases:
                print("TESTED ", instance_id)
                continue

            json_file_name = instance_id + ".json"

            s = "\n############################################################################################################################"
            s = s + "\n# NETWORK: {0} \n# VEHICLE: {1} \n# REQUEST:{2} \n# FILE:{3}".format(
                path_instance_n,
                path_instance_v,
                path_instance_r,
                json_file_name)

            s = s + "\n############################################################################################################################"
            logger.info(s)
            print(s)

            DAO = DaoHybrid((instance_path_network, path_instance_n),
                            (folder_r_nw, path_instance_r+".csv"),
                            (folder_v_nw, path_instance_v+".csv"),
                            lockers_info_path,
                            cost_per_s,
                            discount_passenger)

            print("*** RUNNING MODEL ****")
            darp2 = SARP_PL(DAO, time_limit)

            # Print routing data in vehicles
            print("\
            ############################### \
            FLEET DATA \
            ##############################")

            response = darp2.get_response()

            response.print_requests_info()

            jsonResponse = darp2.get_response().get_json()
            print(labels)
            n_data = str(path_instance_n).split("_")
            v_data = str(path_instance_v).split("_")
            r_data = str(path_instance_r).split("_")

            print("PATH INSTANCE", path_instance_r, path_instance_v)
            line = "{0},{1},{2},{3},{4},{5},{6},{7},{8},{9},{10},{11},{12},{13:.6f},{14},{15:.6f},{16:.6f},{17:.6f},{18:.6f},{19:.6f},{20},{21},{22:.6f},{23:.6f},{24},{25},{26},{27:.6f},{28},{29},{30},{31}".format(
                n_data[0],n_data[1],n_data[2],n_data[3],n_data[4],
                v_data[0],v_data[1],
                r_data[0],r_data[1], r_data[2], r_data[3], r_data[4], r_data[5],
                response.get_overall_occupancy_v(),
                response.get_n_vehicles(),
                round(float(response.get_profit()), 2),
                response.get_profit_reqs(),
                response.get_overall_operational_cost(),
                response.get_overall_detour_discount(),
                response.get_solver_sol()["gap"],
                response.get_solver_sol()["num_vars"],
                response.get_solver_sol()["num_constrs"],
                response.get_solver_sol()["obj_bound"],
                response.get_solver_sol()["obj_val"],
                response.get_solver_sol()["node_count"],
                response.get_solver_sol()["sol_count"],
                response.get_solver_sol()["iter_count"],
                response.get_solver_sol()["runtime"],
                json_file_name,
                "http://localhost/requestGen/solutionGUI.html?json={0}".format(
                    json_file_name),
                instance_path_request + path_instance_r+".csv",
                instance_path_vehicle + path_instance_v+".csv",
                )

            print(line)

            # Save json to file
            """with open(json_result_path + json_file_name, 'w') as file:
                file.write(jsonResponse)
            """
            with open(all_result_path, 'a') as file:
                file.write("\n"+line)

            # print(jsonResponse)
            #print(json.dumps(json.loads(jsonResponse), sort_keys=True, indent=3))
            # Plot result
            # darp2.plot_result()
            # Plot solution in javascript
            # webbrowser.open(url_solution_GUI)
