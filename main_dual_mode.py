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
logging.Logger.disabled = False
logger.setLevel(logging.DEBUG)


def log(logger_obj, file, m):
    hdlr = logging.FileHandler(file, mode=m)
    formatter = logging.Formatter(
        '%(asctime)s - %(name)s - %(levelname)s - %(message)s')
    hdlr.setFormatter(formatter)
    logger_obj.addHandler(hdlr)

def close_logs():
    x = list(logger.handlers)
    for i in x:
        logger.removeHandler(i)
        i.flush()
        i.close()

# SERVICE COSTS
discount_passenger = 0.2  # * (tt / st - 1)
# Put this data into the files, separation per locker size
instance_path_vehicle = "instances/hybrid/vehicles"
instance_path_request = "instances/hybrid/requests"
instance_path_network = "instances/hybrid/networks"
result_path_json = "instances/json/"
all_result_path = "results.csv"
logs_path = "solution_logs/"

gen_test_cases = False
# INPUT PARAMETERS
# PARAMETERS
time_limit = 10
# Address of visualization
url_solution_GUI = "http://localhost/requestGen/solutionGUI.html"
# Where json responses are saved for exibition
#json_result_path = "C:/Servers/htdocs/requestGen/jsonResponse/"
json_result_path = "D:/SERVERS/xampp/htdocs/requestGen/jsonResponse/dual/"

# Fare, Fare per distance and category of the locker
lockers_info_path = "data/config/config_lockers.csv"


# LABELS
labels_networks = list(DaoHybrid.network_instances.keys())[0:-2]
labels_vehicles = list(DaoHybrid.v_info_dual.keys())[0:2]
labels_requests = list(DaoHybrid.r_info_dual_mode.keys())

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
labels = labels_networks+labels_vehicles + labels_requests + Vehicle.vehicle_modes_short + labels_sol


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
                    splitted = row[0:13]
                    test_case_name = "_".join(splitted)
                    tested_cases.add(test_case_name)

            pprint.pprint(tested_cases)
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


# Generate test cases?
if gen_test_cases:
    GenTestCase.genAllTestCases(instance_path_vehicle,
                                instance_path_request,
                                instance_path_network)


# Get all tested cases to avoid unecessary work
tested_cases = get_tested_cases(all_result_path)

