#!/home/fsoares/purchase_planner/PurchaseOrder_Scheduler/bin/python
#
# Script to parse attachments with hot item stock
#

import psycopg2
import csv

filename='BA.csv'

conn = 

lines = list(csv.reader(open(filename, 'rb'), delimiter=';'))

for line in lines:
    print(line[6],line[13])
