class car:
    def __init__(self, name):
        self.name = name

    def drive(self):
        print("Driving the car")

    def show_info(self):
        print(self.name)

class Battery:

    def charge(self):
        print("Battery is charging")

    def check_range(self, charge=0):
        print(f"{100 - charge} %")

class Electric(car, Battery):
    pass

Ecar = Electric("car name :)")
Ecar.charge()
Ecar.drive()
Ecar.check_range(30)
Ecar.show_info()