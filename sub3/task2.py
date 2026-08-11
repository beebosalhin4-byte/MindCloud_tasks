class garage:
    def __init__(self, total_capacity, available_spots):
        self.__total_cap = total_capacity
        self.__available_spots = available_spots
        self.parked = 0
        self.cars = []

    def park_car(self):
        self.parked =(1 + self.parked  if self.parked < self.__total_cap else self.parked)
        self.__available_spots =(self.__available_spots - 1 if self.__available_spots > 0 else self.__available_spots)
        print('Parked')

    def remove_car(self):
        self.parked =(self.parked - 1 if self.parked >0 else self.parked)
        self.__available_spots =(1 +self.__available_spots  if self.__available_spots < self.__total_cap else self.__available_spots)
        print("Removed")

    def display_available_spots(self):
        return self.__available_spots
    

    def add_car(self, car):
        self.cars.append(car)
        print("Added")

garage1 = garage(100, 30)
garage1.park_car()
#garage1.remove_car()
print(garage1.display_available_spots())
garage1.add_car("mine")
        