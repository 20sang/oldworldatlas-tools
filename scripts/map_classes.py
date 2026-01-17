# Class definition for a location class
class Location:
    def __init__(self, name, province, x, y):
        self.name = name
        self.province = province
        self.x = x
        self.y = y
        self.notes = []
        
# Class definition for a settlement class which inherits from Location
class Settlement(Location):
    def __init__(self, name, province, x, y, population=0):
        super().__init__(name, province, x, y)
        self.population = population

# Class definition for a point-of-interest class which inherits from Location
class PointOfInterest(Location):
    def __init__(self, name, province, x, y, description=""):
        super().__init__(name, province, x, y)
        self.description = description

# Class definition of a province which contains multiple locations
class Province:
    def __init__(self, name):
        self.name = name
        self.settlements = []
        self.points_of_interest = []
    
    def add_settlement(self, settlement):
        self.settlements.append(settlement)
    
    def add_point_of_interest(self, poi):
        self.points_of_interest.append(poi)

    def list_all_settlements(self):
        return [s.name for s in self.settlements]
    
    def return_total_population(self):
        return sum(s.population for s in self.settlements)
