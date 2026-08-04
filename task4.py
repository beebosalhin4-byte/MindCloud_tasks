import random
import string
lower = list(string.ascii_lowercase)
upper = list(string.ascii_uppercase)
special = ["!", "@", "#", "$", "%", "&", "*", "?", "_"]

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
res = {"upperr": 0, "lowerr": 0, "speciall": 0, "numberr": 0}
passs = input("Enter your password: ")
fail = 0
for i in passs:
    try:
        if int(i) in range(10):
            res["numberr"] +=1
    except:
        if i in lower:
            res["lowerr"] +=1
        elif i in upper:
            res["upperr"] += 1
        elif i in special:
            res["speciall"] += 1
for j in res.values():
    if j == 0:
        fail +=1
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
  
