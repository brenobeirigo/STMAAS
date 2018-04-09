import config
from model.Request import Request
from model.Vehicle import Vehicle
from model.Compartment import *
from gen.map import *
from model.Coordinate import Coordinate
from model.Node import *
from decimal import *
import pprint
import copy
from manip.URLHelpers import *
import json
import csv
import time
from random import *
from datetime import datetime, date, time, timedelta
from collections import OrderedDict
import pprint
import sys
import logging
logger = logging.getLogger("main.dao_hybrid")


class Dao(object):

    distance_list_path = "data/input_dist.csv"
    request_nyc_path = "data/yellow_tripdata_2015-02.csv"
    url_mapbox = "https://api.mapbox.com/directions-matrix/v1/mapbox/driving/"
    MAPBOX_ACCESS_TOKEN = "pk.eyJ1IjoiYnJlbm9iZWlyaWdvIiwiYSI6ImNpeHJiMDNidTAwMm0zNHFpcXVzd2UycHgifQ.tWIDAiRhjSzp1Bd40rxaHw"
    dist_dic = {}
    new_data = False
    cont = 0

    # https://developers.google.com/maps/documentation/utilities/polylineutility
    # https://www.mapbox.com/api-documentation/#waypoint-object
    # https://api.mapbox.com/directions/v5/mapbox/driving/-73.970974,40.785534;-73.962158,40.768075;-73.970974,40.779803?access_token=pk.eyJ1IjoiYnJlbm9iZWlyaWdvIiwiYSI6ImNpeHJiMDNidTAwMm0zNHFpcXVzd2UycHgifQ.tWIDAiRhjSzp1Bd40rxaHw

    # Read distances from file
    # http://www.nyc.gov/html/tlc/html/about/trip_record_data.shtml
    # http://www.nyc.gov/html/tlc/downloads/pdf/data_dictionary_trip_records_yellow.pdf

    @classmethod
    def get_distances(cls, new_data):
        Dao.new_data = new_data
        print("Read distances data and save them in memory...", new_data)
        # List of requests
        try:
            # Try opening csv file
            with open(Dao.distance_list_path) as f:
                reader = csv.reader(f)
                header = next(reader)
                # Id customer according to number of rows
                id_customer = 0

                # For each data row
                for row in reader:
                    # Pickup latitude
                    pickup_x = float(row[0])
                    # Pickup longitude
                    pickup_y = float(row[1])
                    # Dropoff latitude
                    dropoff_x = float(row[2])
                    # Dropoff longitude
                    dropoff_y = float(row[3])
                    # Distance betweeen points
                    dist = float(row[4])

                    # Save distance
                    cls.dist_dic[(pickup_x, pickup_y,
                                  dropoff_x, dropoff_y)] = dist

        except IOError as e:
            # Does not exist OR no read permissions
            print("Unable to open file")
            return {}

    def get_distance_matrix(self):
        return self.distance_matrix

    def get_distance_from_to(self, p1, p2, mode=None):
        dic_dist_mode = dict()
        if mode:
            tuple = (p1, p2, mode)
            print(tuple)
            dic_dist_mode[mode] = self.distance_matrix[tuple]
        else:
            for m in vehicle_modes:
                tuple = (p1, p2, m)
                if tuple in self.distance_matrix:
                    dic_dist_mode[m] = self.distance_matrix[tuple]
        return dic_dist_mode

    def get_capacity_vehicles(self):
        return self.capacity_vehicles

    def get_earliest_t_dic(self):
        return self.earliest_t

    def get_max_pickup_delay(self):
        return self.max_pickup_delay

    def get_max_delivery_delay(self):
        return self.max_delivery_delay

    def get_earliest_tstamp_dic(self):
        return self.earliest_tstamp

    def get_pk_points_list(self):
        return self.pk_points_list

    def get_dl_points_list(self):
        return self.dl_points_list

    def get_pd_nodes_list(self):
        return self.pd_nodes

    def get_request_dic(self):
        return self.request_dic

    def get_pd_tuples(self):
        return self.pd_tuples

    def get_pd_pairs(self):
        return self.pd_pairs

    def get_vehicle_dic(self):
        return self.vehicle_dic

    def get_pk_dl(self):
        return self.pk_dl

    def get_vehicles_nodes(self):
        return self.vehicles_nodes

    def get_vehicle_list(self):
        return self.vehicle_list

    def get_request_list(self):
        return self.request_list

    def get_vehicle_list(self):
        return self.vehicle_list

    def get_nodes_dic(self):
        return self.nodes_dic

    def get_modes_from_to(self, dist):
        """"Find which modes can depart from PK nodes and arrive at DL.


        Arguments:
            dist {dict} -- Dictionary of all distances p1,m,p2
        """

        pk_dl_modes = defaultdict(set)
        for pk, r in self.get_request_dic().items():
            pk_id_nw = r.get_origin().get_network_id()
            dl_id_nw = r.get_destination().get_network_id()
            pk_id = r.get_origin().get_id()
            dl_id = r.get_destination().get_id()

            for mode, target in dist[pk_id_nw].items():
                if dl_id_nw in target:
                    pk_dl_modes[pk_id].add(mode)
                    pk_dl_modes[dl_id].add(mode)

        return pk_dl_modes

    def get_reachable_o_d(self, network):
        logger.debug(
            "############################ REACHABLE ##################################")
        reachable = set()
        to = defaultdict(set)
        for p1, p2, m in network.keys():

            if isinstance(self.get_nodes_dic()[p1], NodePK):
                to[p1].add(p2)

        logger.debug(pprint.pformat(to))

        for p1, p2, m in network.keys():
            if p1 in self.starting_nodes_dic.keys():
                reachable.add((p1, p2))
                reachable.add((p1, p1))
                for p in to[p2]:
                    reachable.add((p1, p))

        return reachable

    def get_viable_network(self, dist):

        # Modes allowed to depart from PK and arrive at DL
        modes_from_to = self.get_modes_from_to(dist)
        logger.debug(
            "################################# MODES FROM TO ####################################")
        logger.debug(pprint.pformat(modes_from_to))

        # Graph NxN - Remove self connections and arcs arriving in end depot
        nodes_network = dict()

        # For every node
        for p1 in self.nodes_dic.values():
            p1_id = p1.get_id()
            p1_nw_id = p1.get_network_id()

            # Create the dictionary of nodes connected to p1
            nodes_network[p1_id] = dict()

            # For each outbound mode from p1
            for mode in dist[p1_nw_id].keys():

                # For every possible target node
                for p2 in self.nodes_dic.values():
                    p2_id = p2.get_id()
                    p2_nw_id = p2.get_network_id()

                    # There is no looping arc
                    if p1_id == p2_id:
                        continue

                    # Only modes allowed to visit p2's origin/destination can be combined to p2
                    if not isinstance(self.get_nodes_dic()[p2_id], NodeDepot) and mode not in modes_from_to[p2_id]:
                        continue

                    # Only modes allowed to visit p1's origin/destination can be combined to p1
                    if not isinstance(self.get_nodes_dic()[p1_id], NodeDepot) and mode not in modes_from_to[p1_id]:
                        continue

                    """
                    # There is no looping arc
                    if p1_id == p2_id and p1_id not in self.starting_nodes_dic.keys():
                        continue

                    # Origins are never destinations
                    if p2_id in self.starting_nodes_dic.keys() \
                    and p1_id not in self.starting_nodes_dic.keys():
                        continue
                    
                    if p1_id != p2_id \
                    and p1_id in self.starting_nodes_dic.keys() \
                    and p2_id in self.starting_nodes_dic.keys():
                        continue
                    """

                    # Origins are never destinations
                    if p2_id in self.starting_nodes_dic.keys():
                        continue

                    # There is no arc from DL to PK of request R
                    if (p2_id, p1_id) in self.pd_tuples:
                        continue

                    # There are no arcs from starting nodes to delivery nodes
                    if p1_id in self.starting_nodes_dic.keys() and isinstance(self.get_nodes_dic()[p2_id], NodeDL):
                        continue

                    # There are no arcs from origin to depots
                    if p2_id in self.starting_nodes_dic.keys() and isinstance(self.get_nodes_dic()[p1_id], NodePK):
                        continue

                    try:
                        d = dist[p1_nw_id][mode][p2_nw_id]

                        """if isinstance(p1,NodePK)
                        dl = self.pd_pairs[p1_id]
                        if p2_id != dl:
                            max_ride = self.times[p1_id, dl, mode_vehicle] + \
                                self.max_delivery_delay[i]
                            t_i_j = self.times[p1_id, dl, mode_vehicle] + self.nodes_dic[p1_id].get_service_t()
                            t_j_dl = self.times[, dl, mode_vehicle] + self.nodes_dic[j].get_service_t()
                            if t_i_j + t_j_dl > max_ride:
                                continue"""
                        if mode not in nodes_network[p1_id].keys():
                            nodes_network[p1_id][mode] = dict()
                        nodes_network[p1_id][mode][p2_id] = d
                    except KeyError:
                        pass

        return nodes_network

    def create_distance_matrix(self, network, speed=40):
        m_s = speed * (1000 / 3600)
        # Generate fast access dictionary for distance
        # d = t*v
        # t = d/v = d/16
        # 40km/h => 40000m/3600s = 400/36 = 11.11m/s
        distance_matrix = dict()

        for p1 in network.keys():
            for m in network[p1].keys():
                for p2 in network[p1][m].keys():
                    distance_matrix[(p1, p2, m)] = int(
                        network[p1][m][p2] / m_s)

        return distance_matrix

    def __init__(self):

        # Load network related data
        G = load_network(filename=self.network_path,
                         folder=config.instance_path_network)
        #dist = create_distance_data(G)

        dist = load_dist_dic(
            config.instance_path_network + "/" + self.network_path)
        # logger.debug("###################################### LOAD DISTANCE MATRIX ########################################")
        # logger.debug(pprint.pformat(dist))

        # print("########################################### NODES NETWORK #########################################")
        # pprint.pprint(netw)

        print("Loading distances from '{0}'".format(
            self.network_path), len(dist))

        # Generate fast access dictionary for distance
        #self.distance_matrix = self.create_distance_matrix(network = self.nodes_network, speed=40)

        self.nodes_network = self.get_viable_network(dist)
        self.distance_matrix = self.create_distance_matrix(
            network=self.nodes_network, speed=40)
        self.reachable = self.get_reachable_o_d(self.distance_matrix)

        logger.debug(
            "################################## DIST MATRIX #####################################")
        logger.debug(pprint.pformat(self.nodes_network))

        logger.debug(
            "################################### D. MATRIX ######################################")
        logger.debug(pprint.pformat(self.distance_matrix))

        logger.debug(
            "################################### D. REACHABLE ###################################")
        logger.debug(pprint.pformat(self.reachable))

    def get_earliest_latest(self):
        return self.e_l

    def copy(self):
        return copy.deepcopy(self)

    def get_reachable(self):
        return self.reachable

    def create_earliest_latest_dic(self):
        logger.debug("Creating earliest latest time data...")
        self.e_l = defaultdict(dict)
        earliest_tstamp = int(config.start_revealing_tstamp)

        logger.debug("Earliest time: %s", earliest_tstamp)

        for r in self.request_list:
            p1 = r.get_origin().get_id()
            p2 = r.get_destination().get_id()
            for m in self.nodes_network[p1].keys():
                if p2 in self.nodes_network[p1][m].keys():
                    logger.debug("%s [%s] %s", p1, m, p2)
                    # Earliest timestamp in relation to the earliest time in the system
                    # when vehicles are ready to set out
                    revealing_r = r.get_revealing_tstamp() - earliest_tstamp
                    dist_p1_p2 = self.distance_matrix[(p1, p2, m)]
                    pk_delay_p1 = r.get_pickup_delay()
                    dl_delay_p2 = r.get_delivery_delay()
                    service_p1 = self.get_nodes_dic()[p1].get_service_t()
                    service_p2 = self.get_nodes_dic()[p2].get_service_t()
                    self.e_l[(m, p1)]["earliest"] = revealing_r
                    self.e_l[(m, p1)]["delay"] = pk_delay_p1
                    self.e_l[(m, p1)]["service"] = service_p1
                    self.e_l[(m, p1)]["latest"] = self.e_l[(
                        m, p1)]["earliest"] + pk_delay_p1
                    self.e_l[(m, p2)]["earliest"] = self.e_l[(m, p1)
                                                             ]["earliest"] + service_p1 + dist_p1_p2
                    self.e_l[(m, p2)]["delay"] = dl_delay_p2
                    self.e_l[(m, p2)]["service"] = service_p2
                    self.e_l[(m, p2)]["latest"] = self.e_l[(
                        m, p2)]["earliest"] + dl_delay_p2

                    # If times are arbitrary, shrink time windows!
                    """true_latest_p2 = self.e_l[(m,p1)]["latest"] + self.e_l[(m,p1)]["service"] + dist_p1_p2
                    dif = true_latest_p2 - self.e_l[(m,p2)]["latest"]
                    true_latest_p1 = (self.e_l[(m,p1)]["latest"] - dif if dif > 0  else self.e_l[(m,p1)]["latest"])

                    #pprint.pprint(self.e_l)
                    print("{0} - {1} ({2}) -> {3} + {4} = {5} <= {6} - {7} + {8} - ({9})".format(
                    p1,
                    p2,
                    m,
                    self.e_l[(m,p1)]["latest"],
                    self.e_l[(m,p1)]["service"] + dist_p1_p2,
                    true_latest_p2,
                    self.e_l[(m,p2)]["latest"],
                    self.e_l[(m,p2)]["earliest"],
                    dl_delay_p2,
                    true_latest_p1))"""

                    logger.debug("%s - %s -> %s", p1, Node.get_formatted_time_h(self.e_l[(
                        m, p1)]["earliest"] + earliest_tstamp), Node.get_formatted_time_h(self.e_l[(m, p1)]["latest"] + earliest_tstamp))
                    logger.debug("%s - %s -> %s", p2, Node.get_formatted_time_h(self.e_l[(
                        m, p2)]["earliest"] + earliest_tstamp), Node.get_formatted_time_h(self.e_l[(m, p2)]["latest"] + earliest_tstamp))

        for v in self.get_vehicle_dic().values():
            m = v.get_type()
            o = v.get_pos().get_id()
            start = v.get_available_at()
            self.e_l[(m, o)]["earliest"] = 0
            self.e_l[(m, o)]["latest"] = 24 * 3600
            self.e_l[(m, o)]["delay"] = 0
            self.e_l[(m, o)]["service"] = 0

        logger.debug(pprint.pformat(self.e_l))


