import random
rnd = 1
score = 0
wonrnd = 0
numrnd = 0
print("Welcome Player!")
print("I'm thinking of a number between 1 and 100.")
print("You have 6 attempts to guess it.")
while rnd:
    current = 0
    numrnd +=1
    num = random.choice(range(2,100))
    i = 1
    while i <7:
        print(f"Attempt {i}/6")
        user = int(input("Enter your guess: "))
        if user <=1 or user >= 100:
            print("Out of Range")
            continue
        if user == num:
            print("Congratulations!")
            print("You guessed the number")
            print(f"Guesses Remaining: {6-i}")
            print(f"Multiplier: x{7-i}")
            print(f"Points earned: {7-i}")
            current = 7-i
            score +=current
            print(f"Current score: {score}")
            wonrnd +=1
            break
        elif user < num and num-user >= 20:
            print("Too low")
            i +=1
            continue
        elif user > num and user-num >= 20:
            print("Too high")
            i +=1
            continue
        elif user < num and num-user < 20:
            print("Lower")
            i +=1
            continue
        elif user > num and user-num < 20:
            print("Higher")
            i +=1
            continue
    if i == 7:
        print(f"The secret number is {num}")
    res = input("Play another round? (y/n): ")
    if res == "n" or res == "N":
        rnd = 0
    else:
        pass
print(f"Rounds Played: {numrnd}")
print(f"Rounds Won: {wonrnd}")
print(f"Final Score: {score}")
    


