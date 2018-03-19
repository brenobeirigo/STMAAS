import urllib.request
import json
import csv


class Coordinate(object):

    def __init__(self, x, y):
        self.x = x
        self.y = y   

    @classmethod
    def get_middle_point(self, c1, c2):
         # Get middle point of an arrow
        min_x = min([c1.get_x(), c2.get_x()])
        max_x = max([c1.get_x(), c2.get_x()])
        x = min_x + (max_x - min_x) / 2.0
        min_y = min([c1.get_y(), c2.get_y()])
        max_y = max([c1.get_y(), c2.get_y()])
        y = min_y + (max_y - min_y) / 2.0
        return Coordinate(x, y)

    def get_x(self):
        # Getter method for a Coordinate object's x coordinate.
        return self.x

    def get_y(self):
        # Getter method for a Coordinate object's y coordinate
        return self.y

    def __str__(self):
        return '<' + str(self.get_x()) + ',' + str(self.get_y()) + '>'

    def __eq__(self, other):
        # First make sure `other` is of the same type
        assert type(other) == type(self)
        # Since `other` is the same type, test if coordinates are equal
        return self.get_x() == other.get_x() and self.get_y() == other.get_y()

    def __repr__(self):
        return 'Coordinate(' + str(self.get_x()) + ',' + str(self.get_y()) + ')'