class DaoHybrid(Dao):

    # Read requests from file
    def get_requests_from(self):
        # List of requests
        request_list = []

        # Try opening csv file
        with open(self.requests_list_path) as f:
            reader = csv.reader(f)
            header = next(reader)

            # Id customer according to number of rows
            id_customer = 0

            # For each data row
            for row in reader:
                id_customer += 1
                # Revealing instant
                revealing = datetime.strptime(row[0], '%Y-%m-%d %H:%M:%S')
                # Pickup latitude
                pickup_x = float(row[1])
                # Pickup longitude
                pickup_y = float(row[2])
                # Dropoff latitude
                dropoff_x = float(row[3])
                # Dropoff longitude
                dropoff_y = float(row[4])
                # Order configuration as dictionary, e.g. A=2/C=1 => {'A':2, 'C':1}
                order = {o.split('=')[0]: int(o.split('=')[1])
                         for o in row[5].split('/')}
                try:
                    # Pickup lateness
                    pickup_lateness = int(row[6])
                except:
                    pickup_lateness = None

                try:
                    # Delivery lateness (s)
                    delivery_lateness = int(row[7])
                except:
                    delivery_lateness = None

                try:
                    # Id origin node on streamlined map
                    id_origin_node = row[8]
                except:
                    id_origin_node = None
                try:
                    # Id origin node on streamlined map
                    id_destination_node = row[9]
                except:
                    id_destination_node = None
                try:
                    # Service level class of customer e.g. A,B,C
                    service_level = row[10]
                except:
                    service_level = None
                try:
                    # Ad hoc id
                    customer = row[11]
                    if len(customer) == 0:
                        raise IndexError
                except IndexError:
                    customer = 'H_' + str('%03d' % id_customer)

                # Create request for data row

                req = Request(customer,
                              pickup_x,
                              pickup_y,
                              dropoff_x,
                              dropoff_y,
                              revealing,
                              order,
                              pickup_lateness,
                              delivery_lateness,
                              id_origin_node=id_origin_node,
                              id_destination_node=id_destination_node,
                              service_level=service_level)

                # Append request into list of requests
                request_list.append(req)
        return request_list

    def load_lockers_data(self):
        # Example
        # locker,fare,fare_dis,category,pk_delay,dl_delay
        # XS,1,0.001,P,10,10
        # I,2,0.002,H,10,10

        # Try opening csv file
        with open(self.lockers_info_path) as f:

            reader = csv.reader(f)
            header = next(reader)

            # For each data row
            for row in reader:
                locker = row[0]
                self.fare_locker[locker] = float(row[1])
                self.fare_locker_dis[locker] = float(row[2])
                self.fare_locker_category[locker] = row[3]
                self.locker_embarking_t[locker] = int(row[4])  # s
                self.locker_disembarking_t[locker] = int(row[5])  # s

    def reset(self):
        for r in self.request_list:
            r.reset()
        for v in self.vehicle_list:
            v.reset()
        for n in self.nodes_dic.values():
            n.reset()

    # Read vehicles from file - Vehicles a
    def get_individual_vehicles_from(self):
        """[summary]

        Returns:
            [type] -- [description]
        """

        # List of requests
        vehicle_list = []
        # Try opening csv file
        with open(self.vehicles_list_path) as f:
            reader = csv.reader(f)
            # Get the first row with headers
            header = next(reader)
            # Get the label of the sizes
            # ex.: ['XS', 'S', 'M', 'L', 'XL', 'A', 'C', 'B', 'I']
            sizes = header[7:len(header)]
            # Amount of vehicles
            qtd = 0
            # For each data row
            for row in reader:
                qtd += 1
                # Model of vehicle
                model = row[0]
                # Type of vehicle
                type_vehicle = row[1]
                # Time vehicle is available
                available_at = row[2]
                # Latitude vehicle
                latitude = float(row[3])
                # Longitude vehicle
                longitude = float(row[4])
                # id_origin_node
                id_origin_node = row[5]
                # Autonomy vehicle
                autonomy = float(row[6])
                # Array of capacities in vehicle
                capacities = row[7:len(row)]

                # Dictionary of capacities
                dic_capacities = {sizes[i]: int(amount)
                                  for i, amount in enumerate(capacities)}

                # Vehicle ID
                av_id = model + '_' + str(qtd)

                # Vehicle initial location
                initial_location = Node.factory_node('DP',
                                                     'DP_' + av_id,
                                                     latitude,
                                                     longitude,
                                                     {c: 0 for c in dic_capacities.keys(
                                                     ) if dic_capacities[c] > 0},
                                                     None,
                                                     network_node_id=id_origin_node)
                
                veh = Vehicle(av_id,
                              autonomy,
                              initial_location,
                              dic_capacities,
                              available_at,
                              type_vehicle=type_vehicle,
                              acquisition_cost=config.veh_price_scenarios[self.scenario][type_vehicle]["fixed_cost"],
                              operation_cost_s=config.veh_price_scenarios[self.scenario][type_vehicle]["var_cost"])

                # Add vehicle in list
                vehicle_list.append(veh)

        return vehicle_list

    def get_discount_passenger(self):
        return self.discount_passenger

    def get_pd_network_tuples(self):
        return self.pd_network_tuples

    def __init__(self,  test_case):
        
        self.scenario = test_case["s"]
        self.network_path = test_case["n"]
        print(" NETWORK PATH:", self.network_path)
        self.requests_list_path = config.instance_path_request + "/" + test_case["n"] + "/" + test_case["r"] + ".csv"
        self.vehicles_list_path = config.instance_path_vehicle + "/" + test_case["n"] + "/" + test_case["v"] + ".csv"
        self.lockers_info_path = config.lockers_info_path
        self.discount_passenger = config.discount_passenger_s

        self.fare_locker = dict()
        self.fare_locker_dis = dict()
        self.fare_locker_category = dict()
        self.locker_embarking_t = dict()
        self.locker_disembarking_t = dict()

        # DEFINE NODE DATA
        self.nodes_dic = {}
        self.nodes_dic_nw = {}

        # self, id, pos, capacity
        self.vehicle_list = self.get_individual_vehicles_from()

        # vehicles dictionary
        self.vehicle_dic = {v.get_id(): v for v in self.vehicle_list}

        # Create dictionary of starting points in each vehicle
        self.starting_nodes_dic = {self.get_vehicle_dic()[k]
                                       .get_pos()
                                       .get_id():
                                   self.get_vehicle_dic()[k]
                                       .get_pos()
                                   for k in self.get_vehicle_dic().keys()}

        # Create dictionary of starting points in each vehicle (NW)
        self.starting_nodes_dic_nw = {self.get_vehicle_dic()[k]
                                      .get_pos()
                                      .get_network_id():
                                      self.get_vehicle_dic()[k]
                                      .get_pos()
                                      for k in self.get_vehicle_dic().keys()}

        # Create dictionary of starting points in each vehicle
        self.vehicles_nodes = {v.get_pos().get_id(): v
                               for v in self.get_vehicle_dic().values()}

        # Add starting points of vehicles
        for k, v in self.starting_nodes_dic.items():
            self.nodes_dic[k] = v

         # Add starting points of vehicles
        for k, v in self.starting_nodes_dic_nw.items():
            self.nodes_dic_nw[k] = v

        # Load requests from file
        self.request_list = self.get_requests_from()

        # Load lockers data
        self.load_lockers_data()

        # Insert nodes information in dictionary
        for r in self.request_list:
            self.nodes_dic[r.get_origin().get_id()] = r.get_origin()
            self.nodes_dic[r.get_destination().get_id()] = r.get_destination()
            self.nodes_dic_nw[r.get_origin().get_network_id()] = r.get_origin()
            self.nodes_dic_nw[r.get_destination().get_network_id()
                              ] = r.get_destination()

        # The compartments not declared in the request have zero demand
        for n in self.nodes_dic.keys():
            for c in self.fare_locker.keys():
                if c not in self.nodes_dic[n].get_demand().keys():
                    self.nodes_dic[n].get_demand()[c] = 0

        self.request_dic = {
            r.get_origin().get_id(): r for r in self.request_list}

        # Number of passengers picked-up or delivered:
        # pk = load and dl = -load
        # se (start/end) = 0
        # Nodes pickup and delivery demands
        self.pk_dl = {(p,  c): self.nodes_dic[p].get_demand()[c]
                      for p in self.nodes_dic.keys()
                      for c in self.nodes_dic[p].get_demand().keys()
                      }

        # Define earliest latest times to attend request
        self.earliest_t = {p.get_origin().get_id(): p.get_revealing()
                           for p in self.request_list}

        self.earliest_t.update(
            {v.get_pos().get_id(): v.get_available_at() for v in self.vehicle_dic.values()})

        # Define earliest latest times to attend request
        self.earliest_tstamp = {p.get_origin().get_id(): p.get_revealing_tstamp()
                                for p in self.request_list}

        self.earliest_tstamp.update({v.get_pos().get_id(
        ): v.get_available_at_tstamp() for v in self.vehicle_dic.values()})

        # Define max pick-up delay for each node
        self.max_pickup_delay = {p.get_origin().get_id(): p.get_pickup_delay()
                                 for p in self.request_list}

        self.max_pickup_delay.update(
            {v.get_pos().get_id(): 0 for v in self.vehicle_dic.values()})

        # Define max pick-up delay for each node
        self.max_delivery_delay = {p.get_origin().get_id(): p.get_delivery_delay()
                                   for p in self.request_list}

        self.max_delivery_delay.update(
            {v.get_pos(): 0 for v in self.vehicle_dic.values()})

        # Set of pick-up points (human)
        self.pk_points_list = [p.get_origin().get_id()
                               for p in self.request_list]

        # Set of drop-off points (human)
        self.dl_points_list = [p.get_destination().get_id()
                               for p in self.request_list]

        # List of pk and dp points
        self.pd_nodes = []
        self.pd_nodes.extend(self.pk_points_list)
        self.pd_nodes.extend(self.dl_points_list)

        # List of pickup/delivery tuples from model.Requests
        self.pd_tuples = [(p.get_origin().get_id(),
                           p.get_destination().get_id()
                           ) for p in self.request_list]

        # List of pickup/delivery tuples from model.Requests
        self.pd_network_tuples = [(p.get_origin().get_network_id(),
                                   p.get_destination().get_network_id()
                                   ) for p in self.request_list]

        # Dictionary of pickup/delivery tuples from model.Requests
        self.pd_pairs = {p.get_origin().get_id(): p.get_destination().get_id()
                         for p in self.request_list}

        self.pd_pairs_dl = {p.get_destination().get_id(): p.get_origin().get_id()
                            for p in self.request_list}

        # Max load per vehicle dictionary
        self.capacity_vehicles = {(k.get_id(), c): k.get_capacity()[c]
                                  for k in self.vehicle_list
                                  for c in k.get_capacity()}

        # List of lockers keys per vehicle
        self.lockers_v = {k: list(self.vehicle_dic[k].get_capacity().keys())
                          for k in self.vehicle_dic.keys()}

        super().__init__()

        # Update requests costs after defining the distances
        self.update_requests_costs()

        # Define earliest and latest times for each node/mode
        self.create_earliest_latest_dic()

        # Printing input data
        self.print_input_data()

    def get_starting_locations_dic(self):
        return self.starting_nodes_dic

    def print_input_data(self):
        print('####################### COMPARTMENT FARE DATA #######################')
        for c in self.fare_locker.keys():
            print('({0}) {1:>2}: {2:6.3f} (fare) + {3:6.3f} (fare_km) \
            --- Delay pk/dl: {4}s / {5}s'.format(
                self.fare_locker_category[c],
                c,
                self.fare_locker[c],
                self.fare_locker_dis[c],
                self.locker_embarking_t[c],
                self.locker_disembarking_t[c]))

        # https://jsonformatter.curiousconcept.com/

        # Vehicle list
        print("####################### VEHICLE LIST #######################")
        print("ID_VEHICLE,ROUTE,CAPACITY")
        pprint.pprint(self.vehicle_list)

        print("####################### REQUEST DICTIONARY #######################")
        pprint.pprint(self.request_dic)

        print("####################### NODE'S DEMANDS #######################")
        for n in self.nodes_dic.keys():
            print(self.nodes_dic[n].get_id()
                  + " => "
                  + str({k: self.nodes_dic[n].get_demand()[k]
                         for k in self.nodes_dic[n].get_demand()
                         if self.nodes_dic[n].get_demand()[k] != 0}))

        self.request_dic = {
            r.get_origin().get_id(): r for r in self.request_list}

        print("####################### PICK-UP AND DELIVERY DIC #######################")
        for d in self.pk_dl:
            if self.pk_dl[d] != 0:
                print(str(d) + ":" + str(self.pk_dl[d]))

    def get_fare_locker(self):
        return self.fare_locker

    # Calculate:
    # 1 - the costs of all requests
    # 2 - the delay (pk/dl) of all requests
    # after reading the complete input information
    def update_requests_costs(self):
        print("Updating requests...")
        for r in self.request_dic.keys():
            self.request_dic[r].calculate_fare_dual(self)
            self.request_dic[r].calculate_embark_disembark_t(self)

    # Lockers data
    def get_fare_locker_dis(self):
        return self.fare_locker_dis

    def get_fare_locker_category(self):
        return self.fare_locker_category

    def get_locker_embarking_t(self):
        return self.locker_embarking_t

    def get_locker_disembarking_t(self):
        return self.locker_disembarking_t

    def get_lockers_v(self):
        return self.lockers_v

    # Json
    def get_json_compartment_data(self):
        js = '['
        for c in self.fare_locker.keys():
            js += '{'
            a = '"locker_id":"{0}", "locker_category":"{1}", "locker_fare": {2:.3f}, "locker_fare_km": {3:.3f}, "locker_embarking_t": {4}, "locker_disembarking_t": {5}'\
                .format(c, self.fare_locker_category[c], self.fare_locker[c], self.fare_locker_dis[c], self.locker_embarking_t[c], self.locker_disembarking_t[c])
            js += a + "},"
        js = js[:-1] + ']'
        return js
