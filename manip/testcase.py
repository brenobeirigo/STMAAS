import csv


def get_test_case_label(test_case):
    s = "\n############################################################################################################################"
    s = s + "\n# NETWORK: {0} \n# VEHICLE: {1} \n# REQUEST:{2} \n# FILE:{3}".format(
        test_case["n"],
        test_case["v"],
        test_case["r"],
        test_case["id"] + ".log")
    s = s + "\n############################################################################################################################"
    return s

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
            return tested_cases

        except IOError as e:
            print(e)

def get_test_case_info(n, v, r):
    test_case = dict()
    # Singular parameters of an instance
    test_case["n_params"] = str(n).split("_")
    test_case["v_params"] = str(v).split("_")
    test_case["r_params"] = str(r).split("_")
    test_case["n"] = n
    test_case["v"] = v
    test_case["r"] = r
    test_case["id"] = n + "_" + v + "_" + r
    return test_case