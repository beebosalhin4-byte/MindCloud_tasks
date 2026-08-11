import random

posture = random.choice(["sitting", "standing"])
direction = random.choice(["left", "right", "facing"])
distance = random.choice([1, 2, 3, 4, 5, 6, 7, 8, 9, 10])

def dist(distance):
    for step in range(distance,0,-1):
        print (f"Moving.....{step} steps left.")

print(f"Start State -> Posture: {posture}, Direction: {direction}, Distance: {distance}")
if posture == "sitting": 
    print("Nexus stands up.")
if direction=="left" or direction == "right":
    print("Nexus turns towards the door.")
dist(distance)