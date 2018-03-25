from Node import *
from DaoHybrid import *
import pprint
import collections
import json
import logging
logger = logging.getLogger("main.opt_method.response")

class Response(object):

    # VARIABLES [K,I,J] COMING FROM GUROBI OPTIMIZATION
    # var_ride = binary variables Xkij
    # var_travel_t = Get travel self.times of each request
    # var_load = Get load of vehicle at each point
    # arrival_t = Get arrival time at each point

    def __init__(self,
                 vehicles,
                 requests_dic,
                 arcs,
                 vars,
                 rides,
                 travel_t,
                 load,
                 arrival_t,
                 selected_req,
                 DAO,
                 solver_sol):
        self.vehicles = vehicles
        self.requests_dic = requests_dic
        self.profit = solver_sol["obj_val"]
        self.solver_sol = solver_sol
        self.DAO = DAO
        self.arcs = arcs
        self.vars = vars
        self.rides = rides
        self.travel_t = travel_t
        self.selected_req = selected_req
        self.load = load
        self.arrival_t = {(k,i):arrival_t[(k,i)] + Vehicle.start_revealing_tstamp for k,i in arrival_t}
        self.path = None
        # Profit accrued by requests
        self.profit_reqs = 0
        self.overall_detour_discount = 0
        self.all_requests = set([r.get_id()
                                 for r in self.requests_dic.values()])

        # Check rides[k, i, j] and create vehicles and nodes
        self.create_path()

        self.attended_requests = {pk_node.get_request_id():self.requests_dic[pk_node.get_id()] 
                                  for pk_node in self.DAO.get_nodes_dic().values()
                                  if pk_node.get_id() in self.selected_req}

        
        self.denied_requests = self.all_requests - self.attended_requests.keys()

        self.calculate_total_profit()
        
        self.setup_routing_info()

    def calculate_overall_detour_discount(self):
        for r in self.requests_dic.values():
            self.overall_detour_discount += self.DAO.get_discount_passenger() * \
                r.get_detour_ratio()

    # Creates a response for a method, placing the step-by-step information
    # in each node.
    def create_path(self):
        vehicles_dic = self.DAO.get_vehicle_dic()
        v_dic = dict()
        dic_order = dict()

        for k in self.DAO.get_vehicle_dic().keys():
            dic_order[k] = dict()

        logger.info("SELECTED REQUESTS: %s", str(self.selected_req.keys()))

        for k, i, j in self.vars:
            
            # If there is a path from i to j by vehicle k
            # WARNING - FLOATING POINT ERROR IN GUROBI
            """
            This can happen due to feasibility and integrality tolerances.
            You will also find that solution that Gurobi (as all floating-
            point based MIP solvers) provides may slightly violate your 
            constraints. 

            The reason is that floating-point numeric as implemented in 
            the CPU hardware is not exact. Rounding errors can (and 
            usually will) happen. As a consequence, MIP solvers use 
            tolerances within which a solution is still considered to be 
            correct. The default tolerance for integrality in Gurobi 
            is 1e-5, the default feasibility tolerance is 1e-6. This means 
            that Gurobi is allowed to consider a value that is at most 
            1e-5 away from an integer to still be integral, and it is 
            allowed to consider a constraint that is violated by at most
            1e-6 to still be satisfied.
            """
            if self.rides[k, i, j] > 0.9:
                
                # Departure node
                vehicle = vehicles_dic[k]
                path = vehicle.get_path_arrival()

                dep_node = self.DAO.get_nodes_dic()[i]
                arr_node = self.DAO.get_nodes_dic()[j]


                arr_i = self.arrival_t[k, i]
                arr_j = self.arrival_t[k, j]
                # print("--#####",k,i,j, self.rides[k, i, j], self.arrival_t[k, i],  arr_i, self.arrival_t[k, j],  arr_j)

                if arr_i not in path:
                    path[arr_i] = self.get_updated_node2(vehicle, dep_node)
                    vehicle.add_node(path[arr_i])
                
                if arr_j not in path:
                    path[arr_j] = self.get_updated_node2(vehicle, arr_node)
                    vehicle.add_node(path[arr_j])

                if isinstance(dep_node, NodePK):
                    req = self.DAO.get_request_dic()[i]
                    req.update_status(vehicle.get_id(), self.travel_t[k, i], arr_i)

    def calculate_total_profit(self):
        for r in self.attended_requests.values():
            print("R:", r, " --S:", r.get_vehicle_scheduled_id())
            vehicle_mode = self.DAO.get_vehicle_dic()[r.get_vehicle_scheduled_id()].get_type()
            self.profit_reqs += r.get_fare(mode=vehicle_mode)

    def print_requests_info(self):
        # Calculate overall detour discount
        self.calculate_overall_detour_discount()

        mix = defaultdict(int)
        mix_v = defaultdict(set)
        # Print requests ordered by pk time
        for r in self.attended_requests.values():

            #Get type of vehicle that attended the request
            type_v = self.DAO.get_vehicle_dic()[r.get_vehicle_scheduled_id()].get_type()
            mix[type_v] = mix[type_v] + 1
            mix_v[self.DAO.get_vehicle_dic()[r.get_vehicle_scheduled_id()].get_type()].add(r.get_vehicle_scheduled_id())
            
            
            print("### %r ### (RE: %r -> PK: %r -> DL: %r) ETA: %r || TRAVEL TIME: %r || DELAY: %r || FARE: $%.2f || DISCOUNT: $%.2f || VEHICLE: %r" %
                  (r.get_id(),
                   Node.get_formatted_time(r.get_revealing_tstamp()),
                   Node.get_formatted_time_h(r.get_pk_time()),
                   Node.get_formatted_time_h(r.get_dl_time()),
                   Node.get_formatted_duration_h(r.get_eta()),
                   Node.get_formatted_duration_h(r.get_distance(self.DAO)[type_v]),
                   Node.get_formatted_duration_h(r.get_travel_delay(self.DAO)),
                   r.get_fare(mode=type_v),
                   self.DAO.get_discount_passenger() * r.get_detour_ratio(),
                   r.get_vehicle_scheduled_id()))

            logger.info("### %r ### (RE: %r -> PK: %r -> DL: %r) ETA: %r || TRAVEL TIME: %r || DELAY: %r || FARE: $%.2f || DISCOUNT: $%.2f || VEHICLE: %r" ,
                  r.get_id(),
                   Node.get_formatted_time(r.get_revealing_tstamp()),
                   Node.get_formatted_time_h(r.get_pk_time()),
                   Node.get_formatted_time_h(r.get_dl_time()),
                   Node.get_formatted_duration_h(r.get_eta()),
                   Node.get_formatted_duration_h(r.get_distance(self.DAO)[type_v]),
                   Node.get_formatted_duration_h(r.get_travel_delay(self.DAO)),
                   r.get_fare(mode=type_v),
                   self.DAO.get_discount_passenger() * r.get_detour_ratio(),
                   r.get_vehicle_scheduled_id())
        
        print(self.route_v)
        logger.info(self.route_v)
        print("-------------------------------------------------------------------------------------------------------------------------------------------------")
        print("OVERALL OCCUPANCY: %.2f || OPERATING VEHICLES: %d (%s) || PROFIT: %.2f =  %.2f (REQUESTS REVENUE) -  %.2f (OPERATIONAL COSTS) - %.2f (DETOUR DISCOUNT)" %
              (self.overall_occupancy_v,
               self.n_vehicles,
               "/".join([k + " = " + str(len(v)) for k,v in mix_v.items()]),
               round(float(self.profit), 2),
               self.profit_reqs,
               self.overall_operational_cost,
               self.overall_detour_discount
               ))
        print("--------------------------------------------------------------------------------------------------------------------------------------------------")
        logger.info("-------------------------------------------------------------------------------------------------------------------------------------------------")
        logger.info("OVERALL OCCUPANCY: %.2f || OPERATING VEHICLES: %d || PROFIT: %.2f =  %.2f (REQUESTS REVENUE) -  %.2f (OPERATIONAL COSTS) - %.2f (DETOUR DISCOUNT)",
              self.overall_occupancy_v,
               self.n_vehicles,
               round(float(self.profit), 2),
               self.profit_reqs,
               self.overall_operational_cost,
               self.overall_detour_discount
               )
        logger.info("--------------------------------------------------------------------------------------------------------------------------------------------------")
        print("--------------------------------------------------------------------------------------------------------------------------------------------------")

    def get_json(self):
        js = '{{"config":{{\
                            "cost_per_s":{0},\
                            "discount_passenger_s":{1},\
                            "compartment_data":{8}\
                            }},\
                    "nodes":[{2}], \
                    "requests":[{3}], \
                    "vehicles":[{4}], \
                    "result_summary":{{\
                            "attended_requests":[{5}],\
                            "all_requests":[{6}],\
                            "denied_requests":[{7}],\
                            "overall_occupancy":{9},\
                            "operating_vehicles":{10},\
                            "profit":{11},\
                            "profit_comp":{{\
                                "requests_revenue":{12},\
                                "operational_costs":{13},\
                                "detour_discount":{14}\
                            }},\
                            "mip_solution":{{\
                                "gap": {15},\
                                "num_vars": {16},\
                                "num_constrs": {17},\
                                "obj_bound": {18},\
                                "obj_val": {19},\
                                "node_count": {20},\
                                "sol_count": {21},\
                                "iter_count": {22},\
                                "runtime": {23}\
                            }}\
                    }}\
                }}'\
        .format(self.DAO.get_cost_per_s(),
                self.DAO.get_discount_passenger(),
                ",".join(n.get_json() for n in self.DAO.get_nodes_dic().values()),
                ",".join(r.get_json() for r in self.DAO.get_request_list()),
                ",".join(v.get_json() for v in self.DAO.get_vehicle_dic().values() if v.is_used()),
                ",".join('"' + v + '"' for v in self.attended_requests),
                ",".join('"' + v + '"' for v in self.all_requests),
                ",".join('"' + v + '"' for v in self.denied_requests),
                self.DAO.get_json_compartment_data(),
                self.overall_occupancy_v,
                self.n_vehicles,
                round(float(self.profit), 2),
                self.profit_reqs,
                self.overall_operational_cost,
                self.overall_detour_discount,
                self.solver_sol["gap"],
                self.solver_sol["num_vars"],
                self.solver_sol["num_constrs"],
                self.solver_sol["obj_bound"],
                self.solver_sol["obj_val"],
                self.solver_sol["node_count"],
                self.solver_sol["sol_count"],
                self.solver_sol["iter_count"],
                self.solver_sol["runtime"])
        return js
    
    def get_profit_reqs(self):
        return self.profit_reqs
    
    def get_solver_sol(self):
        return self.solver_sol

    def get_all_requests(self):
        return self.all_requests
    
    def get_denied_requests(self):
        return self.denied_requests
    
    def get_attended_requests(self):
        return self.attended_requests

    def get_overall_occupancy_v(self):
        return self.overall_occupancy_v

    def get_n_vehicles(self):
        return self.n_vehicles

    def get_profit(self):
        return self.profit

    def get_profit_reqs(self):
        return self.profit_reqs

    def get_overall_operational_cost(self):
        return self.overall_operational_cost
    
    def get_overall_detour_discount(self):
        return self.overall_detour_discount

    # Print the route within each vehicle and all routes statistics
    def setup_routing_info(self):

        self.route_v = ""
        self.overall_occupancy = 0
        self.n_vehicles = 0
        self.overall_operational_cost = 0
        self.overall_detour_discount = 0

        # For each vehicle ID
        for k in self.vehicles:
            v = self.DAO.get_vehicle_dic()[k]

            # If vehicle v is used
            if v.is_used():
                # Create vehicle occupancy statistics per compartment
                # in relation to operational time (travel time between points)
                # using DAO data
                v.calculate_vehicle_occupancy(self.DAO)

                # Sum individual overall occupancy of each vehicle (route)
                self.overall_occupancy += v.get_overall_avg_occupancy()

                self.overall_operational_cost += v.get_operational_cost()
                # Increment number of active vehicles
                self.n_vehicles += 1
                self.route_v += str(v)

        self.overall_occupancy_v = (self.overall_occupancy * 100 / self.n_vehicles if self.n_vehicles > 0 else 0)

    # Return a copy of the node with load and arrival values
    # updated. This way, every vehicle has a copy of the
    # departure and arrival nodes.
    def get_updated_node(self, vehicle, node, next):
        node_copy = None
        # Depots don't need to be copied
        if not isinstance(node, NodeDepot):
            node_copy = node
        else:
            node_copy = Node.copy_node(node)
            
        arrival = self.arrival_t[vehicle.get_id(), node_copy.get_id()]
        node_copy.set_arrival_t(arrival)
        node_copy.set_vehicle(vehicle)
        node_copy.set_id_next(next)
        for c in vehicle.get_capacity().keys():
            node_copy.get_load()[c] = self.load[c,
                                                vehicle.get_id(),
                                                node_copy.get_id()]
        return node_copy


    # Return a copy of the node with load and arrival values
    # updated. This way, every vehicle has a copy of the
    # departure and arrival nodes.
    def get_updated_node2(self, vehicle, node):
        node_copy = None
        # Depots don't need to be copied
        if not isinstance(node, NodeDepot):
            node_copy = node
        else:
            node_copy = Node.copy_node(node)
        arrival = self.arrival_t[vehicle.get_id(), node_copy.get_id()]
        node_copy.set_arrival_t(arrival)
        node_copy.set_vehicle(vehicle)
        for c in vehicle.get_capacity().keys():
            node_copy.get_load()[c] = self.load[c,
                                                vehicle.get_id(),
                                                node_copy.get_id()]
        return node_copy
