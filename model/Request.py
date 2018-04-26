from model.Coordinate import Coordinate
from model.Node import *
from collections import defaultdict
import time
import logging
logger = logging.getLogger(__name__)


class Request(object):

    parcel_lockers = set(['XS', 'S', 'M', 'L', 'XL'])
    seats = set(['A', 'C', 'B', 'I'])

    def __init__(self,
                id,
                x_origin,
                y_origin,
                x_destination,
                y_destination,
                revealing,
                demand,
                pickup_delay,
                delivery_delay,
                id_origin_node=None,
                id_destination_node=None,
                service_level = None):
        print(id_origin_node, id_destination_node, service_level)
        # Invert the demand for destination nodes, ex.: from(p1:1, p2:2) and to(p1:-1, p2:-2)
        destination_demand = {id: -demand[id] for id in demand.keys()}
        
        self.originNode = Node.factory_node('PK',
                                    None,
                                    x_origin,
                                    y_origin,
                                    demand,
                                    id,
                                    network_node_id = id_origin_node)
        self.destinationNode = Node.factory_node('DL',
                                    None,
                                    x_destination,
                                    y_destination,
                                    destination_demand,
                                    id,
                                    network_node_id = id_destination_node)
        self.id = id
        print("REQUEST id:", self.id)
        self.revealing = revealing  # use revealing.timestamp() to get an integer
        self.demand = demand
        self.pickup_delay = pickup_delay
        self.delivery_delay = delivery_delay
        self.service_level = service_level
        self.ett = -1
        # Dictionary of OD distances per mode
        self.ett_dic_node = None
        self.embarking_t = 0
        self.disembarking_t = 0
        # Check if request features only objects - i.e., allowed to wait longer
        self.live_stock = False
        # Accounts for the case in which a group of people book a vehicle but also book compartments
        if len(set(self.get_demand_short().keys()).intersection(Request.seats))>0:
            self.live_stock = True
        self.originNode.set_is_live_stock(self.live_stock)
        self.destinationNode.set_is_live_stock(self.live_stock)
        self.reset()

    def get_embarking_t(self):
        return self.embarking_t

    def get_disembarking_t(self):
        return self.disembarking_t

    def reset(self):
        self.fare = defaultdict(float)
        self.vehicle_scheduled_id = None
        self.arrival_t = -1
        self.total_travel_time = -1
        self.originNode.reset()
        self.destinationNode.reset()

    # Update status of request after reading response from Solver
    def update_status(self, vehicle_scheduled_id, total_travel_time, arrival_t):
        #print("Updating status", self.id, vehicle_scheduled_id, self.originNode)
        self.vehicle_scheduled_id = vehicle_scheduled_id
        self.total_travel_time = total_travel_time  # Not considering boarding delay
        self.arrival_t = arrival_t
        self.detour_ratio = self.get_detour_ratio()

    def print_status(self):
        print(self.id, "---",
              self.vehicle_scheduled_id,
              self.originNode.id,
              Node.get_formatted_time_h(self.arrival_t),
              self.destinationNode.id,
              Node.get_formatted_time_h(
                  self.arrival_t + self.total_travel_time),
              self.total_travel_time,
              self.detour_ratio)

    def get_pk_time(self):
        return self.originNode.arrival_t

    def get_dl_time(self):
        return self.destinationNode.arrival_t

    def get_distance(self, DAO, type_v=False):
        """ Return dictionary of distances from origin destinaton.
        E.g.: {"autonomous":"45, "dual":34}
        
        Arguments:
            DAO  -- Source of distances
        
        Returns:
            dictionary -- If vehicle was not assigned.
            distance -- Related to type of vehicle assigned (A, C, D).
        """
        dist = DAO.get_distance_from_to(self.originNode.id, self.destinationNode.id)
        if type_v and self.get_vehicle_scheduled_id():
            return dist[DAO.vehicle_dic[self.get_vehicle_scheduled_id()].type_vehicle]
        else:
            return dist

    def get_fare(self, mode=None):
        if mode == None:
            return self.fare
        return self.fare[mode]

    # Define fare from model.Request origin to destination (sum of individual
    # compartment's fares composing the request)
    # Composition: fixed_fare + var_fare * total_dis
    def calculate_fare_dual(self, DAO):
        self.ett_dic_node = self.get_distance(DAO)

        for c in self.demand.keys():
            if self.demand[c] > 0:
                fare_c_fixed = DAO.fare_locker[c]
                fare_c_km = DAO.fare_locker_dis[c]

                for m in self.ett_dic_node.keys():
                    self.fare[m] += self.demand[c]*(fare_c_fixed + self.ett_dic_node[m] * fare_c_km)

    # Calculate service time of embarking/disembarking all requests
    def calculate_embark_disembark_t(self, DAO):
        for c in self.demand.keys():
            if self.demand[c] > 0:
                self.embarking_t += self.demand[c] * \
                    DAO.locker_embarking_t[c]
                self.disembarking_t += self.demand[c] * \
                    DAO.locker_disembarking_t[c]
        # Set values of service time in nodes
        self.originNode.service_t = self.embarking_t
        self.destinationNode.service_t = self.disembarking_t

    def get_distance_clock(self, DAO):
        return self.destinationNode.arrival_t - self.originNode.arrival_t

    def get_eta(self):
        return self.originNode.arrival_t - self.get_revealing_tstamp()

    def get_travel_delay(self, DAO):
        return self.get_distance_clock(DAO) - self.get_distance(DAO, type_v=True)

    def get_revealing_tstamp(self):
        return int(time.mktime(self.revealing.timetuple()))

    def is_live_stock(self):
        return self.live_stock

    def get_origin(self):
        return self.originNode

    def get_destination(self):
        return self.destinationNode

    def get_revealing(self):
        return self.revealing

    def get_revealing_total(self):
        return self.revealing

    def get_demand(self):
        return self.demand

    def get_pickup_delay(self):
        return self.pickup_delay

    def get_delivery_delay(self):
        return self.delivery_delay

    def get_vehicle_scheduled_id(self):
        return self.vehicle_scheduled_id

    # Remove demands = 0
    def get_demand_short(self):
        return {id: int(self.demand[id]) for id in self.demand.keys() if int(self.demand[id]) != 0}


    def get_detour_ratio(self):
        # Only the livestock benefits from detour discount
        if self.is_attended() and self.live_stock:
            #print("##detour:", self.total_travel_time, self.ett)
            return (self.total_travel_time) / self.ett - 1
        return 0

    def is_attended(self):
        return self.originNode.is_visited()

    def __str__(self):
        s = ""
        s + '########' + self.id + '########\n'
        if not self.originNode.is_visited():
            s += self.id+': Impossible to attend.'
        else:
            s += str(self.originNode) + '\n'
            s += str(self.destinationNode) + '\n '
            s += 'Revealing: '
            s += str(self.revealing)
        return s

    def __repr__(self):
        return self.id \
            + ' <' + str(self.get_revealing().strftime('%H:%M')) + '>' \
              + ' ### '\
              + str(self.originNode.id) +'('+ self.originNode.network_node_id +') -> '\
              + str(self.destinationNode.id) +'('+ self.destinationNode.network_node_id +')'\
              + str(" ||" + ", ".join(["[{0}=${1:.2f}]".format(m, self.fare[m]) for m in self.fare.keys()]) + "||") \
              + ("(LSTOCK)" if self.live_stock else "(PARCEL)")\
              + "/".join(['{0:>3}={1:<2}'.format(k, v) for k, v in self.get_demand_short().items()]) \
              + (" || DL DELAY: " + str(self.delivery_delay) if self.delivery_delay != None else "") \
              + (" || PK DELAY: " + str(self.pickup_delay) if self.pickup_delay != None else "") \
              + (" || SL: " + str(self.service_level))
              #return "{1} <{2}> ### {3}({4}) -> {5}({6}) || {7:2f} || ({8}) || DL DELAY: {9} || PK DELAY: {10} || SL: {11}".format()
        

    def get_json(self):
        json = '{{"id":"{10}",\
                  "revealing_t": "{0}", \
                  "origin_node":{1}, \
                  "destination_node":{2}, \
                  "is_passenger":{3}, \
                  "pk_delay":{4}, \
                  "dl_delay":{5}, \
                  "fare":{6}, \
                  "embarking_t":{7}, \
                  "disembarking_t":{8}, \
                  "detour_ratio":{9}}}'\
                  .format(
            Node.get_formatted_time(self.get_revealing().timestamp()),
            self.originNode.get_json_leg_node(),
            self.destinationNode.get_json_leg_node(),
            str(self.live_stock).lower(),
            (self.get_pickup_delay() if self.get_pickup_delay() is not None else "null"),
            (self.get_delivery_delay()
             if self.get_delivery_delay() is not None else "null"),
            self.get_fare(),
            self.get_embarking_t(),
            self.get_disembarking_t(),
            self.get_detour_ratio(),
            self.id)
        return json