import config

from dao.DaoHybrid import *
from datetime import datetime, date, time, timedelta
from model.Compartment import *
import math
import random
from collections import OrderedDict
from gen import map
from gen import network as gen_network
from gen import requests as gen_requests
from gen import vehicles as gen_vehicles


class GenTestCase:





    @staticmethod
    def genAllTestCases():

        # Generate file names of network, requests and vehicles

        print("Starting test case generation...")
    
        print("   Generating networks...")

        gen_network.generate_network_instances()
        
        for nw in config.network_tuples:
            
            network_path = config.instance_path_network + "/" + nw
            
            print("   Generating requests for network {0}...".format(nw + ".graphml"))
            # Store request data for network nw
            folder_r_nw = config.instance_path_request + "/" + nw
            if not os.path.exists(folder_r_nw):
                os.makedirs(folder_r_nw)

            gen_requests.genRequests2(path_requests = folder_r_nw,
                                    network_path = network_path)

            print("   Generating vehicles for network {0}...".format(nw + ".graphml"))
            # Store vehicle data for network nw
            folder_v_nw = config.instance_path_vehicle+ "/" + nw
            if not os.path.exists(folder_v_nw):
                os.makedirs(folder_v_nw)

            gen_vehicles.genVehicles2(path_vehicles = folder_v_nw,
                                    network_path = network_path)
    
