import config
from Node import *
from gurobipy import *
import pprint
from Response import *
from DaoHybrid import *
from GenTestCase import GenTestCase
from datetime import *
import logging
logger = logging.getLogger("main.opt_method")

# Goal:
# - Receive DAO variables
# - Run optimization method
# - Store results in Node, Vehicles variables
# - Create a Response class featuring vehicles, arcs,
#   vars, rides, travel_t, load, arrival_t, DAO and profit


class OptMethod(object):

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

    def __str__(self):
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

    """
    # Print fixed and variable fares
    def print_fares(self):
        fare_locker_dis = self.DAO.get_fare_locker_dis()
        fare_locker = self.DAO.get_fare_locker()
        for k, i, j in self.valid_rides:
            for c in self.nodes_dic[i].get_demand_short().keys():
                print(k, i, j, c, fare_locker[c], fare_locker_dis[c])

    """

    ##########################################################################
    ##########################################################################
    ##########################################################################


class SARP_PL(OptMethod):
    def __init__(self,
                 DAO,
                 TIME_LIMIT):
        self.TIME_LIMIT = TIME_LIMIT
        self.DISCOUNT_PASSENGER_S = DAO.get_discount_passenger()
        super().__init__(DAO)
        self.start()

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

    def calculate_big_m(self):
        BIGM = dict()
        for k, i, j in self.valid_rides:
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
            BIGM[(k, i, j)] = max(0, big_m)
        logger.debug(
            "############################################ BIG M ##########################################")
        logger.debug(pprint.pformat(BIGM))

        return BIGM

    def calculate_big_w(self):
        BIGW = dict()
        logger.debug(
            "################################### BIGW #########################################")
        for c, k, i in self.valid_loads:
            capacity_k = self.vehicles_dic[k].get_capacity()[c]
            load_i = self.nodes_dic[i].get_demand()[c]
            BIGW[(c, k, i)] = min(2 * capacity_k, 2 * capacity_k + load_i)
            logger.debug("# c: %s # k: %s # i: %s # 2Q: %s # 2Q - load_i: %s",
                         c, k, i, 2 * capacity_k, 2 * capacity_k + load_i)
        return BIGW

    ##########################################################################
    ########### MILP SARP_PL (SHARE-A-RIDE PROBLEM WITH PARCEL LOCKERS) ######
    ##########################################################################
    def start(self):
        print("STARTING MILP...")
        t1 = datetime.now()
        try:

            # Create a new model
            m = Model("SARP_PL")

            #### VARIABLES ###################################################
            # Decision variable - viable vehicle paths
            # A vehicle can only attend requests that it can fully handle,
            # e.g.:
            # k[A,C] - i[A,C] -- OK! (k,i,j)
            #   k[A] - i[A,C] -- NO!
            self.valid_rides = set()
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
                    # if there is a path from vehicle origin to i
                    # If vehicle can fully attend request

                    if mode != mode_vehicle:
                        continue

                    # if vehicle cannot reach i and j
                    if (k_id, i) not in self.reachable\
                            or (k_id, j) not in self.reachable:
                        continue

                    #logger.debug("############# FIT (%s) %s ->%s", k, i, j)
                    if not self.vehicle_fit_node_demand(k, i):
                        continue

                    #logger.debug("---------FROM FIT %s", i)
                    if not self.vehicle_fit_node_demand(k, j):
                        continue
                    #logger.debug("-----------TO FIT %s", j)

                    #logger.debug("%s - %s (%s) [ %s -> %s ]",
                    #             mode,
                    #             k,
                    #             k_id,
                    #             i,
                    #             j)
                    latest_i = self.earliest_latest[(mode_vehicle, i)]["latest"]
                    latest_j = self.earliest_latest[(mode_vehicle, j)]["latest"]
                    earliest_i = self.earliest_latest[(mode_vehicle, i)]["earliest"]
                    earliest_j = self.earliest_latest[(mode_vehicle, j)]["earliest"]

                    try:
                        if i in self.pk_points:
                            dl = self.pd_pairs[i]
                            
                            if j != dl:
                                if (j, dl, mode_vehicle) not in self.arcs:
                                    continue
                                max_ride = self.times[i, dl, mode_vehicle] + self.nodes_dic[i].get_service_t() + self.max_delivery_delay[i]
                                t_i_j = self.times[i, j, mode_vehicle] + self.nodes_dic[i].get_service_t()
                                t_j_dl = self.times[j, dl, mode_vehicle] + self.nodes_dic[j].get_service_t()
                                if t_i_j + t_j_dl > max_ride:
                                    continue
                                

                    except KeyError:
                        print("---", k,i,j)
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
                    if earliest_i >  latest_j:
                        e_l = e_l + 1
                        continue

                    # k, i, j is a valid arc
                    self.valid_rides.add((k, i, j))
            
            print("Valid rides:", len(self.valid_rides))
            print("Earliest/latest:", e_l)
            # Set of valid visits (k,i):
            # Vehicle k can fully attend demand in i
            valid_visits=set()

            logger.debug(
                "############################### VALID RIDES ##############################")
            logger.debug(pprint.pformat(self.valid_rides))
            # Set of valid visits (k,i) where i is a pk node:
            # Vehicle k can fully attend demand in pk node i
            valid_visits_pk=set()

            print("Creating valid visits (k, i)...")
            # Create valid rides
            for k, i, j in self.valid_rides:
                valid_visits.add((k, i))
                valid_visits.add((k, j))
                if i in self.pk_points:
                    valid_visits_pk.add((k, i))

            logger.debug(
                "############################# VALID VISITS PK ##########################")
            logger.debug(pprint.pformat(valid_visits))

            # Ex.:
            #  k     i   j      lockers in k         d_i      d_j
            # AV1_0 dl4 dl2 {'XS', 'C', 'L', 'A'} {'A', 'C'} {'A'}
            # AV1_0 pk1 dp2 {'XS', 'C', 'L', 'A'} {'A'} set()
            # AV1_0 dp1 dp2 {'XS', 'C', 'L', 'A'} set() set()

            # Binary variable, 1 if a vehicle k goes from node i to node j
            ride=m.addVars(self.valid_rides,
                             vtype=GRB.BINARY,
                             name="x")

            # Arrival time of vehicle k at node i
            arrival_t=m.addVars(list(valid_visits),
                                  vtype=GRB.INTEGER,
                                  lb=0,
                                  name="u")

            print("Creating valid loads (c, k, i)...")
            # Create valid load variables (c,k,i)
            self.valid_loads=set()
            for k in self.vehicles:
                for i in self.nodes:
                    if (k, i) in valid_visits:
                        for c in self.lockers_v[k]:
                            self.valid_loads.add((c, k, i))

            #print("Calculating BIGM dictionary...")
            # Define big M
            # BIGM = self.calculate_big_m()

            #print("Calculating BIGW dictionary...")
            # Define big W
            # BIGW = self.calculate_big_w()

            print("Setting constraints...")
            logger.debug(
                "############################# VALID LOADS ##########################")
            logger.debug(pprint.pformat(valid_visits))

            # Load of compartment c of vehicle k at pickup node i
            load=m.addVars(self.valid_loads,
                             vtype=GRB.INTEGER,
                             lb=0,
                             name="w")

            # Ride time of request i served by vehicle k
            travel_t=m.addVars(list(valid_visits_pk),
                                 vtype=GRB.INTEGER,
                                 lb=0,
                                 name="r")

            #### ROUTING CONSTRAINTS ##########################################
            print("    # MAX_1_OUT")
            # (ONLY_PK) = Max. one outbound arc in pickup nodes
            m.addConstrs((ride.sum('*', i, '*') <= 1
                          for i in self.pd_nodes), "MAX_1_OUT")

            print("    # ALL_REQ")
            # (ALL_REQ) = All requests are attended
            m.addConstrs((ride.sum('*', i, '*') == 1
                          for i in self.pk_points), "ALL_REQ")

            print("    # ONLY_1_IN")
            # (ONLY_DL) = There is only one vehicle arriving at a pk/dl point
            m.addConstrs((ride.sum('*', '*', j) <= 1
                          for j in self.pd_nodes), "ONLY_1_IN")

            print("    # BEGIN")
            # (BEGIN) = Every vehicle leaves the start depot
            m.addConstrs((ride.sum(k, self.starting_locations, '*') <= 1
                          for k in self.vehicles), "BEGIN")

            print("    # IF_PK_DL1 / IF_PK_DL2")
            # Same vehicle services pickup and delivery:
            m.addConstrs((ride.sum(k, i, '*') - ride.sum(k,'*', j)  == 0
                          for i, j in self.pd_pairs.items()
                          for k in self.vehicles
                          if (k, i) in valid_visits
                          and (k, j) in valid_visits), name="IF_V_PK_DL")
            
            """m.addConstrs((ride.sum('*', i, '*') + ride.sum('*','*', j)  == 2*selected_req[i]
                          for i, j in self.pd_pairs.items()), name="IF_PK_DL2")
            """

            print("    # FLOW_VEH_PK")
            # (IN_OUT_PK) = self.vehicles enter and leave pk nodes
            m.addConstrs((ride.sum(k, '*', i) == ride.sum(k, i, '*')
                          for i in self.pk_points
                          for k in self.vehicles), name="FLOW_VEH_PK")

            print("    # FLOW_VEH_DL")
            # (IN_OUT) = self.vehicles enter and leave/stay dl nodes
            m.addConstrs((ride.sum(k, '*', i) >= ride.sum(k, i, '*')
                          for i in self.dl_points
                          for k in self.vehicles), name="FLOW_VEH_DL")

            print("    # ARRI_T")
            # (ARRI_T) = Arrival time at location j (departing from i) >=
            #            arrival time in i +
            #            service time in i +
            #            time to go from i to j
            #            IF there is a ride from i to j
            m.addConstrs((arrival_t[k, j] >=
                          arrival_t[k, i] +
                          self.nodes_dic[i].get_service_t() +
                          self.times[i, j, self.vehicles_dic[k].get_type()] -
                          self.get_big_m(k, i, j) * (1 - ride[k, i, j])
                          for k, i, j in self.valid_rides), "ARRI_T")

            #### RIDE TIME CONSTRAINTS ########################################

            print("    # RIDE_1")
            r1 = datetime.now()
            # (RIDE_1) = Ride time from i to j >=
            #            time_from_i_to_j
            m.addConstrs((travel_t[k, i] >= self.times[i, j, self.vehicles_dic[k].get_type()]
                          for k in self.vehicles
                          for i, j in self.pd_tuples
                          if (k, i, j) in self.valid_rides), "RIDE_1")

            print("    # RIDE_2")
            # (RIDE_2) = Ride time from i to j <=
            #            time_from_i_to_j + MAX_LATENESS
            m.addConstrs((travel_t[k, i] <=
                          self.times[i, j, self.vehicles_dic[k].get_type(
                          )] + self.max_delivery_delay[i]
                          for k in self.vehicles
                          for i, j in self.pd_tuples
                          if (k, i, j) in self.valid_rides), "RIDE_2")

            print("    # RIDE_3")
            # (RIDE_3) = Ride time from i to j is >=
            # arrival_time_j - (arrival_time_i + self.service_time_i)
            m.addConstrs((travel_t[k, i] ==
                          arrival_t[k, j] -
                          (arrival_t[k, i] +
                           self.nodes_dic[i].get_service_t())
                          for k in self.vehicles
                          for i, j in self.pd_tuples
                          if (k, i, j) in self.valid_rides), "RIDE_3")
            
            """print("Separated:", datetime.now()-r1)
            r2 = datetime.now()
            for k in self.vehicles:
                for i, j in self.pd_tuples:
                    if (k, i, j) in self.valid_rides:
                        m.addConstr((travel_t[k, i] ==
                          arrival_t[k, j] -
                          (arrival_t[k, i] +
                           self.nodes_dic[i].get_service_t())), "RIDE_32[%s,%s,%s]" % (k, i, j))
                        
                        m.addConstr((travel_t[k, i] <=
                          self.times[i, j, self.vehicles_dic[k].get_type(
                          )] + self.max_delivery_delay[i]), "RIDE_22[%s,%s,%s]" % (k, i, j))

                        m.addConstr((travel_t[k, i] >= self.times[i, j, self.vehicles_dic[k].get_type()]), "RIDE_12[%s,%s,%s]" % (k, i, j))
            print("together:", datetime.now() - r2)"""
            ### TIME WINDOW CONSTRAINTS #######################################
            print("    # EARL")
            #>>>>>> TIME WINDOW FOR PICKUP
            # (EARL) = Arrival time in i >=
            #          earliest arrival time in i
            m.addConstrs((arrival_t[k, i] >= self.earliest_latest[(self.vehicles_dic[k].get_type(), i)]["earliest"]
                          for (k, i) in valid_visits_pk), "EARL")

            print("    # LATE")
            # (LATE) = Arrival time in i <=
            #          earliest arrival time + MAX_PICKUP_LATENESS
            m.addConstrs((arrival_t[k, i] <= self.earliest_latest[(self.vehicles_dic[k].get_type(), i)]["latest"]
                          for (k, i) in valid_visits_pk), "LATE")

            #>>>>>> TIME WINDOW FOR MAX. DURATION OF ROUTE
            # (POWER) = Maximal duration of route k <= POWER_K autonomy
            """
            for veh in self.vehicles:
                a = quicksum(self.cost_in_s[i, j, self.vehicles_dic[k].get_type()] * ride[k, i, j]
                             for k, i, j in self.valid_rides
                                 if k == veh )
                m.addConstr(a <= self.DAO.get_vehicle_dic()[k]
                                     .get_autonomy() * 3600, "POWER[%s]" % (k))
            """
            #### LOADING CONSTRAINTS ##########################################

            print("    # LOAD")
            # (LOAD) = Guarantee load flow
            #          Load of compartment c of vehicle k in node j >=
            #          Load of compartment c of vehicle k in node i +
            #          Load collected for compartment c at node j
            #          IF there is a ride of vehicle k from i to j
            m.addConstrs((load[c, k, j] >=
                          (load[c, k, i] + self.pk_dl[j, c]) -
                          self.get_big_w(c, k, j) * (1 - ride[k, i, j])
                          for k, i, j in self.valid_rides
                          for c in self.lockers_v[k]
                          if (c, k, i) in self.valid_loads
                          and (c, k, j) in self.valid_loads), "LOAD")

            print("    # LOAD_END_DL")
            for c, v, dl in self.valid_loads:
                if dl in self.dl_points:
                    m.addConstr((load[c, v, dl] <= (
                        self.capacity_vehicle[v, c] + self.pk_dl[dl, c]) * ride.sum(v, dl, '*')), "LOAD_END_DL[%s,%s,%s]" % (c, v, dl))

            print("    # LOAD_MIN")
            # (LOAD_MIN) = Load of vehicle k in node i >=
            #              MAX(0, PK/DL demand in i)
            m.addConstrs((load[c, k, i] >= max(0, self.pk_dl[i, c])
                          for c, k, i in self.valid_loads), "LOAD_MIN")

            print("    # LOAD_MAX")
            # (LOAD_MAX) = Load of compartment c of vehicle k in node i <=
            #              MIN(MAX_LOAD, MAX_LOAD - DL demand in i)
            #              Every time a DL node is visited, it is KNOWN
            #              that the load will be decremented. Hence, it
            #              is impossible that the remaining load is higher than
            #              MAX_LOAD, MAX_LOAD - DL
            m.addConstrs((load[c, k, i] <= min(self.capacity_vehicle[k, c],
                                               self.capacity_vehicle[k, c]
                                               + self.pk_dl[i, c])
                          for c, k, i in self.valid_loads
                          ), "LOAD_MAX")

            # The constrainst only applies to nodes that can be visited by
            # vehicle k. Suppose the following:
            # LOAD(XS,AV2,DL2) <= MIN(Q(AV2, XS), Q(AV2, XS) + D(DL2,XS))
            #   must be >=0!   <=         1            1     +   (-2)
            #                  <= -1
            # Vehicle AV2 cannot visit node DL2

            #### FEASIBILITY CONSTRAINTS ######################################
            print("    # LOAD_0")
            m.addConstrs((load[c, k, i] >= 0
                          for c, k, i in self.valid_loads),  "LOAD_0")

            print("    # ARRI_0")
            m.addConstrs((arrival_t[k, i] >= 0
                          for k, i in arrival_t), "ARRI_0")

            print("    # ARRI_AT_ORIGIN")
            # Guarantees a vehicle will be available only at an specified time
            # Some vehicles are discarded because they cannot access any node
            # (not a valid visit)
            m.addConstrs((arrival_t[k, i] ==
                          self.vehicles_dic[k]
                          .get_pos()
                          .get_arrival_t() - Vehicle.start_revealing_tstamp
                          for k, i in arrival_t
                          if i == self.vehicles_dic[k]
                          .get_pos()
                          .get_id()), "ARRI_AT_ORIGIN")

            start_end_nodes = list(self.starting_locations)

            print("    # LOAD_DEPOT_0")
            m.addConstrs((load[c, k, i] == 0
                          for c, k, i in self.valid_loads
                          if i in start_end_nodes), "LOAD_DEPOT_0")

            #### OPTIMIZE MODEL ###############################################
            print("Setting fares of lockers...")
            fare_locker_dis = self.DAO.get_fare_locker_dis()
            fare_locker = self.DAO.get_fare_locker()

            print("Setting Objective function...")
            # OBJECTIVE FUNCTION 1 - INCREASE PROFIT
            # B: fare_locker[c] = fixed fare to deliver commodity c
            # Y: fare_locker_km[c] = variable fare (according to distance)
            #                        to deliver commodity c
            # C_ij: cost_in_s[i,j] = travel time(s) to go from i to j
            # Function = (B + Y*C_kij)*X_kij
            
            mode_info = config.vehicle_instances["MODE_INFO"]
            m.setObjective(-quicksum(self.vehicles_dic[k].acquisition_cost
                             * ride[k, self.vehicles_dic[k].get_pos().get_id(), j]
                         for k in self.vehicles_dic
                         for j in self.nodes
                         if (k, self.vehicles_dic[k].get_pos().get_id(), j) in self.valid_rides)
                    + quicksum(d * (fare_locker[c]
                              + fare_locker_dis[c]
                              * self.cost_in_s[i, j, self.vehicles_dic[k].get_type()])
                         * ride[k, i, j]
                         for k in self.vehicles_dic
                         for i, j in self.pd_pairs.items()
                         if (k, i) in valid_visits and (k, j) in valid_visits
                         for c, d in self.nodes_dic[i].get_demand_short().items())
                - quicksum(self.vehicles_dic[k].operation_cost_s
                           *self.cost_in_s[i, j, self.vehicles_dic[k].get_type()]
                           * ride[k, i, j]
                           for k, i, j in self.valid_rides),
                GRB.MAXIMIZE)

            """
            -quicksum(mode_info[self.vehicles_dic[k].get_type()]["fixed_cost"]
                             * ride[k, self.vehicles_dic[k].get_pos().get_id(), j]
                         for k in self.vehicles_dic
                         for j in self.nodes
                         if (k, self.vehicles_dic[k].get_pos().get_id(), j) in self.valid_rides)
            """
            logger.debug(
                "########################## COSTS #################################")
            for k, i, j in self.valid_rides:
                logger.debug("(%s) %s -> %s COST: %.4f (%.4f$/s * %ss)",
                             k,
                             i,
                             j,
                             self.vehicles_dic[k].operation_cost_s *
                             self.cost_in_s[i, j,
                                            self.vehicles_dic[k].get_type()],
                             self.vehicles_dic[k].operation_cost_s,
                             self.cost_in_s[i, j, self.vehicles_dic[k].get_type()])

            # DISCOUNT
            # Ride time of request i (minus service time (embarking
            # /disembarking)) served by vehicle k over the minimum
            # time spent to go travel from i to j

            # Setup time limit
            m.Params.timeLimit=self.TIME_LIMIT
            preprocessing_t = (datetime.now() - t1).seconds
            print("Optimizing...")
            # Optimize model
            m.optimize()
            print("Preprocessing:", preprocessing_t)
            print("Model runtime:", m.Runtime)

            #### SHOW RESULTS #################################################
            # m.update()
            
            # Store route per vehicle

            # Model is unbounded
            if m.status == GRB.Status.UNBOUNDED:
                print('The model cannot be solved because it is unbounded')
                raise
                #exit(0)

            # If status is optimal
            elif m.status == GRB.Status.OPTIMAL or m.status == GRB.Status.TIME_LIMIT:
                if m.status == GRB.Status.TIME_LIMIT:
                    print("TIME LIMIT (%d s) RECHEADED." % (self.TIME_LIMIT))


                # Get binary variables Xkij
                var_ride = m.getAttr('x', ride)

                # Get travel self.times of each request
                var_travel_t = m.getAttr('x', travel_t)

                # Get load of vehicle at each point
                var_load = m.getAttr('x', load)

                # Get arrival time at each point
                var_arrival_t = m.getAttr('x', arrival_t)

                # Convert loads to integer
                for k in var_load.keys():
                    var_load[k] = int(var_load[k])
                    
                print("REQUEST DICTIONARY")
                pprint.pprint(self.request_dic)
                print("ALL:", [r.get_id() for r in self.request_dic.values()])


                 ###################################################################

                # MODEL ATTRIBUTES
                # http://www.gurobi.com/documentation/7.5/refman/model_attributes.html
                # BEST PRACTICES
                # http://www.gurobi.com/pdfs/user-events/2016-frankfurt/Best-Practices.pdf
                # http://www.dcc.fc.up.pt/~jpp/seminars/azores/gurobi-intro.pdf
                solver_sol={
                    "gap": m.MIPGap,
                    "num_vars": m.NumVars,
                    "num_constrs": m.NumConstrs,
                    "obj_bound": m.ObjBound,
                    "obj_val": m.ObjVal,
                    "node_count": m.NodeCount,
                    "sol_count": m.SolCount,
                    "iter_count": m.IterCount,
                    "runtime": m.Runtime,
                    "preprocessing_t": preprocessing_t
                }

                
                # Create DARP answer
                darp_answer = Response(self.vehicles,
                                       self.request_dic,
                                       self.arcs,
                                       self.valid_rides,
                                       var_ride,
                                       var_travel_t,
                                       var_load,
                                       var_arrival_t,
                                       self.DAO,
                                       solver_sol
                                       )
                # Return answer
                self.response=darp_answer
                print("RESPONSE:", solver_sol)
                # exit(0)
                m.write("debug.lp")

            elif m.status == GRB.Status.INFEASIBLE:
                print('Model is infeasible.')
                # raise Exception('Model is infeasible.') 
                # exit(0)

            elif m.status != GRB.Status.INF_OR_UNBD and m.status != GRB.Status.INFEASIBLE:
                print('Optimization was stopped with status %d' % m.status)
                # raise Exception('Model is infeasible.') 
                #exit(0)

            # IRREDUCIBLE INCONSISTENT SUBSYSTEM (IIS).
            # An IIS is a subset of the constraints and variable bounds
            # of the original model. If all constraints in the model
            # except those in the IIS are removed, the model is still
            # infeasible. However, further removing any one member
            # of the IIS produces a feasible result.
            # do IIS

            """print('The model is infeasible; computing IIS')
            removed = []

            # Loop until we reduce to a model that can be solved
            while True:

                m.computeIIS()
                print('\nThe following constraint cannot be satisfied:')
                for c in m.getConstrs():
                    if c.IISConstr:
                        print('%s' % c.constrName)
                        # Remove a single constraint from the model
                        removed.append(str(c.constrName))
                        m.remove(c)
                        break
                print('')

                m.optimize()
                status = m.status

                if status == GRB.Status.UNBOUNDED:
                    print('The model cannot be solved because it is unbounded')
                    exit(0)
                if status == GRB.Status.OPTIMAL:
                    break
                if status != GRB.Status.INF_OR_UNBD and status != GRB.Status.INFEASIBLE:
                    print('Optimization was stopped with status %d' % status)
                    exit(0)

            print('\nThe following constraints were removed to get a feasible LP:')
            print(removed)
            """
            """
            # MODEL RELAXATION
            # Relax the constraints to make the model feasible
            print('The model is infeasible; relaxing the constraints')
            orignumvars = m.NumVars
            m.feasRelaxS(0, False, False, True)
            m.optimize()
            status = m.status
            if status in (GRB.Status.INF_OR_UNBD, GRB.Status.INFEASIBLE, GRB.Status.UNBOUNDED):
                print('The relaxed model cannot be solved \
                    because it is infeasible or unbounded')
                exit(1)

            if status != GRB.Status.OPTIMAL:
                print('Optimization was stopped with status %d' % status)
                exit(1)

            print('\nSlack values:')
            slacks = m.getVars()[orignumvars:]
            for sv in slacks:
                if sv.X > 1e-6:
                    print('%s = %g' % (sv.VarName, sv.X))
            """
            

        except GurobiError:
            print('Error reported:', GurobiError.message)
            raise
        finally:
            # Reset indices of nodes
            Node.reset_nodes_ids()
            Vehicle.reset_vehicles_ids()

    ##########################################################################
    ##########################################################################
    ##########################################################################
