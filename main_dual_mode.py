# General configuration
import config
from dao.DaoHybrid import DaoHybrid
from milp.SARP_PL import SARP_PL
import webbrowser
import math
from GenTestCase import *
import logging

# Create Logger
# https://www.blog.pythonlibrary.org/2012/08/02/python-101-an-intro-to-logging/
logger = logging.getLogger('main')
logging.Logger.disabled = False
logger.setLevel(logging.INFO)


def set_save_mode(source_input, save_mode):
    if save_mode == "excel":
        source_input[save_mode]["network"] = "=HYPERLINK(\"{0}\";\"{1}\")".format(
            source_input["path"]["network"], source_input["network"])
        source_input[save_mode]["request"] = "=HYPERLINK(\"{0}\";\"{1}\")".format(
            source_input["path"]["request"], source_input["request"])
        source_input[save_mode]["vehicle"] = "=HYPERLINK(\"{0}\";\"{1}\")".format(
            source_input["path"]["vehicle"], source_input["vehicle"])
        source_input[save_mode]["image"] = "=HYPERLINK(\"{0}\";\"{1}.png\")".format(
            source_input["path"]["image"], source_input["network"])
        source_input[save_mode]["log"] = "=HYPERLINK(\"{0}\";\"{1}\")".format(
            source_input["path"]["log"], source_input["instance"])


def get_source_input(test_case):

    n = test_case["n"]
    v = test_case["v"]
    r = test_case["r"]

    instance_id = test_case["id"]
    source_input = defaultdict(lambda: defaultdict(str))
    source_input["network"] = n
    source_input["vehicle"] = v
    source_input["request"] = r
    source_input["instance"] = instance_id
    source_input["path"]["network"] = config.instance_path_network + \
        "/" + n + ".json"
    source_input["path"]["request"] = config.instance_path_request + \
        "/" + n + "/" + r + ".csv"
    source_input["path"]["vehicle"] = config.instance_path_vehicle + \
        "/" + n + "/" + v + ".csv"
    source_input["path"]["image"] = config.images_path + n + ".png"
    source_input["path"]["log"] = config.logs_path + instance_id + ".log"
    return source_input


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


def get_result_line(test_case, response=None, save_mode=None):

    n_data = test_case["n_params"]
    v_data = test_case["v_params"]
    r_data = test_case["r_params"]
    instance_id = test_case["id"]

    line = ""
    if response != None:
        source_input = get_source_input(test_case)
        if save_mode != None:
            set_save_mode(source_input, save_mode)
        line = "{0},{1},{2},{3},{4},{5},{6},{7},{8},{9},{10},{11},{12},{13},{14:.6f},{15},{16:.6f},{17:.6f},{18:.6f},{19:.6f},{20},{21},{22:.6f},{23:.6f},{24},{25},{26},{27:.6f},{28:.6f},{29},{30},{31},{32},{33}".format(
            n_data[0], n_data[1], n_data[2], n_data[3], n_data[4],
            v_data[0], v_data[1],
            r_data[0], r_data[1], r_data[2], r_data[3], r_data[4], r_data[5],
            ",".join([str(response.mix_n[k])
                      if k in response.mix_n else "0" for k in Vehicle.vehicle_modes]),
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
    else:
        line = "{0},{1},{2},{3},{4},{5},{6},{7},{8},{9},{10},{11},{12},,,,,,,,,,,,,,,,,,,,,".format(
            n_data[0], n_data[1], n_data[2], n_data[3], n_data[4],
            v_data[0], v_data[1],
            r_data[0], r_data[1], r_data[2], r_data[3], r_data[4], r_data[5]
        )
    return line


##############################################################################
##### Loop all instances #####################################################
##############################################################################

# Generate test cases?
if config.gen_test_cases:
    GenTestCase.genAllTestCases()


# Number of tested cases
n_tested = len(config.tested_cases)

# Total number of test cases
total_tested = len(config.all_tests)

print("Remaining tests: {}/{}({:.2f}%)".format(n_tested,
                                               total_tested, n_tested / total_tested))

# Vary network, vehicle, and request info
for n, v, r in config.all_tests:

    # Get dict with test case info
    test_case = config.get_test_case_info(n, v, r)

    # Only not tested instances are saved
    if test_case["id"] in config.tested_cases:
        n_tested += 1
        print("TESTED: ", test_case["id"])
        continue

    # Log instance data
    log(logger, config.logs_path + test_case["id"] + ".log", 'w')

    # Generate test case label
    test_case_label = config.get_test_case_label(test_case)
    logger.info(test_case_label)
    print(test_case_label)

    # Try reading the test case
    try:
        DAO = DaoHybrid(test_case)

    except Exception as e:
        # Input file probably doesn't exist ("Not generated yet")
        print(
            "Impossible reading files in test case (Exception:{0}):".format(str(e)))
        pprint.pprint(test_case)
        close_logs()
        # Start next test case
        continue

    print("*** RUNNING MODEL ****")
    ilp_model = SARP_PL(DAO, config.time_limit)

    # If model running is interrupted
    if ilp_model.status == "interrupted":
        close_logs()
        print("INTERRUPTED:", test_case["id"])
        continue

    # Output line
    line = ""

    # If model is infeasible, store test case id and empty data
    if ilp_model.status == "infeasible":
        print("INFEASIBLE:", test_case["id"])
        # Build response line for infeasible
        line = get_result_line(test_case)

    # If model is executed successfully
    elif ilp_model.status == "optimal":
        response = ilp_model.get_response()
        # printing response
        response.print_requests_info()

        # Build response line
        line = get_result_line(test_case, response, save_mode="excel")
        print("RUNTIME:", response.get_solver_sol()[
              "runtime"], "----->>>>> PROGRESS {0}/{1}({2:.2f}%)".format(n_tested, total_tested, n_tested / total_tested))

    # Write line in the result file
    with open(config.all_result_path, 'a') as file:
        file.write("\n" + line)

    # Close log file
    close_logs()
