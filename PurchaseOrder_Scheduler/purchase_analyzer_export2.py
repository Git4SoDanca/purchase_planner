#!/opt/purchase_planner/PurchaseOrder_Scheduler/bin/python
import psycopg2
import datetime
from dateutil import rrule
import csv

class reg(object):
	def __init__(self, cursor, registro):
		for (attr, val) in zip((d[0] for d in cursor.description),registro) :
			setattr(self, attr, val)

try:
	conn = psycopg2.connect("dbname='OE-Prod-USA-D1' host='192.168.100.70' user='purchase_planner' password='wy92ugzE98yz'")
	conn.set_session(autocommit=True)


except:
	print("I am unable to connect to the database")

fileout = open('purchase_export.csv','w')
cursor_dates = conn.cursor()
cur = conn.cursor()
cur2 = conn.cursor()
now_date = (datetime.datetime.now()).strftime('%Y-%m-%d')

schedule_query = "SELECT * FROM sodanca_shipment_schedule WHERE supplier_id = 69 AND cut_off_date > '{0}'::date".format(now_date)
cursor_dates.scrollable
cursor_dates.execute(schedule_query)
schedule_list = cursor_dates.fetchall()


product_list_query = """SELECT sc.id, pp.name
FROM product_product as pp
LEFT JOIN (select id from sodanca_stock_control where grade = 'A') as sc ON pp.id = sc.id
WHERE sc.id IS NOT NULL
ORDER BY pp.name_template"""

cur.execute(product_list_query)

product_list = cur.fetchall()

for product in product_list:
	print('product id: {0} product name: {1}'.format(product[0],product[1]))

	cursor_dates.scroll(0,mode='absolute')
	for cutoff_date in schedule_list:
		print('Cutoff Date: {0}, Exp Date {1}'.format(cutoff_date[3],cutoff_date[4]))
		


conn.close()
fileout.close()
