import time
minutess = int(input("enter the minutes: "))
secondss = int(input("enter the seconds: "))
timee= minutess*60 + secondss
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
    print(f"{mins}:{secs}", end = "\r")
print("Power test completed successfully.")

