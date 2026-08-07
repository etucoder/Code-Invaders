stardust_needed = 9465.48
paymentperhour = 0
goal = "CF"
mode = "CalculateHours"
while True:
    if goal == "CF":
        stardust_needed = 8281
        total_days = 50
        weekend = 14
        weekendhours = 16
        weekdays = 36
        weekdayhours = 7
    else:
        stardust_needed = int(input())
        total_days = int(input("What are the total amount of days?"))
        weekend = int(input("How many weekends?"))
        weekendhours = int(input("How many hours per weekend"))
        weekdays = total_days - weekend
        weekdayhours  = int(input("How many hours per weekday?"))
    paymentperhour = int(input())
    if mode == "CalculateHours":
           print((weekend * weekendhours * paymentperhour) + (weekdays * weekdayhours * paymentperhour))
