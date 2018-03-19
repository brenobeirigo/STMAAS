from Dao import *
from OptMethod import *
import json
import webbrowser
import math
from GenTestCase import *

# SERVICE COSTS
cost_per_s = 0.005  # $/s
discount_passenger = 0.2  # * (tt / st - 1)
# Put this data into the files, separation per locker size
instance_path_vehicle = "instances/vehicles/"
instance_path_request = "instances/requests/"
result_path_json = "instances/json/"
all_result_path = "result32r60min.csv"
gen_test_cases = False
# INPUT PARAMETERS
# PARAMETERS
time_limit = 10

# There is no need to pull data from server
new_data = False
# Address of visualization
url_solution_GUI = "http://localhost/requestGen/solutionGUI.html"
# Where json responses are saved for exibition
json_result_path = "D:/SERVERS/xampp/htdocs/requestGen/jsonResponse/"
# FILES
# requests_list_path = "data/input_requests_same_departure.csv"  # Requests details
# requests_list_path = "data/input_requests.csv"  # Requests details
# vehicles_list_path = "data/input_vehicles_spacious.csv"  # Vehicles features

requests_list_path = "data/input_requests_NYC_32_50_50_R10.csv"  # Requests details
vehicles_list_path = "data/input_vehicles_NYC_16_REG.csv"  # Vehicles features

# requests_list_path = "instances/32_3_1_4_SS_5-10_5km-10km_HIGH_A=5-XL=5.csv"  # Requests details
# vehicles_list_path = "data/input_vehicles_NYC_16_integrated.csv"  # Vehicles features

# Fare, Fare per distance and category of the locker
lockers_info_path = "data/config_lockers.csv"


# Pull distances from API for new requests and vehicless if
# new_data is true
if gen_test_cases:
    GenTestCase.genRequests(instance_path_request)
    GenTestCase.genVehicles(instance_path_vehicle)

Dao.get_distances(new_data)

"""
DAO = DaoSARP_NYC(requests_list_path,
                  vehicles_list_path,
                  lockers_info_path,
                  cost_per_s,
                  discount_passenger)

# Generate test case
#GenTestCase.genRequests(instance_path_request)
#GenTestCase.genVehicles(instance_path_vehicle)
GenTestCase.tes()

# Label of the test case
config = 1
for deny_service in deny_service_set:
    # Every ride can only be MAX_LATENESS seconds over the fastest trip
    for max_lateness in ride_lateness_set:
        # Every vehicle must serve a request within MAX_PICKUP_LATENESS seconds.
        # The arrival time is only determined for pick_up points. The delivery points
        # arrival time is derived from the travel time.
        for max_pickup_lateness in pickup_lateness_set:
            for time_limit in time_limit_set:
                print(
                    "**********************************************************************************************")
                print(
                    "**********************************************************************************************")
                print("## %03d ## DENY_SERVICE: %r || MAX_LATENESS: %d || MAX_PICKUP_LATENESS: %d || TIME_LIMIT: %d" % (
                    config,
                    deny_service,
                    max_lateness,
                    max_pickup_lateness,
                    time_limit))
                print(
                    "**********************************************************************************************")
                print(
                    "**********************************************************************************************")

                # Create solution
                darp2 = SARP_PL(DAO,
                                max_lateness,
                                max_pickup_lateness,
                                deny_service,
                                time_limit)

                # Print routing data in vehicles
                print("\
                ############################### \
                FLEET DATA \
                ##############################")

                darp2.get_response().print_requests_info()

                jsonResponse = darp2.get_response().get_json()

                # Save json to file
                with open(json_result_path + "output.json", 'w') as file:
                    file.write(jsonResponse)

                # print(jsonResponse)
                #print(json.dumps(json.loads(jsonResponse), sort_keys=True, indent=3))
                # Plot result
                # darp2.plot_result()
                # Plot solution in javascript
                webbrowser.open(url_solution_GUI)
                DAO.reset()
"""
# GenTestCase.tes()
# VEHICLES
n_vehicles = GenTestCase.v_info["#VEHICLES"]
# Heterogeneus and regular vehicles
fleet_composition = GenTestCase.v_info["FLEET COMPOSITION"]
compartments = GenTestCase.v_info["COMPARTMENTS DIV."]

# REQS
n_requests = GenTestCase.r_info["#REQUESTS"]
request_comp_pf = GenTestCase.r_info["H_F_SHARE"]
parcel_spatial_distribution = GenTestCase.r_info["SPATIAL_DIST"]
interval_between_requests = GenTestCase.r_info["INTERVAL"]
trips_distance = GenTestCase.r_info["TRIPS_DIST"]
occupancy_levels = GenTestCase.r_info["OCCUPANCY_LEVELS"]
demand_limit = GenTestCase.r_info["DEMAND_LIMIT"]
nature_requests = GenTestCase.r_info["NATURE"]

