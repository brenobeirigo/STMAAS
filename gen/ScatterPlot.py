import matplotlib.pyplot as plt
class ScatterPlot:
    ##########################################################################
    ########################### PLOTTING WITH MATPLOTLIB #####################
    ##########################################################################
    # 1 - Get a scatter plot from model.Coordinates
    def create_scatter_plot(self):
        nodes_dic = self.DAO.get_nodes_dic()
        # Create list of x coordinates
        x_coord = [nodes_dic[key].get_coord().get_x() * 1000000
                   for key in nodes_dic.keys()]

        # Create list of y coordinates
        y_coord = [nodes_dic[key].get_coord().get_y() * 1000000
                   for key in nodes_dic.keys()]

        # Create scatter distribution on plt (import from matplotlib)
        plt.scatter(x_coord, y_coord)

        return plt

    # 2 - Receive p1, data(p2, arrival_t, load, travel_t) and creates
    # annotations with this information next to the node
    def create_node_info(self):
        nodes = self.DAO.get_nodes_dic()
        for n_id in nodes.keys():
            n = nodes[n_id]
            arrival = n.get_arrival_t()
            # If arrival == 0 service was denied, i.e. node wasn't attended
            if arrival == 0:
                continue
            load = n.get_load_0()
            tt = 0
            an = ''
            # If travel time is empty => print arrival node
            if isinstance(n, NodeDL):
                arri = datetime.fromtimestamp(arrival).strftime('%H:%M:%S')
                an = 'AR:' + str(arri) + "\nLOAD:" + str(load)

            # If travel time is NOT empty => print departure node
            elif isinstance(n, NodePK):

                # Max travel time of request p1
                # max_tt = str(self.dist_matrix[n.get_id(), n.get_id_next()] + self.MAX_LATENESS)

                # Earliest time / Arrival time
                # Load to be picked up in departure node
                # Total travel time of request / Max. travel time allowed
                arri = datetime.fromtimestamp(arrival).strftime('%H:%M:%S')
                ear = self.earliest_t[n.get_id()].strftime('%H:%M:%S')
                an = 'ARRIVAL:' + str(ear) + '/' + str(arri)\
                    + '\nLOAD:' + str(load)\
                    #+ '\nTT:' + str(tt) + '/' + max_tt

            # Create annotation to show node info
            plt.annotate(an,
                         (n.get_coord().get_x() * 1000000,
                          n.get_coord().get_y() * 1000000),
                         xytext=(25, -25),
                         textcoords='offset points',
                         ha='left',
                         va='bottom',
                         fontsize=10,
                         bbox=dict(boxstyle='round4,pad=0.1',
                                   fc='white',
                                   color='white',
                                   alpha=50))

    # 3 - Create nodes with text inside above each point
    def create_nodes(self):
        nodes_dic = self.DAO.get_nodes_dic()

        plt, self.DAO.get_nodes_dic()
        for p in nodes_dic.keys():
            n = nodes_dic[p]
            arrival = n.get_arrival_t()
            bg_node = "white"
            if arrival == 0 and (not isinstance(n, NodeDepot)):
                bg_node = "red"
            plt.annotate("$" + n.get_id()[0:2]
                         + "_{" + n.get_id()[2:] + "}$",
                         (n.get_coord().get_x() * 1000000,
                          n.get_coord().get_y() * 1000000),
                         xytext=(0, 0),
                         textcoords='offset points',
                         ha='center',
                         va='bottom',
                         fontsize=16,
                         bbox=dict(boxstyle='circle, pad=0.2',
                                   fc=bg_node,
                                   alpha=1))

    # 4 - Draw vehicle arrows
    def create_arrows(self):
        vehicle_dic = self.DAO.get_vehicle_dic()
        for k in vehicle_dic.keys():
            veh = vehicle_dic[k]
            p1 = veh.get_pos().get_id()
            path = veh.get_path()
            p2 = path[p1].get_id_next()
            while p1 in path.keys() and p2 != None:
                # From/to coordinates
                p1_coord = path[p1].get_coord()
                p2_coord = path[p2].get_coord()

                # x, y coordinates From/to
                p1_x = p1_coord.get_x() * 1000000
                p1_y = p1_coord.get_y() * 1000000
                p2_x = p2_coord.get_x() * 1000000
                p2_y = p2_coord.get_y() * 1000000

                plt.arrow(p1_x,
                          p1_y,
                          p2_x - p1_x,
                          p2_y - p1_y,
                          head_width=0.01,
                          head_length=0.1,
                          fc='k',
                          ec=veh.get_color())

                # Get middle point of an arrow
                middle_p = Coordinate.get_middle_point(p1_coord, p2_coord)
                p1 = p2
                p2 = path[p1].get_id_next()

    # 5 - Draw annotation for lines (e.g.: Xij = 2.3 min)
    def create_middle_line_annotation(self):
        vehicle_dic = self.DAO.get_vehicle_dic()
        for k in vehicle_dic.keys():
            veh = vehicle_dic[k]
            p1 = veh.get_pos().get_id()
            path = veh.get_path()
            p2 = path[p1].get_id_next()
            while p1 in path.keys() and p2 != None:
                # From/to coordinates
                p1_coord = path[p1].get_coord()
                p2_coord = path[p2].get_coord()

                # Get middle point of an arrow
                middle_p = Coordinate.get_middle_point(p1_coord, p2_coord)

                # Annotate the distance between points
                x_ij = '$' + p1[0:2] + "_{" + p1[2:] + \
                    '},' + p2[0:2] + "_{" + p2[2:] + '}' + '$'
                plt.annotate(str(x_ij + '(' + str(round(self.DAO.get_distance_matrix()[p1, p2] / 60, 2)) + ')'),
                             (middle_p.get_x() * 1000000,
                              middle_p.get_y() * 1000000),
                             xytext=(0, 0),
                             textcoords='offset points',
                             ha='center',
                             va='bottom',
                             fontsize='10',
                             bbox=dict(boxstyle='round4,pad=0.1',
                                       color='white',
                                       fc='white',
                                       alpha=1))

                p1 = p2
                p2 = path[p1].get_id_next()

    # 6 - Draw requests annotation
    def create_requests(self):
        requests = self.DAO.get_request_list()
        for h in requests:
            p1 = h.get_origin()
            p1_coord = p1.get_coord()
            p2 = h.get_destination()
            p2_coord = p2.get_coord()

            id_origin = p1.get_id()
            id_destination = p2.get_id()

            # Pickup
            plt.annotate("$" + str(h.get_id()) + "$" + '(' + str(h.get_demand_short()) + ')',
                         (p1_coord.get_x() * 1000000, p1_coord.get_y() * 1000000),
                         xytext=(0, 30),
                         textcoords='offset points',
                         ha='center',
                         va='bottom',
                         bbox=dict(boxstyle='round,pad=0.5',
                                   fc='#b2ffb6',
                                   alpha=1))

            # Dropoff
            plt.annotate("$" + str(h.get_id()) + "$" + '(' + str(h.get_demand_short()) + ')',
                         (p2_coord.get_x() * 1000000,
                          p2_coord.get_y() * 1000000),
                         xytext=(0, 30),
                         textcoords='offset points',
                         ha='center',
                         va='bottom',
                         bbox=dict(boxstyle='round4,pad=0.5',
                                   fc='#ffae93',
                                   alpha=1))

    # Plot the result of method
    def plot_result(self):
        if self.response is not None:
            # Create scatter plot in plt from matplotlib
            self.create_scatter_plot()

            # Draw nodes
            self.create_nodes()

            # Draw arrows
            self.create_arrows()

            # Draw requests
            self.create_requests()

            # Create node annotation (AR, LOAD)
            self.create_node_info()

            # Annotation for lines (e.g.: Xij = 2.3 min)
            self.create_middle_line_annotation()

            # Show graph
            plt.axis('off')
            plt.show()
        else:
            print('PLOT IMPOSSIBLE - MODEL IS UNFEASIBLE')
