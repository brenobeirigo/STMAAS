import math
from random import *


class Compartment:
    sep1 = "/"
    sep2 = "="

    def __init__(self, label, amount, cost=0):
        self.label = label
        self.amount = int(amount)
        self.cost = 0

    def __str__(self):
        return self.label + Compartment.sep2 + str(self.amount)

    def __repr__(self):
        return self.label + Compartment.sep2 + str(self.amount)
    
    @classmethod
    def factory(cls, type_comp, label_comp, number_comp):
        if type_comp == "H":
            return CompartmentHuman(label_comp, number_comp)

    @staticmethod
    def get_array_of_compartments(str_compartment, s1, s2):
        comps = str_compartment.split(s1)
        a = []
        for c in comps:
            pair = c.split(s2)
            a.append(Compartment(pair[0], pair[1]))
        return a

    def get_label(self):
        return self.label

    def get_amount(self):
        return self.amount

    def get_random_occupancy_level(self, l, u):
        lower = 1 if l == 0 else math.ceil(l * self.amount)
        upper = self.amount if u > self.amount else math.ceil(u * self.amount)
        return randint(lower, upper)


    def get_random_copy(self):
        rand_amount = randint(1, self.amount)
        return Compartment(self.label, rand_amount)

    def get_random_copy_in_range(self, l,u):
        lower = 1 if l == 0 else math.ceil(l * self.amount)
        upper = self.amount if u > self.amount else math.ceil(u * self.amount)
        rand_amount = randint(lower, upper)
        # print("RANDOM:", l, u, lower, upper, rand_amount)
        return Compartment(self.label, rand_amount)

    @staticmethod
    def get_random_request(str_compartment, s1, s2, l, u):
        a_compartments = Compartment.get_array_of_compartments(
            str_compartment, s1, s2)
        str_random_compartments = []
        for c in a_compartments:
            str_random_compartments.append(str(Compartment(
                c.get_label(), c.get_random_occupancy_level(l, u))))
        return Compartment.sep1.join(sr for sr in str_random_compartments)

class CompartmentHuman(Compartment):
    def __init__(self, label, amount):
        Compartment.__init__(self,label, amount)
        
class CompartmentFreight(Compartment):
   def __init__(self, label, amount):
        Compartment.__init__(self,label, amount)
        