from model.Leg import Leg
import collections
from model.Node import *
import pprint
import datetime
import logging
logger = logging.getLogger("main.opt_method.response.route")

class Route:
    def __init__(self, DAO, path, start_pos):
        self.request_list = []
        self.path = path
        self.DAO = DAO
        self.start_pos = start_pos
        
        logger.debug("#### Creating route - START: %s - PATH: %s", self.start_pos, self.path)
        # Ordered list of nodes from path
        self.ordered_list = list()
        self.legs_dic = self.create_legs_dic()

        # Total travel time between first PK and last DL
        # considering boarding times (duration_pk_dl in DAO)
        self.total_invehicle_t = 0
        # Clock time between first PK and last DL
        self.total_clock_t = 0

        for l in self.legs_dic.values():
                # if not isinstance(l.get_from_node(), NodeDepot) and not isinstance(l.get_to_node(), NodeDepot):
                # Total time (travel times + service time in each node)
                self.total_invehicle_t += l.get_invehicle_t()
                self.total_clock_t += l.get_clock_t()

        self.total_idle_t = self.total_clock_t - self.total_invehicle_t
        self.set_legs_proportional_time()

        
    def get_request_list(self):
        return self.request_list
    
    def create_legs_dic(self):
        # Vehicle journey according to clock results. Includes
        # the slack time that vehicle is not moving (includes boarding time)

        legs = collections.OrderedDict()

        # Print the ordered list of nodes
        origin_v = self.start_pos.get_id()
        vehicle = self.DAO.get_vehicles_nodes()[origin_v]
        self.ordered_list = list(vehicle.get_path().keys())

        # print("Ordered List")
        pprint.pprint(self.ordered_list)

        for i in range(0,len(self.ordered_list)-1):
            origin = vehicle.get_path()[self.ordered_list[i]]
            destination = vehicle.get_path()[self.ordered_list[i+1]]

            # Add the destinations request to request list. The requests list
            # contains all requests attended by vehicle performing the route
            if isinstance(destination, NodeDL):
                self.request_list.append(destination.get_request_id())
            
            origin_v = self.start_pos.get_id()
            vehicle = self.DAO.get_vehicles_nodes()[origin_v]
            vehicle_type = vehicle.get_type()
            vehicle_id = vehicle.get_id()

            # Define the time window between origin and destination
            origin_dest_delay = self.DAO.get_distance_from_to(
                origin.get_id(), destination.get_id())[vehicle_type]

            

            legs[(origin.get_id(), destination.get_id())] = \
                Leg(origin,
                    destination,
                    int(origin_dest_delay)
                    )

        return legs

    def get_ordered_route(self):
        return self.ordered_list

    def set_legs_proportional_time(self):
        for l in self.legs_dic.values():
            # Proportional time of complete route rode from
            # origin to destination
            l.set_proportional_t(l.get_invehicle_t() / self.total_invehicle_t)

    def get_total_invehicle_t(self):
        return self.total_invehicle_t

    def get_total_clock_t(self):
        return self.total_clock_t

    def get_total_idle_t(self):
        return self.total_idle_t

    def get_legs_dic(self):
        return self.legs_dic

    def __str__(self):

        s = "\nOPERATIONAL TIME: " + \
            str(datetime.timedelta(seconds=self.get_total_clock_t())) + " - "
        s += str(datetime.timedelta(seconds=self.get_total_invehicle_t())
                 ) + " (WORKING) + "
        s += str(datetime.timedelta(seconds=self.get_total_idle_t())) + " (IDLE)"

        s += "\nROUTE:\n"
        route = ""
        for k,legs in self.legs_dic.items():
            from_k = k[0]
            to_k = k[1]
            if isinstance(self.path[from_k], NodeDepot):
                route += "  " + str(self.path[from_k]) + '\n'
            route += legs.get_time_profile()
            route += "  " + str(self.path[to_k]) + '\n'

        s += route

        return str(s)

    def get_json(self):

        s = '{{"route_clock_time":"{0}"'.format(
            datetime.timedelta(seconds=self.get_total_clock_t()))
        s += ', "route_working_time":"{0}"'.format(
            datetime.timedelta(seconds=self.get_total_invehicle_t()))
        s += ', "route_requests":[{0}]'.format(",".join('"'+r+'"' for r in self.get_request_list()))
        s += ', "route_idle_time":"{0}"'.format(
            datetime.timedelta(seconds=self.get_total_idle_t()))
        s += ', "route_sequence_of_nodes":[' + ','\
             .join(self.path[node].get_json_leg_node()
                   for node in self.ordered_list) + ']'

        s += ', "route_legs":[' + ',' \
            .join(self.legs_dic[(node, self.path[node].get_id_next())].get_json() for node in self.ordered_list
                  if not (self.path[node].get_id_next() is None
                          or isinstance(self.path[self.path[node].get_id_next()], NodeDepot))) + ']}'
        # If next is depot (auxiliar node) --> discarded
        return str(s)
