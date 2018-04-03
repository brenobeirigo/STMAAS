import random
from Node import *
import pprint
from datetime import datetime, date, time, timedelta
import collections
from Leg import Leg
from Route import Route
import json
import time
from collections import OrderedDict
class Vehicle:
    vehicle_modes = ["autonomous", "conventional", "dual"]
    
    start_revealing = '2017-10-10 00:00:00'
    start_revealing_t = datetime.strptime('2017-10-10 00:00:00', '%Y-%m-%d %H:%M:%S')
    start_revealing_tstamp = start_revealing_t.timestamp()

    color = {}
    color[0] = "(60, 180, 75)"
    color[1] = "(255, 225, 25)"
    color[2] = "(0, 130, 200)"
    color[3] = "(245, 130, 48)"
    color[4] = "(145, 30, 180)"
    color[5] = "(70, 240, 240)"
    color[6] = "(240, 50, 230)"
    color[7] = "(210, 245, 60)"
    color[8] = "(250, 190, 190)"
    color[9] = "(0, 128, 128)"
    color[10] = "(230, 190, 255)"
    color[11] = "(170, 110, 40)"
    color[12] = "(255, 250, 200)"
    color[13] = "(128, 0, 0)"
    color[14] = "(170, 255, 195)"
    color[15] = "(128, 128, 0)"
    color[16] = "(255, 215, 180)"
    color[17] = "(0, 0, 128)"
    color[18] = "(128, 128, 128)"
    color[19] = "(255, 255, 255)"
    color[20] = "(0, 0, 0)"

    n_vehicles = 0

    @classmethod
    def reset_vehicles_ids(cls):
        cls.n_vehicles = 0

    def get_type(self):
        return self.type_vehicle

    def __init__(self, id, autonomy, pos, capacity, available_at, type_vehicle=None, acquisition_cost=0, operation_cost_s=0):
        self.type_vehicle = type_vehicle
        self.color = Vehicle.color[Vehicle.n_vehicles % 21]
        self.id = id

        # Establish the costs
        self.acquisition_cost = acquisition_cost
        self.operation_cost_s = operation_cost_s

        
        # Autonomy of vehicle
        self.autonomy = autonomy

        # Initial position vehicle
        self.pos = pos

        # Time when vehicle is available
        self.available_at = datetime.strptime(available_at, '%Y-%m-%d %H:%M').timestamp()

        # Set time when vehicle is available in node vehicle is located
        self.pos.set_arrival_t(self.available_at)

        # Capacity of vehicles (compartments available != 0)
        self.capacity = {k: capacity[k] for k in capacity if capacity[k] != 0}

        # Color of vehicle path
        self.color = str("#%06x" % random.randint(0, 0xFFFFFF))
        self.reset()
        Vehicle.n_vehicles += 1

    def get_operational_cost(self):
        return self.operational_cost
        
    def get_color(self):
        return self.color

    
    def reset(self):
        
        # Average occupancy of vehicle's compartments in relation
        # to travel_time
        self.avg_occupancy_c = {}
        # Overall average occupancy of vehicle considering all
        # compartments throughout the entire travel time
        self.overall_avg_occupancy = 0
        self.operational_cost = 0
        # If requests origin == vehicle origin, departure time, there are two
        # nodes (DP and PK) related to the same key (00:00), since vehicle does
        # not need to travel to arrive in PK. Hence, the key 00:00 will carry a set
        # of nodes to cover this special case.
        self.path = OrderedDict()
        average_occupation = {
            k: 0 for k in self.capacity if self.capacity[k] != 0}
        self.route = None

    # Check if vehicle is used
    # Case positive -> path > 2 (depot nodes)
    def is_used(self):
        # Don't show not used vehicles
        if len(self.path.keys()) <= 2:
            return False
        return True

    
    # Return TRUE if vehicle can fully attend request
    def fit_demand(self, request):
        demand = request.get_demand_short()
        # If vehicle can a accommodate demand
        if set(demand.keys()).issubset(set(self.get_capacity.keys())):
            # A vehicle only visits nodes that it can FULLY attend, i.e.,
            # if node demand is greater than node capacity, vehicle will not
            # visit a node.

            # Test if node demand > vehicle capacity for departure node
            for d in demand.keys():
                if demand[d] > veh_capacity[d]:
                    return False

            # Test if node demand > vehicle capacity for arrival node
            for dj in demand_j.keys():
                if abs(demand_j[dj]) > this.get_capacity[dj]:
                    return False
            return True
        return False

    def is_feasible(self, request):
        return None
    # - Check if vehicle compartments match with request compartments
    # - Check if there is enough space to accomodate the requested amount
    # for each compartment.
    # - Check if the dislocation time from vehicle's current position to
    # request's position (passing throughout all the previous requests) is
    # lower than the earliest pick-up time.
    # - Check if the dislocation time from vehicle's pickup position to
    # request's delivery position (passing throughout all the previous
    # requests) is lower than the latest delivery time.
    # - Check the impact of deviating from the original path to pick-up
    # a customer. What is the impact on the other customers? How the penalty
    # will affect the profits?
    # Autonomy in hours

    def get_overall_avg_occupancy(self):
        return self.overall_avg_occupancy

    def get_id(self):
        return self.id

    def get_autonomy(self):
        return self.autonomy

    def get_color(self):
        return self.color

    def add_node(self, node):
        self.path[node.get_id()] = node

    def get_pos(self):
        return self.pos

    def get_capacity(self):
        return self.capacity

    def get_path(self):
        return self.path

    def set_path(self, path):
        self.path = path

    def __str__(self):
        current_node = self.pos.get_id()
        print(self.path.keys())
        s = '#' + self.get_id() + ':\n'
        while current_node in self.path.keys():
            next_node = self.path[current_node].get_id_next()
            s += str(current_node) + ' -> ' + str(next_node)\
                + ': ' + str(self.path[current_node]) + '\n'
            current_node = next_node
        return s

    def __repr__(self):
        current_node = self.pos.get_id()
        print(self.path.keys())
        s = '#' + self.get_id() + ':\n'
        while current_node in self.path.keys():
            next_node = self.path[current_node].get_id_next()
            s += str(current_node) + ' -> ' + str(next_node)\
                + ': ' + str(self.path[current_node]) + '\n'
            current_node = next_node
        return s

    def get_available_at(self):
        return self.available_at
    
    def get_available_at_tstamp(self):
        return self.available_at
    
    def get_attended_requests(self):
        return self.route.get_request_list()

    # Calculate vehicle proportional occupancy of each compartment
    # by time ridden
    def calculate_vehicle_occupancy(self, DAO):

        ############### VEHICLE ROUTE OCCUPANCY ####################

        self.route = Route(DAO, self.path, self.pos)

        # Get vehicle's capacity
        capacity_vehicle = self.get_capacity()

        # for i in range(0, len(list_nodes) - 1):
        for leg in self.route.get_legs_dic().values():

            # Starting node (origin)
            origin = leg.get_origin()

            # Get the current (destination) node
            destination = leg.get_destination()


            # Distance disconsidering pk/dp service time
            dist = self.route.get_legs_dic()[(
                origin, destination)].get_travel_t()

            # Operational cost of leg
            leg_op_cost = self.operation_cost_s * dist

            # Add leg operational cost to the total cost
            self.operational_cost += leg_op_cost

            """print("&&&OC", origin, " -> ", destination, ":", Node.get_formatted_duration_h(dist),
                  self.operation_cost_s, leg_op_cost, self.operational_cost)"""

            origin_dest_delay = leg.get_invehicle_t()

            # Get the load departing from the origin node (after loading)
            load_origin = self.path[origin].get_load()
            load_destination = self.path[destination].get_load()

            # Proportional time of complete route rode from
            # origin to destination
            proportional_time = leg.get_proportional_t()

            # Log of occupation data for each compartment c of vehicle
            occupation_log_c = collections.OrderedDict()

            for c in capacity_vehicle.keys():
                # Determine how full a parcel locker c remained occupied
                # from origin to destination
                from_to_parcel_occup = load_origin[c] / capacity_vehicle[c]

                # Stores the truest occupation of the compartiment
                # in relation to the route total time
                partial_occupation = proportional_time * from_to_parcel_occup

                # If c not yet stored in the the average_occupation array
                if c not in self.avg_occupancy_c.keys():
                    self.avg_occupancy_c[c] = 0

                # Store the sum of all proportional occupation measures
                # for all parcel
                self.avg_occupancy_c[c] += partial_occupation

                # From origin to destination:
                # Compartment "c" is "from_to_parcel_occup" % occupied
                # what corresponds to "partial_occupation" % of the total route
                occupation_log_c[c] = from_to_parcel_occup

            # Remove not occupied compartments
            occupation_log_c = {
            c: occupation_log_c[c]
            for c in occupation_log_c.keys()
            if occupation_log_c[c] != 0}
            

            # Store leg occupation log
            leg.set_occupation_log_c(occupation_log_c)

            #print("LOAD_ORIGIN", load_origin, "OCC. Log:", occupation_log_c)

            self.route.get_legs_dic()[(
                origin, destination)].set_load_origin_dic(load_origin)

        # Filter compartments not occupied during the whole route
        # (avg_occupation = 0)
        self.avg_occupancy_c = {
            c: self.avg_occupancy_c[c]
            for c in self.avg_occupancy_c.keys()
        }
        #    if self.avg_occupancy_c[c] != 0}

        self.overall_avg_occupancy = sum(self.avg_occupancy_c.values()) / float(len(self.capacity))

        """print("\n TOTAL TIME:", self.route.get_total_invehicle_t(),
              "( travel times + service times from ORIGIN to DESTINATION)")"""

    def __repr__(self):
         # Get the list of nodes ordered by visitation order
        #list_nodes = self.route.get_ordered_route()

        # print("LIST NODES: ", list_nodes)

        # If vehicle is not used, its data is irrelevant and
        # therefore not shown
        # print("items:", self.capacity.items())
        js = '{'
        if not self.is_used():
            s = self.get_id() + ' - ' + self.get_type() + ' - (' + str(self.pos) +')' + ",still,"
            s += "-".join(['{0:>3}:{1:<3}'.format(k, v)
                           for k, v in self.capacity.items()])
            
            js += '"vehicle_id": "' + self.get_id() + '"'
            js += ', "vehicle_is_used": true'
            js += ', "vehicle_compartment_set":['
            js += ",".join(['{{"compartment_id":"{0}", "compartment_amount":{1}, "compartment_current_occupation": 0}}'.format(k, v)
                            for k, v in self.capacity.items()])
            js += ']}'
            return s

        s = '\n###### ' + self.get_id() + \
            ' ###############################################################'

        # Print route
        # e.g.:
        # H_006 - 12:45:00  |PK011| - LOAD: {'XL': 4}
        # H_006 - 12:48:21  |DL012| - LOAD: {}
        # H_007 - 12:48:35  |PK013| - LOAD: {'XL': 2}

        s += '\nCAPACITY: '
        for c in self.capacity:
            s += c + ":" + str(self.capacity[c]) + " / "
        s += "\nAVG. OCCUPANCY (COMPARTMENT): "
        for c in self.avg_occupancy_c:
            s += c + ":" + \
                str("%.4f" %
                    round(self.avg_occupancy_c[c] * 100, 2)) + "%" + " / "
        s += "\nOVERALL AVERAGE OCCUPANCY: " + \
            str("%.4f" % round(self.overall_avg_occupancy * 100, 2)) + "%" + "\n"
        s += "OPERATIONAL COSTS:  ${0:<2} ".format(self.operational_cost)

        s += str(self.route)

        """print("LOG LEGS")
        print(Leg.get_labels_line())
        for v in self.route.get_legs_dic().values():
            print(v)"""

        return str(s)

    def get_operational_cost(self):
        return self.operational_cost

    def __str__(self):
        # Get the list of nodes ordered by visitation order
        #list_nodes = self.route.get_ordered_route()

        # print("LIST NODES: ", list_nodes)

        # If vehicle is not used, its data is irrelevant and
        # therefore not shown
        if not self.is_used():
            s = "->" + self.get_id() +'('+str(self.pos)+')' + "-- STATUS: still"
            s += "->" + self.get_id() + "-- STATUS: still"
            s += "/".join(['{0:>3}={1:<2}'.format(k, v)
                           for k, v in self.capacity.items()])
            return s

        s = '\n---###### ' + self.get_id() + \
            ' ###############################################################'

        # Print route
        # e.g.:
        # H_006 - 12:45:00  |PK011| - LOAD: {'XL': 4}
        # H_006 - 12:48:21  |DL012| - LOAD: {}
        # H_007 - 12:48:35  |PK013| - LOAD: {'XL': 2}
        s += str(self.route)

        s += '\nCAPACITY: '
        for c in self.capacity:
            s += c + ":" + str(self.capacity[c]) + " / "
        s += "\nAVG. OCCUPANCY (COMPARTMENT): "
        for c in self.avg_occupancy_c:
            s += c + ":" + \
                str("%.4f" %
                    round(self.avg_occupancy_c[c] * 100, 2)) + "%" + " / "
        s += "\nOVERALL AVERAGE OCCUPANCY: " + \
            str("%.4f" % round(self.overall_avg_occupancy * 100, 2)) + "%" + "\n"
        s += "OPERATIONAL COSTS:  ${0:.2f} ".format(self.operational_cost)

        """print("LOG LEGS")
        print(Leg.get_labels_line())
        for v in self.route.get_legs_dic().values():
            print(v)"""
        return str(s)
    
    def get_json(self):
        print("COLOR:", self.get_color())
        js = '{'
        js += '"vehicle_id": "' + self.get_id() + '"'
        js += ', "vehicle_is_used":' + str(self.is_used()).lower()
        js += ', "vehicle_color": "' + self.get_color()+ '"'
        js += ', "available_at":"{0}"'.format(
            Node.get_formatted_time(self.get_available_at()))
        js += ', "lat":' + str(self.get_pos().get_coord().get_y())
        js += ', "lng":' + str(self.get_pos().get_coord().get_x())
        js += ', "autonomy":' + str(self.get_autonomy())
        js += ', "vehicle_compartment_set":['
        js += ",".join(['{{"compartment_id":"{0}", "compartment_amount":{1}, "compartment_avg_occupancy": {2}}}'.format(
            k, v, self.avg_occupancy_c[k]) for k, v in self.capacity.items()])
        js += ']'
        js += ', "vehicle_overall_avg_occupancy":{0}'.format(
            round(self.overall_avg_occupancy * 100, 2))
        js += ', "vehicle_operational_costs":{0}'.format(self.operational_cost)
        js += ', "vehicle_route":' + self.route.get_json()
        js += '}'
        return js
