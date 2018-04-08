import config
from model.Node import *
from model.Response import *
from gurobipy import *
from dao.DaoHybrid import *
from datetime import *
import pprint
import logging

logger = logging.getLogger("main.opt_method")

# Goal:
# - Receive DAO variables
# - Run optimization method
# - Store results in Node, Vehicles variables
# - Create a Response class featuring vehicles, arcs,
#   vars, rides, travel_t, load, arrival_t, DAO and profit


class OptMethod:

    def __init__(self, DAO):
        # Declare the response of the method
        self.response = None

        logger.debug(
            "############################ INIT OPT METHOD #############################")

        # Create copy of DAO
        self.DAO = DAO.copy()

        # The distance matrix
        self.dist_matrix = self.DAO.get_distance_matrix()

        # All points involving the orders
        self.nodes_dic = self.DAO.get_nodes_dic()

        # Start and end av location
        self.starting_locations = self.DAO.get_starting_locations_dic().keys()

        # List of vehicles ids
        self.vehicles = [k.get_id() for k in self.DAO.get_vehicle_list()]

        # Dictionary of vehicles
        self.vehicles_dic = DAO.get_vehicle_dic()

        # List of nodes ids
        self.nodes = list(self.nodes_dic.keys())

        # Dictionary of nodes reachable by vehicles
        self.reachable = DAO.get_reachable()

        self.earliest_latest = DAO.get_earliest_latest()
        logger.debug(
            "################################ EARLIEST LATEST ##########################################")
        logger.debug(pprint.pformat(self.earliest_latest))

        # List of all arcs  = [( p9 , p6, autonomous ), ( p1 , p2, conventional  ), ...]
        # and times = {('p9', 'p6'): 4.2, ('p1', 'p2'): 5.7, ...}
        # WARNING!
        #   - There are no arcs from depots to delivery nodes
        #   - There are no arcs from origin to depots
        #   - There are no arcs from delivery to origin pairs
        #     (Vehicle always visit pk before dl)

        logger.debug(
            "################################# MATRIX ##################################")
        for p1, p2, m in self.dist_matrix.keys():
            logger.debug("%s %s %s", (p1 + "(depot)" if isinstance(self.nodes_dic[p1], NodeDepot) else p1), (
                p2 + "(DL)" if isinstance(self.nodes_dic[p2], NodeDL) else p2), m)

        self.arcs, self.times = multidict({(p1, p2, m): self.dist_matrix[p1, p2, m]
                                           for p1, p2, m in self.dist_matrix.keys()})

        logger.debug(
            "################################# ARCS ####################################")
        logger.debug(pprint.pformat(list(self.arcs)))

        logger.debug(
            '################################# TIMES ###################################')
        logger.debug(pprint.pformat(list(self.times)))

        # Delay in seconds to go from point p1 to point p2 in vehicle k
        self.cost_in_s = {(p1, p2, m): self.dist_matrix[p1, p2, m]
                          for p1, p2, m in self.arcs}

        logger.debug(
            '#### COST #####################################################################')

        logger.debug(pprint.pformat(list(self.cost_in_s)))

        logger.debug(
            '#### VEHICLES #################################################################')

        logger.debug(pprint.pformat(list(self.vehicles_dic)))

        # Get dictionary of requests ex.: {'PK1':Req}
        self.request_dic = self.DAO.get_request_dic()

        # Define earliest latest self.times to attend request
        self.earliest_t = self.DAO.get_earliest_t_dic()

        # Define earliest latest self.times to attend request
        self.earliest_tstamp = self.DAO.get_earliest_tstamp_dic()

        # Define dic of max pick-up delay
        self.max_pickup_delay = self.DAO.get_max_pickup_delay()

        # Define dic of max pick-up delay
        self.max_delivery_delay = self.DAO.get_max_delivery_delay()

        # Set of pick-up points
        self.pk_points = self.DAO.get_pk_points_list()

        # List of pk and dp points
        self.pd_nodes = self.DAO.get_pd_nodes_list()

        # Get dl points
        self.dl_points = self.DAO.get_dl_points_list()

        # List of pickup/delivery tuples from self.requests
        self.pd_tuples = self.DAO.get_pd_tuples()

        # Dictionary of pickup/delivery tuples from self.requests
        self.pd_pairs = self.DAO.get_pd_pairs()

        # Each vehicle k ∈ K has a capacity Qk
        self.capacity_vehicle = self.DAO.get_capacity_vehicles()

        # self.nodes pickup and delivery demands
        # Ex.: {('pk3', 'C'): 1, ('dp1', 'I'): 0, ('dl4', 'C'): -1, ...}
        self.pk_dl = self.DAO.get_pk_dl()

        # Parcel dictionary, e.g. {'AV1_0': ['L', 'XL'], 'AV2_0': ['S']}
        self.lockers_v = self.DAO.get_lockers_v()

        self.vehicle_nodes = self.DAO.get_vehicles_nodes()

        print("TESTEDaaa--", len(self.vehicle_nodes))

    # Return TRUE if vehicle k can fully attend demands of nodes i and j
    def vehicle_fit_node_demand(self, k, i):
        logger.debug("Checking match V{0} and R{1}...".format(k, i))
        id_node_vehicle = self.vehicles_dic[k].get_pos().get_id()
        # Vehicle k can only visit depot nodes that correspond to its
        # own starting position, i.e. DP_AV2_5 can visit node DP_AV2_5
        # but can't visit DP_AV2_4
        if i in self.starting_locations \
                and isinstance(self.DAO.get_nodes_dic()[i], NodeDepot) \
                and id_node_vehicle != i:

            # Log information regarding node i
            logger.debug("Node %s is in starting locations", i)
            logger.debug(self.DAO.get_nodes_dic()[i])
            logger.debug("Network id of vehicle: %s", id_node_vehicle)

            return False

        logger.debug("Node %s belongs to a request", i)
        veh_capacity = self.DAO.get_vehicle_dic()[k].get_capacity()
        demand_i = self.DAO.get_nodes_dic()[i] \
            .get_demand_short()

        logger.debug(demand_i)
        logger.debug("Demand: %s -- Vehicle capacities: %s",
                     demand_i, veh_capacity)
        logger.debug("Demand keys: %s -- Vehicle capacities keys: %s",
                     demand_i.keys(), veh_capacity.keys())
        # If vehicle can a accommodate origin/destination demands
        if set(demand_i.keys()).issubset(set(veh_capacity.keys())):
            logger.debug("Demand keys: %s are SUBSET of vehicle capacities keys: %s",
                         demand_i.keys(), veh_capacity.keys())
            # A vehicle only visits nodes that it can FULLY attend, i.e.,
            # if node demand is greater than node capacity, vehicle will not
            # visit a node.

            # Test if node demand > vehicle capacity for departure node
            for di in demand_i.keys():
                if abs(demand_i[di]) > veh_capacity[di]:
                    logger.debug("%s - Demand (%s) > Capacity: (%s)",
                                 di, demand_i[di], veh_capacity[di])
                    return False

                logger.debug("%s - Demand (%s) < Capacity: (%s)",
                             di, demand_i[di], veh_capacity[di])

            return True
        return False

    def get_big_m(self, k, i, j):
        k_mode = self.vehicles_dic[k].get_type()
        latest_i = self.earliest_latest[(k_mode, i)]["latest"]
        earliest_i = self.earliest_latest[(k_mode, i)]["earliest"]
        service_i = self.earliest_latest[(k_mode, i)]["service"]
        pk_delay_i = self.earliest_latest[(k_mode, i)]["delay"]
        t_i_j = self.times[i, j, k_mode]

        earliest_j = self.earliest_latest[(k_mode, j)]["earliest"]
        big_m = latest_i + t_i_j + service_i - earliest_j
        # E.g.: BIGM A5_D_3, PK001, DL002 - LATEST_i: 00:12:00 (00:07:00+00:05:00)
        #                                   TIME_i_j: 00:02:17
        #                                  SERVICE_i: 00:03:00
        #                                 EARLIEST_j: 00:19:50
        #                                       BIGM:-00:02:33
        # Earliest in J combined with latest in I
        # 19:50(j) >= 12:00(i) + 03:00(service i) + 02:17(time i->j) - (-02:33(M))
        # print("BIGM %s, %s, %s - LATEST_i: %s (%s+%s) TIME_i_j: %s SERVICE_i: %s EARLIEST_j: %s BIGM: %s" % (k, i, j, latest_i, earliest_i, pk_delay_i, t_i_j, service_i, earliest_j, big_m))
        # print("BIGM %s, %s, %s - LATEST_i: %s (%s+%s) TIME_i_j: %s SERVICE_i: %s EARLIEST_j: %s BIGM: %s" % (k, i, j, Node.get_formatted_time_h(latest_i),Node.get_formatted_time_h(earliest_i), Node.get_formatted_duration_h(pk_delay_i), Node.get_formatted_duration_h(t_i_j), Node.get_formatted_duration_h(service_i), Node.get_formatted_time_h(earliest_j), Node.get_formatted_duration_h(big_m)))
        return max(0, big_m)

    def get_big_w(self, c, k, i):
        capacity_k = self.vehicles_dic[k].get_capacity()[c]
        load_i = self.nodes_dic[i].get_demand()[c]
        return min(2 * capacity_k, 2 * capacity_k + load_i)

    def __repr__(self):
        str = '################### PRINT ####################################'
        str += "\n\n##### REQUESTS\n"
        str += pprint.pformat(self.pd_tuples, 4)

        str += "\n\n##### PD NODES\n"
        str += pprint.pformat(self.pd_nodes, 4, 4)

        str += "\n\n##### PICKUPS AND DELIVERIES AT EACH POINT P:\n"
        filter_pk_dl = {}
        for i in self.pk_dl.keys():
            if self.pk_dl[i] != 0:
                filter_pk_dl[i] = pk_dl[i]

        str += pprint.pformat(self.pk_dl, 4)

        str += "\n\n##### SERVICE DURATION AT EACH POINT P:\n"
        str += pprint.pformat(self.service_t, 4)

        str += "\n\n##### EARLIEST:\n"
        str += pprint.pformat(self.earliest_t, 4, 4)

        str += "\n\n##### VEHICLE CAPACITY:\n"
        str += pprint.pformat(self.capacity_vehicle, 4)

        return str

    # Return response generated by opt method
    def get_response(self):
        return self.response

    def get_valid_rides(self):
        #### VARIABLES ###################################################
        # Decision variable - viable vehicle paths
        # A vehicle can only attend requests that it can fully handle,
        # e.g.:
        # k[A,C] - i[A,C] -- OK! (k,i,j)
        #   k[A] - i[A,C] -- NO!
        valid_rides = set()
        logger.debug(
            "########################### REACHEABLE NODES ##############################")
        logger.debug(pprint.pformat(self.reachable))
        logger.debug(
            "############################### ARCS ######################################")
        logger.debug(pprint.pformat([(i, j, mode)
                                     for i, j, mode in self.arcs]))
        print("Number of arcs:", len(self.arcs))
        print("Creating valid rides (k, i, j)...")

        # Create valid rides
        e_l = 0
        for k in self.vehicles:
            k_id = self.vehicles_dic[k].get_pos().get_id()
            mode_vehicle = self.vehicles_dic[k].get_type()
            for i, j, mode in self.arcs:
                # If vehicle k can reach node i
                # if vehicle can travel in arc i,j (coincident modes)
                # if there is a path from model.Vehicle origin to i
                # If vehicle can fully attend request

                if mode != mode_vehicle:
                    continue

                # if vehicle cannot reach i and j
                if (k_id, i) not in self.reachable\
                        or (k_id, j) not in self.reachable:
                    continue

                # logger.debug("############# FIT (%s) %s ->%s", k, i, j)
                if not self.vehicle_fit_node_demand(k, i):
                    continue

                #logger.debug("---------FROM FIT %s", i)
                if not self.vehicle_fit_node_demand(k, j):
                    continue
                #logger.debug("-----------TO FIT %s", j)

                # logger.debug("%s - %s (%s) [ %s -> %s ]",
                #             mode,
                #             k,
                #             k_id,
                #             i,
                #             j)
                latest_i = self.earliest_latest[(mode_vehicle, i)]["latest"]
                latest_j = self.earliest_latest[(mode_vehicle, j)]["latest"]
                earliest_i = self.earliest_latest[(
                    mode_vehicle, i)]["earliest"]
                earliest_j = self.earliest_latest[(
                    mode_vehicle, j)]["earliest"]

                try:
                    if i in self.pk_points:
                        dl = self.pd_pairs[i]

                        if j != dl:
                            if (j, dl, mode_vehicle) not in self.arcs:
                                continue
                            max_ride = self.times[i, dl, mode_vehicle] + \
                                self.nodes_dic[i].get_service_t(
                            ) + self.max_delivery_delay[i]
                            t_i_j = self.times[i, j, mode_vehicle] + \
                                self.nodes_dic[i].get_service_t()
                            t_j_dl = self.times[j, dl, mode_vehicle] + \
                                self.nodes_dic[j].get_service_t()
                            if t_i_j + t_j_dl > max_ride:
                                continue

                except KeyError:
                    print("---", k, i, j)
                    continue

                """self.e_l[(m,p1)]["earliest"] = revealing_r
                self.e_l[(m,p1)]["delay"] = pk_delay_p1
                self.e_l[(m,p1)]["service"] = service_p1
                self.e_l[(m,p1)]["latest"] = self.e_l[(m,p1)]["earliest"] + pk_delay_p1
                self.e_l[(m,p2)]["earliest"] = self.e_l[(m,p1)]["earliest"] + service_p1 + dist_p1_p2
                self.e_l[(m,p2)]["delay"] = dl_delay_p2
                self.e_l[(m,p2)]["service"] = service_p2
                self.e_l[(m,p2)]["latest"] = self.e_l[(m,p2)]["earliest"] + pk_delay_p1"""

                # If e_i=6PM and l_j=5PM, k cannot visit i first, otherwise j cannot be visited
                if earliest_i > latest_j:
                    e_l = e_l + 1
                    continue

                # k, i, j is a valid arc
                valid_rides.add((k, i, j))

        print("Valid rides:", len(valid_rides))
        print("Earliest/latest:", e_l)

        logger.debug(
            "############################### VALID RIDES ##############################")
        logger.debug(pprint.pformat(valid_rides))
        # Set of valid visits (k,i):
        # Vehicle k can fully attend demand in i
        return valid_rides

    def get_valid_visits(self, valid_rides):

        valid_visits = dict()
        valid_visits["all"] = set()
        valid_visits["pk"] = set()

        # Set of valid visits (k,i) where i is a pk node:
        # Vehicle k can fully attend demand in pk node i

        print("Creating valid visits (k, i)...")
        # Create valid rides
        for k, i, j in valid_rides:
            valid_visits["all"].add((k, i))
            valid_visits["all"].add((k, j))
            if i in self.pk_points:
                valid_visits["pk"].add((k, i))

        logger.debug(
            "############################# VALID VISITS PK ##########################")
        logger.debug(pprint.pformat(valid_visits))

        return valid_visits
    ##########################################################################
    ##########################################################################
    ##########################################################################

    def get_valid_loads(self, valid_visits):
        print("Creating valid loads (c, k, i)...")
        # Create valid load variables (c,k,i)
        valid_loads = set()
        for k in self.vehicles:
            for i in self.nodes:
                if (k, i) in valid_visits:
                    for c in self.lockers_v[k]:
                        valid_loads.add((c, k, i))
        
        return valid_loads
