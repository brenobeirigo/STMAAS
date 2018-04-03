# General configuration
import config

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
logger.setLevel(logging.INFO)


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



"""Helpers.save_json(DaoHybrid.network_instances, "data/config" + "/" + "network" + ".json")
Helpers.save_json(config.vehicle_instances, "data/config" + "/" + "vehicles" + ".json")
Helpers.save_json(DaoHybrid.r_info_dual_mode, "data/config" + "/" + "requests" + ".json")"""






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
if config.gen_test_cases:
    GenTestCase.genAllTestCases(config.instance_path_vehicle,
                                config.instance_path_request,
                                config.instance_path_network)


# Get all tested cases to avoid unecessary work
tested_cases = GenTestCase.get_tested_cases(config.all_result_path)

all_tested = set([path_instance_n + "_" + path_instance_v + "_" + path_instance_r
                for path_instance_n in GenTestCase.network_tuples
                for path_instance_v in GenTestCase.vehicle_tuples
                for path_instance_r in GenTestCase.request_tuples
                    if int(path_instance_v.split("_")[0])<=int(path_instance_r.split("_")[0])])




n_tested = len(tested_cases)

total_tested = len(all_tested)


"""thefile1 = open('tested_cases.txt', 'w')
for item in tested_cases:
  thefile1.write("%s\n" % item)

thefile2 = open('all_tested.txt', 'w')
for item in all_tested:
  thefile2.write("%s\n" % item)
  """


print("N. TESTED:", n_tested)
#pprint.pprint(tested_cases)

print("ALL TESTS:", total_tested)
#pprint.pprint(all_tests)

print("INTERSECTION")
print(len(all_tested.intersection(tested_cases)))


print ("Remaining tests: {}/{}({:.2f}%)".format(n_tested, total_tested, n_tested/ total_tested))

for path_instance_n in GenTestCase.network_tuples:
    folder_v_nw = config.instance_path_vehicle+"/"+path_instance_n
    folder_r_nw = config.instance_path_request+"/"+path_instance_n

    # Vary the vehicles attributes
    for path_instance_v in GenTestCase.vehicle_tuples:
        # Vary the requests attributes
        for path_instance_r in GenTestCase.request_tuples:
            n_veh = int(path_instance_v.split("_")[0])
            n_req = int(path_instance_r.split("_")[0])
            
            # There must have at least/most one vehicle per request
            if n_veh > n_req:
                continue

            cont += 1
            n_tested += 1

            instance_id = path_instance_n + "_" + path_instance_v + "_" + path_instance_r

            # Log instance data
            log(logger, config.logs_path + instance_id + ".log", 'w')

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
                DAO = DaoHybrid((config.instance_path_network, path_instance_n),
                            (folder_r_nw, path_instance_r+".csv"),
                            (folder_v_nw, path_instance_v+".csv"),
                            config.lockers_info_path,
                            config.discount_passenger)
            
            # Input file probably doesn't exist ("Not generated yet")
            except Exception as e:
                print("Impossible reading files. Exception:{0}".format(str(e)))
                close_logs()
                # Start next test case
                continue
            
            
            
            try:
                print("*** RUNNING MODEL ****")
                darp2 = SARP_PL(DAO, config.time_limit)

                # Print routing data in vehicles
                print("\
                ############################### \
                FLEET DATA \
                ##############################")

                response = darp2.get_response()
                response.print_requests_info()
            except:
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
            for k in Vehicle.vehicle_modes:
                if k in response.mix_n:
                    mix.append(str(response.mix_n[k]))
                else:
                    mix.append("0")
            mix = ",".join(mix)

            save_mode = "path_excel"
            source_input = defaultdict(lambda:defaultdict(str))
            source_input["path"]["network"] = config.instance_path_network + "/" + path_instance_n + ".json"
            source_input["path"]["request"] = config.instance_path_request + "/" + path_instance_n + "/" + path_instance_r+".csv"
            source_input["path"]["vehicle"] =  config.instance_path_vehicle + "/" + path_instance_n + "/" + path_instance_v+".csv"
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
            print("----->>>>> PROGRESS {0}/{1}({2:.2f}%)".format(n_tested, total_tested, n_tested/ total_tested))


            # Save json to file
            """with open(json_result_path + json_file_name, 'w') as file:
                file.write(jsonResponse)
            """
            with open(config.all_result_path, 'a') as file:
                file.write("\n"+line)
            
            close_logs()
            # print(jsonResponse)
            #print(json.dumps(json.loads(jsonResponse), sort_keys=True, indent=3))
            # Plot result
            # darp2.plot_result()
            # Plot solution in javascript
            # webbrowser.open(url_solution_GUI)