for path_instance_n in GenTestCase.network_tuples:
    folder_v_nw = instance_path_vehicle+"/"+path_instance_n
    folder_r_nw = instance_path_request+"/"+path_instance_n

    # Vary the vehicles attributes
    for path_instance_v in GenTestCase.vehicle_tuples:
        # Vary the requests attributes
        for path_instance_r in GenTestCase.request_tuples:
            n_veh = path_instance_v.split("_")[0]
            n_req = path_instance_r.split("_")[0]
            # There must have at least one vehicle per request
            if n_veh != n_req:
                continue

            cont += 1
            instance_id = path_instance_n + "_" + path_instance_v + "_" + path_instance_r

            # Log instance data
            log(logger, logs_path + instance_id + ".log", 'w')

            # Only not tested instances are saved
            if instance_id in tested_cases:
                print("TESTED ", instance_id)
                continue

            s = "\n############################################################################################################################"
            s = s + "\n# NETWORK: {0} \n# VEHICLE: {1} \n# REQUEST:{2} \n# FILE:{3}".format(
                path_instance_n,
                path_instance_v,
                path_instance_r,
                instance_id + ".log")

            s = s + "\n############################################################################################################################"
            logger.info(s)
            print(s)

            try:
                DAO = DaoHybrid((instance_path_network, path_instance_n),
                            (folder_r_nw, path_instance_r+".csv"),
                            (folder_v_nw, path_instance_v+".csv"),
                            lockers_info_path,
                            discount_passenger)
            
            # Input file probably doesn't exist ("Not generated yet")
            except Exception as e:
                print("Impossible reading files. Exception:{0}".format(str(e)))
                close_logs()
                # Start next test case
                continue
            
            
            print("*** RUNNING MODEL ****")
            darp2 = SARP_PL(DAO, time_limit)

            # Print routing data in vehicles
            print("\
            ############################### \
            FLEET DATA \
            ##############################")
            try:
                response = darp2.get_response()
                response.print_requests_info()
            except:
                print("Time is up. No response found.")
                close_logs()
                continue
            print("RUNTIME:", response.get_solver_sol()["runtime"])

            # jsonResponse = darp2.get_response().get_json()

            # print(labels)

            n_data = str(path_instance_n).split("_")
            v_data = str(path_instance_v).split("_")
            r_data = str(path_instance_r).split("_")

            # Get mix of vehicles like 1,2,3 for A,C,D
            mix = list()
            n_mix_mode = response.get_mix()
            for k in Vehicle.vehicle_modes:
                if k in n_mix_mode:
                    mix.append(str(n_mix_mode[k]))
                else:
                    mix.append("0")
            mix = ",".join(mix)

            save_mode = "path_excel"
            source_input = defaultdict(lambda:defaultdict(str))
            source_input["path"]["network"] = instance_path_network + "/" + path_instance_n + ".json"
            source_input["path"]["request"] = instance_path_request + "/" + path_instance_n + "/" + path_instance_r+".csv"
            source_input["path"]["vehicle"] =  instance_path_vehicle + "/" + path_instance_n + "/" + path_instance_v+".csv"
            source_input["path"]["image"] =  "images/" + path_instance_n + ".png"
            source_input["path"]["log"] = "solution_logs/"+instance_id+".log"
            source_input["path_excel"]["network"] = "=HYPERLINK(\"{0}\";\"{1}\")".format(source_input["path"]["network"], path_instance_n)
            source_input["path_excel"]["request"] = "=HYPERLINK(\"{0}\";\"{1}\")".format(source_input["path"]["request"], path_instance_r)
            source_input["path_excel"]["vehicle"] = "=HYPERLINK(\"{0}\";\"{1}\")".format(source_input["path"]["vehicle"], path_instance_v)
            source_input["path_excel"]["image"] = "=HYPERLINK(\"{0}\";\"{1}.png\")".format(source_input["path"]["image"], path_instance_n)
            source_input["path_excel"]["log"] = "=HYPERLINK(\"{0}\";\"{1}\")".format(source_input["path"]["log"], instance_id)

            print("PATH INSTANCE", path_instance_r, path_instance_v)
            line = "{0},{1},{2},{3},{4},{5},{6},{7},{8},{9},{10},{11},{12},{13},{14:.6f},{15},{16:.6f},{17:.6f},{18:.6f},{19:.6f},{20},{21},{22:.6f},{23:.6f},{24},{25},{26},{27:.6f},{28:.6f},{29},{30},{31},{32},{33}".format(
                n_data[0], n_data[1], n_data[2], n_data[3], n_data[4],
                v_data[0], v_data[1],
                r_data[0], r_data[1], r_data[2], r_data[3], r_data[4], r_data[5],
                mix,
                response.get_overall_occupancy_v(),
                response.get_n_vehicles(),
                round(float(response.get_profit()), 2),
                response.get_profit_reqs(),
                response.get_overall_operational_cost(),
                response.get_solver_sol()["gap"],
                response.get_solver_sol()["num_vars"],
                response.get_solver_sol()["num_constrs"],
                response.get_solver_sol()["obj_bound"],
                response.get_solver_sol()["obj_val"],
                response.get_solver_sol()["node_count"],
                response.get_solver_sol()["sol_count"],
                response.get_solver_sol()["iter_count"],
                response.get_solver_sol()["preprocessing_t"],
                response.get_solver_sol()["runtime"],
                source_input[save_mode]["network"],
                source_input[save_mode]["request"],
                source_input[save_mode]["vehicle"],
                source_input[save_mode]["image"],
                source_input[save_mode]["log"]
            )

            print(line)

            # Save json to file
            """with open(json_result_path + json_file_name, 'w') as file:
                file.write(jsonResponse)
            """
            with open(all_result_path, 'a') as file:
                file.write("\n"+line)
            
            close_logs()
            # print(jsonResponse)
            #print(json.dumps(json.loads(jsonResponse), sort_keys=True, indent=3))
            # Plot result
            # darp2.plot_result()
            # Plot solution in javascript
            # webbrowser.open(url_solution_GUI)
