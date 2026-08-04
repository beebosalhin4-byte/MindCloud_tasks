import time
minutess = int(input("enter the minutes: "))
secondss = int(input("enter the seconds: "))
timee= minutess*60 + secondss
state = " "
if timee<= 0 or secondss > 59:
    print("Invalid test duration.")
    sys.exit()
if secondss > 300:
    print("Safety limit exceeded! Test duration capped to 05:00.")
    timee= 5*60
for second in range(timee,-1,-1):
    time.sleep(1)
    mins = second // 60
    secs = second % 60
    if second > 30:
        state = "POWER ON"
        print(f"{state} | Remaining: {mins}:{secs}", end = "\r")
    elif second <= 30 and second > 10: 
        state = "STABILIZING SYSTEM"
        print(f"{state} | Remaining: {mins}:{secs}", end = "\r")
    elif second <= 10 and second != 0:
        state = "COOLDOWN PHASE | Do not touch"
        print(f"{state} | Remaining: {mins}:{secs}", end = "\r")
    elif second == 0:
        print(f"{state} | Remaining: {mins}:{secs}", end = "\n")
print("Power test completed successfully.")

