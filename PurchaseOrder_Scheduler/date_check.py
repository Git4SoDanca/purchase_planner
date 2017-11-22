#!/usr/bin/python3
import datetime
from dateutil import rrule

now = datetime.datetime.now()
now_week = now.strftime('%Y-W%W')


rush_ship_date = (now+ datetime.timedelta(weeks = 5))   #.strftime('%Y-%m-%d')
rush_ship_week = (now+ datetime.timedelta(weeks = 5)).strftime('%Y-W%W')
rush_cutoff = (datetime.datetime.strptime(rush_ship_week + '-4', '%Y-W%W-%w' )).strftime('%Y-%m-%d')

regular_ship_week = (now+ datetime.timedelta(weeks = 9+1)).strftime('%Y-W%W')
regular_ship_date = (datetime.datetime.strptime(regular_ship_week + '-4', '%Y-W%W-%w' ))   #.strftime('%Y-%m-%d')


print(now, now_week, rush_ship_date, rush_cutoff)
print(("""Now:{0}, Now Week:{1}, Rush Date: {2}, Rush Cutoff {3}""").format(now, now_week, rush_ship_date, rush_cutoff))
print(("""Now:{0}, Now Week:{1}, Regular Ship Week: {2}, Regular Ship Date {3}""").format(now, now_week, regular_ship_week, regular_ship_date))


planning_limit = 'weeks = 54'
planning_limit_date = now + datetime.timedelta(weeks = 26+9)

for pdate in rrule.rrule(rrule.WEEKLY, dtstart = regular_ship_date, until = planning_limit_date):
    print(pdate.strftime('%Y-%m-%d %a'))
