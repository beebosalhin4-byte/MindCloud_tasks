import random
import string
lower = list(string.ascii_lowercase)
upper = list(string.ascii_uppercase)
special = ["!", "@", "#", "$", "%", "&", "*", "?", "_"]
number = range(10)
###### OPTION 1
lenn = int(input("Enter password length: "))
response = 1
while response:
    user = " "
    for letter in range(lenn):
        user += random.choice([str(random.choice(range(10))), random.choice(special), random.choice(lower), random.choice(upper)])
    print(user)
    respo = input("satisfied? (y/n): ")
    if respo == "y" or respo =="Y":
        response = 0
    elif respo == "n" or respo == "N":
        continue
    else:
        response = 0

###### OPTION 2
def check(passs):
    res = {"upper": 0, "lower": 0, "special": 0, "number": 0}
    fail = 0
    miss = list()
    for i in passs:
        try:
            if int(i) in range(10):
                res["number"] +=1
        except:
            if i in lower:
                res["lower"] +=1
            elif i in upper:
                res["upper"] += 1
            elif i in special:
                res["special"] += 1
    for j  in res:
        if res[j] == 0:
            fail +=1
            miss.append(j)
    if len(passs) < 8:
        fail += 1
    if fail >= 3:
        print("Password Strength: Weak")
    elif fail == 2:
        print("Password Strength: Medium")
    elif fail == 1:
        print("Password Strength: Strong")
    elif fail == 0:
        print("Password Strength: Very strong")
    return miss

passs1 = input("Enter your password: ")
check(passs1)
yy = 1
while yy:
    yyy = input("Need Improvement Suggestions? (y/n): ")
    if yyy == "y" or yyy == "Y":
        pass
    else:
        yy = 0
        continue
    passs2 = input("Enter another password: ")
    listt = check(passs2)
    for i in listt:
        if i != "number":
            passs2 += random.choice(globals()[i])
        elif i == "number":
            passs2 += str(random.choice(globals()[i]))
    if len(passs2) < 8:
        for p in range(8-len(passs2)):
            passs2 += random.choice([str(random.choice(range(10))), random.choice(special), random.choice(lower), random.choice(upper)])
    print(f"Recommendation: {passs2}")
