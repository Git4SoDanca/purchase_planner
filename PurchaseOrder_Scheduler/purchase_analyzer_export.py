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

fileout = open('purchase_export.txt','w')
cursor_dates = conn.cursor()
cur = conn.cursor()
cur2 = conn.cursor()
now = datetime.datetime.now()
now_date = (datetime.datetime.now()).strftime('%Y-%m-%d')

lead_time = lead_normal = 1
forecast_window_limit = 39
purchase_period = 1
initial_regular_ship_date = now + datetime.timedelta(weeks = lead_time) #lead time in weeks
forecast_window_limit_date = now + datetime.timedelta(weeks = forecast_window_limit+lead_time)

product_list_query = """SELECT sc.id, pp.name
FROM product_product as pp
LEFT JOIN (select id from sodanca_stock_control where grade in ('A')) as sc ON pp.id = sc.id
WHERE sc.id IS NOT NULL AND pp.name_template IN ('SD16', 'JZ76L')
ORDER BY pp.name_template"""

cur.execute(product_list_query)

product_list = cur.fetchall()
fileout.write('pid;product_name;start_date;end_date;quantity_to_order;on_order_late; on_order_current;committed;sold;expected_on_hand;on_hand;trend_last9mo;query string\n')
for product in product_list:
	# print('product id: {0} product name: {1}'.format(product[0],product[1]))
	pid = product[0]
	pname = product[1]
	for pdate in rrule.rrule(rrule.WEEKLY, dtstart = initial_regular_ship_date, until = forecast_window_limit_date):
		start_date = pdate.strftime('%Y-%m-%d')
		# print('DEBUG - Top of pdate loop:',start_date)
		end_date = (pdate + datetime.timedelta(weeks = purchase_period)).strftime('%Y-%m-%d')
		start_prev_year = (pdate - datetime.timedelta(weeks = 52)).strftime('%Y-%m-%d')
		end_prev_year = (pdate - datetime.timedelta(weeks = 52) + datetime.timedelta(weeks = purchase_period)).strftime('%Y-%m-%d')
		now_minus_6mo = (datetime.datetime.now()-datetime.timedelta(weeks = 12)).strftime('%Y-%m-%d')


		quantities_query = """SELECT COALESCE(sd_quantity_to_order({0},'{1}','{2}'),0), COALESCE(sd_qoo({0},'{3}','{1}'),0), COALESCE(sd_qoo({0},'{1}','{2}'),0), COALESCE(sd_qcomm({0},'{1}','{2}'),0), COALESCE(sd_qs({0},'{4}','{5}'),0), COALESCE(sd_expected_onhand({0},'{1}'),0), COALESCE(sd_qoh({0}),0), COALESCE(sd_sales_trend({0}),0)""".format(pid, start_date, end_date, now_minus_6mo, start_prev_year, end_prev_year)
		cur2.execute(quantities_query)
		conn.commit()
		qq_list = cur2.fetchall()
		for qq_each in qq_list:
			fileout.write("{0};{1};{2};{3};{4};{5};{6};{7};{8};{9};{10};{11};{12}\n".format(pid,pname,start_date,end_date,qq_each[0],qq_each[1],qq_each[2],qq_each[3],qq_each[4],qq_each[5],qq_each[6],qq_each[7],quantities_query))

conn.close()
fileout.close()
