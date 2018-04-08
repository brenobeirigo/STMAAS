from model.Coordinate import Coordinate
from datetime import *
import time


# Class node
class Node(object):
    # Number of pickup/delivery nodes
    n_nodes = 1
    # Number of depots
    d_nodes = 1

    @classmethod
    def reset_nodes_ids(cls):
        # Number of pickup/delivery nodes
        cls.n_nodes = 1
        # Number of depots
        cls.d_nodes = 1

    @staticmethod
    def get_formatted_time(time):
        if time == 0:
            return "---------- --:--:--"
        else:
            return datetime.fromtimestamp(int(time)).strftime('%Y-%m-%d %H:%M:%S')

    @staticmethod
    def get_formatted_time_h(time):
        if time == 0:
            return "--:--:--"
        else:
            return datetime.fromtimestamp(int(time)).strftime('%H:%M:%S')

    @staticmethod
    def get_formatted_duration_h(time):
        if time == 0:
            return "--:--:--"
        else:
            return datetime.fromtimestamp(int(time), timezone.utc).strftime('%H:%M:%S')
    
    @staticmethod
    def get_formatted_duration_m(time):
        if time == 0:
            return "--:--"
        else:
            return datetime.fromtimestamp(int(time), timezone.utc).strftime('%M:%S')

    def __init__(self, type, id, x, y, demand, request_id, network_node_id=None):
        self.request_id = request_id
        self.type = type
        self.id = id
        self.coord = Coordinate(x, y)
        self.demand = demand
        self.reset()
        self.network_node_id = network_node_id
        self.service_t = 0  # Time for embarking disembarking
    
    def get_network_id(self):
        return self.network_node_id

    def set_is_live_stock(self, live_stock):
        self.live_stock = live_stock
    
    def is_live_stock():
        return self.live_stock

    def set_service_t(self, service_t):
        self.service_t = service_t

    def get_service_t(self):
        return self.service_t
    
    def get_network_node_id(self):
        return self.network_node_id

    def reset(self):
        self.arrival_t = 0
        self.load = {}
        self.id_next = None
        self.vehicle = None

    def get_vehicle(self):
        return self.vehicle
    def get_request_id(self):
        return self.request_id

    def get_demand(self):
        return self.demand

    def get_demand_short(self):
        return {id: int(self.demand[id]) for id in self.demand.keys() if int(self.demand[id]) != 0}

    def get_load(self):
        return self.load

    def get_type(self):
        return self.type

    def set_type(self, type):
        self.type = type

    def get_id_next(self):
        return self.id_next

    def set_id_next(self, id_next):
        self.id_next = id_next

    def set_arrival_t(self, arrival_t):
        self.arrival_t = arrival_t

    def is_visited(self):
        return self.arrival_t > 0

    def set_vehicle(self, vehicle):
        self.vehicle = vehicle

    def set_load(self, load):
        self.load = load

    def get_id(self):
        return self.id

    def get_arrival_t(self):
        return self.arrival_t

    def get_load(self):
        return self.load

    def get_load_0(self):
        return {id: int(self.load[id]) for id in self.load.keys() if abs(int(self.load[id])) != 0}

    def get_coord(self):
        return self.coord

    @classmethod
    def increment_id(self):
        Node.n_nodes = Node.n_nodes + 1

    @classmethod
    def increment_id_depot(self):
        Node.d_nodes = Node.d_nodes + 1

    @classmethod
    def get_n_nodes(self):
        return Node.n_nodes

    @classmethod
    def get_d_nodes(self):
        return Node.d_nodes

    @classmethod
    def factory_node(self, type, id, x, y, demand, request_id, network_node_id=None):
        if type == 'DL':
            return NodeDL(type, id, x, y, demand, request_id, network_node_id=network_node_id)
        elif type == 'PK':
            return NodePK(type, id, x, y, demand, request_id, network_node_id=network_node_id)
        elif type == 'DP':
            return NodeDepot(type, id, x, y, demand, request_id, network_node_id=network_node_id)
        else:
            return None

    @classmethod
    def copy_node(self, node):
        return Node.factory_node(node.get_type(), node.get_id(), node.get_coord().get_x(), node.get_coord().get_y(), node.get_demand(), node.get_request_id(), node.get_network_id())

    def __str__(self):
        return " " + str(self.get_id()) + str(self.coord) + " " + str({id: int(self.demand[id]) for id in self.demand.keys() if int(self.demand[id]) != 0})