# LABELS
labels_vehicles = list(GenTestCase.v_info.keys())
labels_requests = list(GenTestCase.r_info.keys())
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
labels = labels_vehicles + labels_requests + labels_sol

# SET OF CASE TESTS TO SKIP
tested_cases = set()
try:
    # Try opening csv file
    with open(all_result_path, "r") as f:
        reader = csv.reader(f)
        header = next(reader)

        # For each data row
        for row in reader:
            # Get instance identity
            splitted = row[0:11]
            tested_cases.add("_".join(splitted))

except IOError as e:
            # Does not exist OR no read permissions
    print("Unable to read file... Creating", all_result_path)
    with open(all_result_path, 'w') as file:
        file.write(",".join(labels))

# Counter of instances tested
cont = 0

for v in n_vehicles:  # 6
    for fc in fleet_composition:  # 7
        for a, b in [(a, b) for (a, b) in compartments.keys() if a == fc]:  # 8
            for td in trips_distance.keys():  # 4
                print("VEH:", fc, a, b)
                for r in n_requests:  # 0 OK --- 3
                    for ibr in interval_between_requests.keys():  # 3
                        for j in nature_requests:  # JOINT OR DISJOINT
                            for rc in request_comp_pf.keys():  # 1 OK --- 3_1_4
                                for sd in parcel_spatial_distribution:  # 2 OK
                                    for ol in occupancy_levels.keys():  # 5 OK --- HIGH(>half)
                                        for k in demand_limit.keys():
                                            cont += 1
                                            path_instance_v = "{0:02}_{1}_{2}".format(
                                                v, a, b)
                                            path_instance_r = "{0:02}_{1}_{2}_{3}_{4}_{5}_{6}_{7}".format(
                                                r, rc, sd, ibr, td, ol, k, j)
                                            instance_id = path_instance_v+"_"+path_instance_r
                                            # Only not tested instances are saved
                                            if instance_id in tested_cases:
                                                print("TESTED ", instance_id)
                                                continue

                                            json_file_name = instance_id + ".json"

                                            print(
                                                "###############################################################################################################################################")
                                            print(cont, "--- INSTANCE VEHICLE: ", path_instance_v,
                                                  "--- INSTANCE REQUEST:", path_instance_r, "--- FILE:", json_file_name)
                                            print(
                                                "###############################################################################################################################################")

                                            DAO = DaoSARP_NYC(instance_path_request + path_instance_r+".csv",
                                                              instance_path_vehicle + path_instance_v+".csv",
                                                              lockers_info_path,
                                                              cost_per_s,
                                                              discount_passenger)

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
                                            line = "{0:02},{1},{2},{3:02},{4},{5},{6},{7},{8},{9},{10},{11:.6f},{12},{13:.6f},{14:.6f},{15:.6f},{16:.6f},{17:.6f},{18},{19},{20:.6f},{21:.6f},{22},{23},{24},{25:.6f},{26},{27},{28},{29}".format(
                                                v,
                                                a,
                                                b,
                                                r, rc, sd, ibr, td, ol, k, j,
                                                response.get_overall_occupancy_v(),
                                                response.get_n_vehicles(),
                                                round(
                                                    float(response.get_profit()), 2),
                                                response.get_profit_reqs(),
                                                response.get_overall_operational_cost(),
                                                response.get_overall_detour_discount(),
                                                response.get_solver_sol()[
                                                    "gap"],
                                                response.get_solver_sol()[
                                                    "num_vars"],
                                                response.get_solver_sol()[
                                                    "num_constrs"],
                                                response.get_solver_sol()[
                                                    "obj_bound"],
                                                response.get_solver_sol()[
                                                    "obj_val"],
                                                response.get_solver_sol()[
                                                    "node_count"],
                                                response.get_solver_sol()[
                                                    "sol_count"],
                                                response.get_solver_sol()[
                                                    "iter_count"],
                                                response.get_solver_sol()[
                                                    "runtime"],
                                                json_file_name,
                                                "http://localhost/requestGen/solutionGUI.html?json={0}".format(
                                                    json_file_name),
                                                instance_path_request + path_instance_r+".csv",
                                                instance_path_vehicle + path_instance_v+".csv")

                                            # Save json to file
                                            with open(json_result_path + json_file_name, 'w') as file:
                                                file.write(jsonResponse)

                                            with open(all_result_path, 'a') as file:
                                                file.write("\n"+line)

                                            # print(jsonResponse)
                                            #print(json.dumps(json.loads(jsonResponse), sort_keys=True, indent=3))
                                            # Plot result
                                            darp2.plot_result()
                                            # Plot solution in javascript
                                            webbrowser.open(url_solution_GUI)
