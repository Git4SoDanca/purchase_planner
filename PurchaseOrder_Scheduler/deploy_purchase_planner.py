#!/home/fsoares/purchase_planner/PurchaseOrder_Scheduler/bin/python
#
# Script to create purchase_planner table
#

import psycopg2
conn = psycopg2.connect("dbname='OE-BackupProd-CAN-20171117' host='192.168.100.70' user='postgres' password='y586ML6FFnSbRStcjcae'")
conn.autocommit = True

cur = conn.cursor()

sql_file = open('SQL/CREATE_purchase_planner_functions_views.sql','r')
# print(sql_file)
cur.execute(sql_file.read())
sql_file = open('SQL/update_product_inventory_grading.sql','r')
# print(sql_file)
cur.execute(sql_file.read())
conn.close()