# Pickup node
class NodePK(Node):
    def __init__(self, type, id, x, y, demand, request_id, network_node_id=None):
        new_id = id
        # Nodes with new_id != None have a specific value assigned
        if new_id == None:
            new_id = "PK" + str('%03d' % Node.get_n_nodes())
        #Node.increment_id()
        Node.__init__(self, type, new_id, x, y, demand, request_id, network_node_id=network_node_id)

    def set_vehicle(self, vehicle):
        self.vehicle = vehicle

    def __str__(self):
        return self.get_request_id() + " - " + Node.get_formatted_time(self.arrival_t) \
            + '  |' + self.get_id() + '|' \
            + ' - LOAD: ' \
            + str({id: int(self.load[id])
                   for id in self.load.keys()
                   if int(self.load[id]) > 0})

    def get_json(self):
        js = '{'
        js += '"node_id": "' + self.get_id() + '"'
        js += ', "request_id":"' + self.get_request_id() + '"'
        js += ', "type":"' + self.get_type() + '"'
        js += ', "lat":' + str(self.coord.get_y())
        js += ', "lng":' + str(self.coord.get_x())
        js += '}'
        return js

    def get_json_leg_node(self):
        js = '{'
        js += '"node_id": "' + self.get_id() + '"'
        js += ', "request_id":"' + self.get_request_id() + '"'
        js += ', "type":"' + self.get_type() + '"'
        js += ', "vehicle_id":'+ ('"'+self.get_vehicle().get_id()+'"' if self.get_vehicle() is not None else "null")
        js += ', "lat":' + str(self.coord.get_y())
        js += ', "lng":' + str(self.coord.get_x())
        js += ', "node_arrival_time":"' + \
            Node.get_formatted_time(self.arrival_t) + '"'
        js += ', "compartment_status": ['\
            + ','.join('{{ "compartment_id":"{0}","compartment_load":{1} }}'.format(c, l) for c, l in self.get_load_0().items())\
            + ']'
        js += '}'
        return js

# Delivery node


class NodeDL(Node):
    def __init__(self, type, id, x, y, demand, request_id, network_node_id=None):
        new_id = id
        # Nodes with new_id != None have a specific value assigned
        if new_id == None:
            new_id = "DL" + str(str('%03d' % Node.get_n_nodes()))
        Node.increment_id()
        Node.__init__(self, type, new_id, x, y, demand, request_id, network_node_id=network_node_id)

    def get_json(self):
        js = '{'
        js += '"node_id": "' + self.get_id() + '"'
        js += ', "request_id":"' + self.get_request_id() + '"'
        js += ', "type":"' + self.get_type() + '"'
        js += ', "lat":' + str(self.coord.get_y())
        js += ', "lng":' + str(self.coord.get_x())
        js += '}'
        return js

    def get_json_leg_node(self):
        js = '{'
        js += '"node_id": "' + self.get_id() + '"'
        js += ', "request_id":"' + self.get_request_id() + '"'
        js += ', "type":"' + self.get_type() + '"'
        js += ', "vehicle_id":'+ ('"'+self.get_vehicle().get_id()+'"' if self.get_vehicle() is not None else "null")
        js += ', "lat":' + str(self.coord.get_y())
        js += ', "lng":' + str(self.coord.get_x())
        js += ', "node_arrival_time":"' + \
            Node.get_formatted_time(self.arrival_t) + '"'
        js += ', "compartment_status": ['\
            + ','.join('{{ "compartment_id":"{0}","compartment_load":{1} }}'.format(c, l) for c, l in self.get_load_0().items())\
            + ']'
        js += '}'
        return js
    def __str__(self):
        # return '|DL|' + super().__str__() + ' - LOAD: ' + str({id:int(self.load[id]) for id in self.load.keys() if int(self.load[id])>0}) + ' - ARR: ' + datetime.fromtimestamp(int(self.arrival_t)).strftime('%Y-%m-%d %H:%M:%S')
        return self.get_request_id() + " - " + Node.get_formatted_time(self.arrival_t) + '  |' + self.get_id() + '|' + ' - LOAD: ' + str({id: int(self.load[id]) for id in self.load.keys() if int(self.load[id]) > 0})

# Departure/arrival node


class NodeDepot(Node):
    def __init__(self, type, id, x, y, demand, request_id, network_node_id=None):
        new_id = id
        if new_id == None:
            new_id = "DP" + str('%03d' % Node.get_d_nodes())
        Node.increment_id_depot()
        Node.__init__(self, type, new_id, x, y, demand, request_id, network_node_id=network_node_id)

    def get_json(self):
        js = '{'
        js += '"node_id": "' + self.get_id() + '"'
        js += ', "request_id":null'
        js += ', "type":"' + self.get_type() + '"'
        js += ', "lat":' + str(self.coord.get_y())
        js += ', "lng":' + str(self.coord.get_x())
        js += '}'
        return js

    def get_json_leg_node(self):
        js = '{'
        js += '"node_id": "' + self.get_id() + '"'
        js += ', "request_id":null'
        js += ', "type":"' + self.get_type() + '"'
        js += ', "vehicle_id":'+ ('"'+self.get_vehicle().get_id()+'"' if self.get_vehicle() is not None else "null")
        js += ', "lat":' + str(self.coord.get_y())
        js += ', "lng":' + str(self.coord.get_x())
        js += ', "node_arrival_time":"' + \
            Node.get_formatted_time(self.arrival_t) + '"'
        js += ', "compartment_status": ['\
            + ','.join('{{ "compartment_id":"{0}","compartment_load":{1} }}'.format(c, l) for c, l in self.get_load_0().items())\
            + ']'
        js += '}'
        return js

    def __str__(self):
        # print("STR: ", self.arrival_t)
        return "START - " + Node.get_formatted_time(self.arrival_t) + '  |' + self.get_id() + ' (' + str(self.get_network_node_id()) + ')' + '|' + ' - LOAD: ' + str({id: int(self.load[id]) for id in self.load.keys() if int(self.load[id]) > 0})
