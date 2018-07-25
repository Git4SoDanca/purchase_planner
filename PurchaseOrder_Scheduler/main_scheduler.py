#!/opt/purchase_planner/PurchaseOrder_Scheduler/bin/python
#
# Script to create purchase_planner table
#

import psycopg2
import datetime
import dateutil
from dateutil import rrule
from datetime import date
from dateutil.relativedelta import relativedelta
import math
import configparser
import os,sys,getopt
import poplib
import email
import csv
import logging
import time
from logging.handlers import RotatingFileHandler

#----------------------------------------------------------------------

class reg(object):
	def __init__(self, cursor, registro):
		for (attr, val) in zip((d[0] for d in cursor.description),registro) :
			setattr(self, attr, val)

def roundup(x,y):
  return int(math.ceil(x/y))*y

# def rotate_log(logfilename):
#     logger = logging.getLogger("Rotating Log")
#     logger.setLevel(logging.INFO)
#      # add a rotating handler
#     handler = RotatingFileHandler(logfilename, maxBytes=5242880, backupCount=10)
#     logger.addHandler(handler)

def log_entry(logfile, entry_text):
	# rotate_log(logfile)
	print(entry_text,'\n')
	fil = open(logfile,'a')
	fil.write(entry_text)
	fil.write('\n')
	fil.close()

def get_rush_expected_date(conn, vendor_id, now_date, companycode):
	sub_cur = conn.cursor()
	schedule_query = "SELECT * FROM sodanca_shipment_schedule WHERE supplier_id = {0} AND cut_off_date > '{1}'::date ORDER BY cut_off_date LIMIT 1".format(vendor_id, now_date)
	# print('DEBUG schedule_query: {0}'.format(schedule_query))
	logfilename = config[companycode]['logfilename']
	try:
		# print(schedule_query)
		sub_cur.execute(schedule_query)

	except Exception as e:
		log_str = 'Cannot query schedule dates. ERR:012 {}'.format(datetime.datetime.now().strftime('%H:%M:%S - %Y-%m-%d'))

		log_entry(logfilename, log_str+'\n'+str(e))
		raise

	first_date = sub_cur.fetchone()
	# print('DEBUG first_date: {}'.format(first_date))
	cut_off_date = first_date[3]
	ship_date = first_date[4]

	schedule_query = "SELECT * FROM sodanca_shipment_schedule WHERE supplier_id = {0} AND expected_date > '{1}'::date ORDER BY cut_off_date LIMIT 1".format(vendor_id, ship_date)
	logfilename = config[companycode]['logfilename']
	try:
		# print(schedule_query)
		sub_cur.execute(schedule_query)

	except Exception as e:
		log_str = 'Cannot query schedule dates. ERR:012 {}'.format(datetime.datetime.now().strftime('%H:%M:%S - %Y-%m-%d'))

		log_entry(logfilename, log_str+'\n'+str(e))
		raise

	second_date = sub_cur.fetchone()
	forecast_window_limit_date = second_date[4]
	sub_cur.close()

	return cut_off_date, ship_date, forecast_window_limit_date

def create_order(conn, order_type, product_grade, period_length, companycode):

	logfilename = config[companycode]['logfilename']

	# database cursor definitions
	cur = conn.cursor()
	cur2 = conn.cursor()

	now = datetime.datetime.now()

	now_minus_6mo = (datetime.datetime.now()-datetime.timedelta(weeks = 26)).strftime('%Y-%m-%d')
	# print(now, now_minus_6mo)

	log_str = "Starting run -- order_type: {0} Grade: {1} - {2}".format(order_type, product_grade, (datetime.datetime.now().strftime('%H:%M:%S - %Y-%m-%d')))
	log_entry(logfilename,log_str)

	vendor_array = list()

	for vendor_parent in config[companycode]['vendor_id_list'].split(","):#vendor_id_list:
		vendor_list_query = "SELECT id FROM res_partner WHERE parent_id = {0} and supplier = true".format(int(vendor_parent))
		# print(vendor_list_query)
		try:
			cur.execute(vendor_list_query)
			vendors = cur.fetchall()

		except Exception:
			log_entry(logfilename,"I can't SELECT from res_partner. ERR:001\n")

			raise

		for subvendor in vendors:
			vendor_array.append(tuple((subvendor[0],vendor_parent)))

		vendor_array.append(tuple((vendor_parent,)))

	# print('DEBUG vendor_array:',vendor_array[0])

	for vendor in vendor_array:

		# Setting dates for purchase period calculated dates for normal shipments and queried for rush
		if order_type == 'N':
			# print('DEBUG ORDER "R":',vendor, order_type)
			# initial_date_query = "SELECT ship_date FROM sodanca_purchase_plan_date WHERE status ='c';"
			# cur.execute(initial_date_query)
			initial_regular_ship_date = check_ship_date(conn, companycode) #cur.fetchone()

			lead_time = int(config[companycode]['lead_normal'])
			# initial_regular_ship_date = now + datetime.timedelta(weeks = lead_time) #lead time in weeks
			forecast_window_limit = int(config[companycode]['forecast_window_limit_normal']) #weeks
			forecast_window_limit_date = now + datetime.timedelta(weeks = forecast_window_limit+lead_time)

		elif order_type == 'R':
			# forecast_window_limit = int(config[companycode]['forecast_window_limit_rush']) #weeks DELETE IF THIS DECLARATION IS NOT NEEDED
			# print('DEBUG ORDER "R":',vendor, order_type)
			try:
				# print('DEBUG:',vendor, order_type)
				cut_off_date, initial_regular_ship_date, forecast_window_limit_date = get_rush_expected_date(conn, vendor[0], now.strftime('%Y-%m-%d'), companycode)
				# print('DEBUG expected_date return:',cut_off_date, initial_regular_ship_date, forecast_window_limit_date)

			except Exception as e:
				log_str = 'Cannot define rush window dates. ERR:011 {}'.format(datetime.datetime.now().strftime('%H:%M:%S - %Y-%m-%d'))
				log_entry(logfilename, log_str+'\n'+str(e))
				raise

		elif order_type == 'H':
			lead_time = int(config[companycode]['lead_normal'])
			initial_regular_ship_date = now
			forecast_window_limit = 1 #weeks
			forecast_window_limit_date = now + datetime.timedelta(weeks = 1)

		try:
			vendor_parent = vendor[1]
		except:
			vendor_parent = 0

		# print(subvendor[0])

		product_list_query = """SELECT product_supplierinfo.product_id, product_template.name, pricelist_partnerinfo.price AS vendor_cost, categ_id, product_product.name as product_name,
			  product_product.id, sodanca_stock_control.grade,
			  sodanca_stock_control.min_stock, sodanca_stock_control.max_stock, sodanca_stock_control.order_mod --, sodanca_stock_control.lead_time
		FROM product_supplierinfo
		LEFT JOIN product_template ON product_template.id = product_supplierinfo.product_id
		LEFT JOIN product_product ON product_supplierinfo.product_id = product_product.product_tmpl_id
		LEFT JOIN sodanca_stock_control ON sodanca_stock_control.id = product_product.id
		LEFT JOIN pricelist_partnerinfo ON pricelist_partnerinfo.suppinfo_id = product_supplierinfo.id
		-- LEFT JOIN res_partner ON res_partner.id = product_supplierinfo.name
		WHERE product_template.procure_method = 'make_to_stock'
			AND product_template.purchase_ok = true
			AND product_template.active = true
			AND product_product.active = true
			AND product_product.discontinued_product = false
			AND product_product.procure_method = 'make_to_stock'
			AND product_supplierinfo.name = {0}
			AND product_product.grade = '{1}'
			""".format(vendor[0], product_grade)
		# print(vendor)

		try:
			# print(product_list_query)
			cur.execute(product_list_query)
			product_count = cur.rowcount
			product_list = cur.fetchall()

		except Exception as e:
			log_str = "ERR:002 - Cannot query product list.\n"
			log_str += str(e)
			log_entry(logfilename,log_str)
			raise Exception
			pass

		for product in product_list:
			#Generating regular purchase orders
			product_template_id = product[0]
			product_template_name = product[1]
			vendor_cost = product[2]
			category_id = product[3]
			product_name = product[4]
			product_id = product[5]
			product_grade = product[6]
			min_stock = product[7]
			max_stock = product[8]
			order_mod = product[9]
			# lead_time = product[10]

			purchase_period = period_length #in weeks

			# print(product)
			# print('before pdate_loop', initial_regular_ship_date, forecast_window_limit_date)
			# for pdate in rrule.rrule(rrule.WEEKLY, dtstart = initial_regular_ship_date, until = forecast_window_limit_date):

			start_date = initial_regular_ship_date # pdate.strftime('%Y-%m-%d')
			now_date = (datetime.datetime.now()).strftime('%Y-%m-%d')
			end_date = (start_date + datetime.timedelta(weeks = purchase_period)).strftime('%Y-%m-%d')
			start_prev_year = (start_date - datetime.timedelta(weeks = 52)).strftime('%Y-%m-%d')
			end_prev_year = (start_date - datetime.timedelta(weeks = 52) + datetime.timedelta(weeks = purchase_period)).strftime('%Y-%m-%d')

			if order_type == 'R' and product_grade in ['C','D'] :
				qto_query = "SELECT COALESCE(sd_quantity_to_order_no_hist({0},'{1}' ,'{2}'),0)".format(product_id,start_date, end_date)
			elif order_type == 'N' and product_grade == 'C':
				qto_query = "SELECT COALESCE(sd_quantity_to_order({0},'{1}' ,'{2}'),0), COALESCE(sd_qcomm({0},'{1}' ,'{2}'),0), COALESCE(sd_quantity_to_order_no_hist({0},'{1}' ,'{2}'),0)".format(product_id,start_date, end_date)
				# qcomm_query = "SELECT COALESCE(sd_qcomm({0},'{1}' ,'{2}'),0)".format(product_id,start_date, end_date)
			else:
				qto_query = "SELECT COALESCE(sd_quantity_to_order({0},'{1}' ,'{2}'),0)".format(product_id,start_date, end_date)
			# log_str = "Processing Week {0} to {1}\n".format(start_date,end_date)
			# log_entry(logfilename,log_str)
			# print("vendor : {0} ,product_template_name: {1}, product_name: {2}, product_grade: {3}, qto_query: {4}".format(vendor, product_template_name, product_name, product_grade, qto_query)) # DEBUG
			cur.execute(qto_query) #cur3

			try:
				cur.execute(qto_query) #cur3
				product_qto = cur.fetchall()
				# if product_qto[0][0] > 0:
					# print("vendor : {0} ,product_template_name: {1}, product_name: {2}, product_grade: {3}, qto_query: {4}".format(vendor, product_template_name, product_name, product_grade, qto_query)) # DEBUG
					# print("Quantity to order: {0}".format(product_qto[0][0])) # DEBUG

			except Exception as e:
				log_str = "ERR:003 - Cannot query quantity to order.\n"
				log_str += str(e)
				log_entry(logfilename,log_str)
				raise Exception
				pass

			qto_qval = product_qto[0][0]

			if product_grade == 'C' and order_type == 'N' :
				qcomm_qval = product_qto[0][1]
				qcomm_qval_nh = product_qto[0][2]

				if qto_qval<3 and qcomm_qval == 0:
				# product_qto[0][0] = 0
					qty_2_ord = 0
				elif  qcomm_qval > 0:
				# product_qto[0][0] = product_qto[0][1]
					qty_2_ord = qcomm_qval_nh
				else:
					qty_2_ord = qto_qval
			else:
				qty_2_ord = qto_qval

			if qty_2_ord > 0: ### Production

				prod_details_query = """SELECT COALESCE(sd_quantity_to_order({0},'{1}','{2}'),0), COALESCE(sd_qoo({0},'{3}','{1}'),0), COALESCE(sd_qoo({0},'{1}','{2}'),0), COALESCE(sd_qcomm({0},'{3}','{2}'),0), COALESCE(sd_qs_prev_yr({0},'{4}','{2}'),0), COALESCE(sd_expected_onhand({0},'{1}'),0), COALESCE(sd_qoh({0}),0), COALESCE(sd_sales_trend({0}),0)""".format(product_id, start_date, end_date, now_minus_6mo, now_date)
				#Still missing box_capacity which should come here maybe as a function or a query
				# print(prod_details_query)
				try:
					cur.execute(prod_details_query) #cur3
					prod_details = cur.fetchall()

					qto=prod_details[0][0]
					qoo=prod_details[0][1]
					qoop=prod_details[0][2]
					qcomm=prod_details[0][3]
					qspy=prod_details[0][4]
					qeoh=prod_details[0][5]
					qoh=prod_details[0][6]
					qst=prod_details[0][7]

					min_qty_2_ord_c_grade = int(config[companycode]['c_min'])
					if product_grade == 'C':
						if qcomm > qspy:
							prt_str = """DEBUG qcomm>qspy- Product name:{8}
							qto:{0}
							qoo:{1}
							qoop:{2}
							qcomm:{3}
							sold_prev_year:{4}
							qeoh:{5}
							qoh:{6}
							trend:{7}""".format(qto,qoo,qoop,qcomm,qspy,qeoh, qoh,qst, product_name)
							print(prt_str)
							qto_rounded = qcomm
						elif qspy < min_qty_2_ord_c_grade:
							qto_rounded = qcomm
						elif qspy >= min_qty_2_ord_c_grade:
							qto_rounded = qspy
					elif product_grade == 'D':
						qto_rounded = qcomm
					else:
						qto_rounded = roundup(qto,order_mod)

				except Exception as e:
					log_str = 'ERR:004 - Error while gathering product quantities\n'
					log_str += str(e)
					log_entry(logfilename,log_str)
					raise Exception
					pass

				if vendor_parent != 0:
					product_vendor = vendor_parent
					product_group = vendor[0]
				else:
					product_vendor = vendor[0]
					product_group = vendor[0]

				# qto_rounded, prod_details[0][0],prod_details[0][1], prod_details[0][2], prod_details[0][3], prod_details[0][4], prod_details[0][5])
				# print(product_vendor, product_group, now.strftime('%Y-%m-%d'), start_date, product_template_id, product_id, product_grade, order_mod, product_qto[0][0],

				insert_query = """INSERT INTO sodanca_purchase_plan (id, type, vendor, vendor_group, creation_date, expected_date, template_id, template_name, product_id,
				product_name, product_category_id, product_grade, order_mod, qty_2_ord, qty_2_ord_adj, qty_on_order, qty_on_order_period, qty_committed, qty_sold,
				expected_on_hand, qty_on_hand, sales_trend, purchase_price) VALUES (default, '{20}', {0}, {1}, '{2}'::date, '{3}'::date, {4}, '{5}', {6}, '{7}', {8},
				'{9}', {10}, {11}, {12}, {13}, {14}, {15}, {16}, {17}, {18}, {19}, {21})""".format(product_vendor, product_group, now.strftime('%Y-%m-%d'), start_date,
				product_template_id, product_template_name, product_id, product_name, category_id, product_grade, order_mod, qto, qto_rounded, qoo, qoop, qcomm, qspy,
				qeoh, qoh, qst, order_type, vendor_cost)

				# print(insert_query)
				try:
					cur2.execute(insert_query)
					conn.commit()

				except Exception as e:
					log_str = "ERR:005 - Cannot insert into purchase_plan table.\n"
					log_str += str(e)
					log_entry(logfilename,log_str)
					raise Exception
					pass

	cur.close()
	cur2.close()
	now_finish = datetime.datetime.now()
	run_time = now_finish-now
	log_str="Ending run -- order_type: {0} Grade: {1} - {2}\nRun time: {3}".format(order_type, product_grade, (now_finish.strftime('%H:%M:%S - %Y-%m-%d')), str(run_time))

	log_entry(logfilename,log_str)

def create_tights_order(conn, companycode):

	logfilename = config[companycode]['logfilename']

	# database cursor definitions
	cur = conn.cursor()
	cur2 = conn.cursor()

	now = datetime.datetime.now()

	now_minus_6mo = (datetime.datetime.now()-datetime.timedelta(weeks = 26)).strftime('%Y-%m-%d')
	# print(now, now_minus_6mo)

	log_str = "Starting run -- Tights Order: {0}".format(now.strftime('%H:%M:%S - %Y-%m-%d'))
	log_entry(logfilename,log_str)

	product_vendor = config[companycode]['vendor_tights']
	categ_tights = config[companycode]['categ_tights']

	# TODO need to add check if order has already been placed for current purchasing period

	purchase_period = int(config[companycode]['lead_tights']) #in MONTHS


	now_date = datetime.datetime.now().strftime('%Y-%m-%d')
	start_date = (now + relativedelta(months =+ purchase_period)).strftime('%Y-%m-01')
	end_date = (now + relativedelta(months =+ purchase_period+1)).strftime('%Y-%m-01')
	start_prev_year = (now - relativedelta(years =- 1)).strftime('%Y-%m-01')
	end_prev_year = (now - relativedelta(months =- 11)).strftime('%Y-%m-01')

	check_po_query = """SELECT * FROM purchase_order WHERE minimum_planned_date >= '{0}' AND minimum_planned_date < '{1}'""".format(start_date,end_date)

	try:
	# print(product_list_query)
		cur.execute(check_po_query)
		po_count = cur.rowcount

		if po_count > 0:
			log_str = "Tights order already exists for delivery on period {0} to {1}.\nSkipping process.\n".format(start_date, end_date)
			log_entry(log_str)
			return
		else:
			pass

	except Exception as e:
		log_str = "ERR:120 - Cannot execute purchase order query.\n"
		log_str += str(e)
		log_entry(logfilename,log_str)
		raise Exception
		pass

	print('DEBUG - Working dates: {},{},{},{},{}'.format(now_date,start_date,end_date,start_prev_year,end_prev_year))

	product_list_query = """SELECT product_supplierinfo.product_id, product_template.name, pricelist_partnerinfo.price AS vendor_cost, categ_id, product_product.name as product_name,
	  product_product.id, sodanca_stock_control.grade,
	  sodanca_stock_control.min_stock, sodanca_stock_control.max_stock, sodanca_stock_control.order_mod --, sodanca_stock_control.lead_time
	FROM product_supplierinfo
	LEFT JOIN product_template ON product_template.id = product_supplierinfo.product_id
	LEFT JOIN product_product ON product_supplierinfo.product_id = product_product.product_tmpl_id
	LEFT JOIN sodanca_stock_control ON sodanca_stock_control.id = product_product.id
	LEFT JOIN pricelist_partnerinfo ON pricelist_partnerinfo.suppinfo_id = product_supplierinfo.id
	-- LEFT JOIN res_partner ON res_partner.id = product_supplierinfo.name
	WHERE product_template.procure_method = 'make_to_stock'
	AND product_template.purchase_ok = true
	AND product_template.active = true
	AND product_product.active = true
	AND product_product.discontinued_product = false
	AND product_product.procure_method = 'make_to_stock'
	AND product_supplierinfo.name = {0}
	""".format(product_vendor)
	# print(vendor)

	try:
	# print(product_list_query)
		cur.execute(product_list_query)
		product_count = cur.rowcount
		product_list = cur.fetchall()

	except Exception as e:
		log_str = "ERR:116 - Cannot execute product list query.\n"
		log_str += str(e)
		log_entry(logfilename,log_str)
		raise Exception
		pass

	for product in product_list:
		#Generating regular purchase orders
		product_template_id = product[0]
		product_template_name = product[1]
		vendor_cost = product[2]
		category_id = product[3]
		product_name = product[4]
		product_id = product[5]
		product_grade = product[6]
		min_stock = product[7]
		max_stock = product[8]
		order_mod = product[9]
		# lead_time = product[10]

		# print(product)
		# print('before pdate_loop', initial_regular_ship_date, forecast_window_limit_date)
		# for pdate in rrule.rrule(rrule.WEEKLY, dtstart = initial_regular_ship_date, until = forecast_window_limit_date):

		qto_query = "SELECT COALESCE(sd_quantity_to_order({0},'{1}' ,'{2}'),0)".format(product_id,start_date, end_date)
		# log_str = "Processing Week {0} to {1}\n".format(start_date,end_date)
		# log_entry(logfilename,log_str)
		# print("vendor : {0} ,product_template_name: {1}, product_name: {2}, product_grade: {3}, qto_query: {4}".format(vendor, product_template_name, product_name, product_grade, qto_query)) # DEBUG
		cur.execute(qto_query) #cur3

		try:

			cur.execute(qto_query) #cur3
			product_qto = cur.fetchall()
			# if product_qto[0][0] > 0:
				# print("vendor : {0} ,product_template_name: {1}, product_name: {2}, product_grade: {3}, qto_query: {4}".format(vendor, product_template_name, product_name, product_grade, qto_query)) # DEBUG
				# print("Quantity to order: {0}".format(product_qto[0][0])) # DEBUG

		except Exception as e:
			log_str = "ERR:117 - Cannot execute quantity to order query.\n"
			log_str += str(e)
			log_entry(logfilename,log_str)
			raise Exception
			pass

		qty_2_ord = product_qto[0][0]

		if qty_2_ord > 0: ### Production

			prod_details_query = """SELECT COALESCE(sd_quantity_to_order({0},'{1}','{2}'),0), COALESCE(sd_qoo({0},'{3}','{1}'),0), COALESCE(sd_qoo({0},'{1}','{2}'),0), COALESCE(sd_qcomm({0},'{3}','{2}'),0), COALESCE(sd_qs_prev_yr({0},'{4}','{2}'),0), COALESCE(sd_expected_onhand({0},'{1}'),0), COALESCE(sd_qoh({0}),0), COALESCE(sd_sales_trend({0}),0)""".format(product_id, start_date, end_date, now_minus_6mo, now_date)
			#Still missing box_capacity which should come here maybe as a function or a query
			try:
				cur.execute(prod_details_query) #cur3
				prod_details = cur.fetchall()
				qto=prod_details[0][0]
				qoo=prod_details[0][1]
				qoop=prod_details[0][2]
				qcomm=prod_details[0][3]
				qspy=prod_details[0][4]
				qeoh=prod_details[0][5]
				qoh=prod_details[0][6]
				qst=prod_details[0][7]

				qto_rounded = roundup(qto,order_mod)

			except Exception as e:
				log_str = "ERR:118 - Cannot execute product details query.\n"
				log_str += str(e)
				log_entry(logfilename,log_str)
				raise Exception
				pass

			product_group = product_vendor
			order_type = 'T'

			insert_query = """INSERT INTO sodanca_purchase_plan (id, type, vendor, vendor_group, creation_date, expected_date, template_id, template_name, product_id,
			product_name, product_category_id, product_grade, order_mod, qty_2_ord, qty_2_ord_adj, qty_on_order, qty_on_order_period, qty_committed, qty_sold,
			expected_on_hand, qty_on_hand, sales_trend, purchase_price) VALUES (default, '{20}', {0}, {1}, '{2}'::date, '{3}'::date, {4}, '{5}', {6}, '{7}', {8},
			'{9}', {10}, {11}, {12}, {13}, {14}, {15}, {16}, {17}, {18}, {19}, {21})""".format(product_vendor, product_group, now.strftime('%Y-%m-%d'), start_date,
			product_template_id, product_template_name, product_id, product_name, category_id, product_grade, order_mod, qto, qto_rounded, qoo, qoop, qcomm, qspy,
			qeoh, qoh, qst, order_type, vendor_cost)

			try:
				cur2.execute(insert_query)
				conn.commit()

			except Exception as e:
				log_str = "ERR:119 - Cannot insert into purchase_plan table.\n"
				log_str += str(e)
				log_entry(logfilename,log_str)
				raise Exception
				pass

	cur.close()
	cur2.close()
	now_finish = datetime.datetime.now()
	run_time = now_finish-now
	log_str="Ending run -- Tights order: {0}\nRun time: {1}".format(now_finish.strftime('%H:%M:%S - %Y-%m-%d'), str(run_time))
	log_entry(logfilename,log_str)

def drop_results_table(conn, companycode):

	cur = conn.cursor()

	start_clock = datetime.datetime.now()
	logfilename=config[companycode]['logfilename']

	# Clearing results table - Resetting for new data
	clear_table_query = """
	-- Table: public.sodanca_purchase_plan

	DROP TABLE IF EXISTS public.sodanca_purchase_plan;

	CREATE TABLE public.sodanca_purchase_plan
	(
		id SERIAL,
		type character(1) COLLATE pg_catalog."default" NOT NULL,
		vendor integer NOT NULL,
		vendor_group integer,
		creation_date date NOT NULL,
		expected_date date NOT NULL,
		template_id integer NOT NULL,
		template_name varchar(64),
		product_id integer NOT NULL,
		product_name varchar(64),
		product_category_id integer,
		product_grade character(1) COLLATE pg_catalog."default",
		order_mod smallint,
		qty_2_ord numeric NOT NULL,
		qty_2_ord_adj numeric NOT NULL,
		qty_on_order numeric,
		qty_on_order_period numeric,
		qty_committed numeric,
		qty_sold numeric,
		expected_on_hand numeric,
		qty_on_hand numeric,
		sales_trend numeric,
		purchase_price numeric,
		status character(1) DEFAULT 'N',
		--box_capacity integer,
		CONSTRAINT sodanca_purchase_plan_pkey PRIMARY KEY (id)
	)
	WITH (
		OIDS = FALSE
	)
	TABLESPACE pg_default;

	ALTER TABLE public.sodanca_purchase_plan
		OWNER to {login};
	COMMENT ON TABLE public.sodanca_purchase_plan
		IS 'Reset nightly, used by stock purchase planner';

	""".format(login = config[companycode]['login'])
	try:
		cur.execute(clear_table_query)
		conn.commit()
		cur.close()
		log_str="sodanca_purchase_plan was dropped."
		log_entry(logfilename, log_str)
	except Exception:
		log_str = "Cannot clear sodanca_purchase_plan. ERR:000\n{0}".format(conn.notices)
		log_entry(logfilename,log_str)
		pass

	cur.close()

def create_tables(conn, companycode):
	#print("In create_tables") #DEBUG
	table_queries = ['']*4

	#sodanca_stock_control & update product_product
	table_queries[0] = """
		DROP TABLE IF EXISTS sodanca_stock_control;
		CREATE TABLE sodanca_stock_control AS
		(
		WITH
		const AS (
		select     {grade_a_margin} as grade_a_margin,
				{grade_b_margin} as grade_b_margin,
				{grade_c_margin} as grade_c_margin,
				{min_inv_time_a} as min_inv_time_a,
				{max_inv_time_a} as max_inv_time_a,
				{min_inv_time_b} as min_inv_time_b,
				{max_inv_time_b} as max_inv_time_b,
				{min_inv_time_c} as min_inv_time_c,
				{max_inv_time_c} as max_inv_time_c,
				{min_inv_time_d} as min_inv_time_d,
				{max_inv_time_d} as max_inv_time_d,
				{mod_a_ba} as mod_a_ba,
				{mod_a_jz} as mod_a_jz,
				{mod_a_ch} as mod_a_ch,
				{mod_b_ba} as mod_b_ba,
				{mod_b_jz} as mod_b_jz,
				{mod_b_ch} as mod_b_ch,
				array[{categ_ba}] as categ_ba,
				array[{categ_ch}] as categ_ch,
				array[{categ_jz}] as categ_jz

		)
		, sodanca_inventory_status_last12 AS (

			 SELECT product_product.name_template,
			product_product.name, product_product.id as product_id,
			CASE
				WHEN product_template.categ_id = {categ_tights} -- Tights
					THEN 'Tights'
				WHEN product_template.categ_id IN (SELECT id from product_category where parent_id in ({categ_shoes})) -- Child of Shoes
					THEN 'Shoes'
				WHEN product_template.categ_id IN (SELECT id from product_category where parent_id in ({categ_dwear})) -- Child of Dancewear
					THEN 'Dancewear'
				WHEN product_template.categ_id = {categ_dwear} -- Dancewear
					THEN 'Dancewear'
				ELSE
					'Others'
			END AS category,
			product_template.categ_id AS category_id,
			product_template.list_price AS sale_price,
			product_template.standard_price AS cost,
			product_template.list_price - product_template.standard_price AS gross_margin,
			on_hand.quantity_on_hand,
			CASE
				WHEN sold.product_sale_total IS NOT NULL THEN sold.product_sale_total
				ELSE 0::numeric
			END AS total_sold,
			(sold.product_sale_total::double precision / 52::double precision) AS weekly_average

		   FROM product_product
			 LEFT JOIN product_template ON product_template.id = product_product.product_tmpl_id
			 LEFT JOIN ( SELECT stock_move.product_id,
					sum(stock_move.product_qty) AS product_sale_total
				   FROM stock_move
					 LEFT JOIN product_product product_product_1 ON product_product_1.id = stock_move.product_id
				  WHERE stock_move.location_dest_id = {customers} AND stock_move.location_id = {wh_stock} AND stock_move.state::text = 'done'::text
						AND stock_move.date >= (now()::date - '1 year'::interval)
				  GROUP BY stock_move.product_id) sold ON product_product.id = sold.product_id
			 LEFT JOIN ( SELECT stock_move.product_id,
					sum(stock_move.product_qty) AS product_committed_total
				   FROM stock_move
					 LEFT JOIN product_product product_product_1 ON product_product_1.id = stock_move.product_id
				  WHERE stock_move.location_dest_id = {customers} AND stock_move.location_id = {wh_stock} AND (stock_move.state::text = ANY (ARRAY['confirmed'::character varying, 'assigned'::character varying]::text[]))
				  GROUP BY stock_move.product_id) commited ON product_product.id = commited.product_id
			 LEFT JOIN ( SELECT sodanca_stock_on_hand.id,
					sodanca_stock_on_hand.quantity_on_hand
				   FROM sodanca_stock_on_hand) on_hand ON product_product.id = on_hand.id
		  WHERE
			(sold.product_sale_total > 0::numeric --Including items with no sales makes items with no sales become 'B' items
			OR commited.product_committed_total > 0::numeric) AND
			product_template.exclusive_customer IS NULL
			AND product_template.procure_method = 'make_to_stock'
			AND product_template.type = 'product'
			AND product_product.discontinued_product = false
			AND product_product.active = true

		  ORDER BY (
				CASE
					WHEN sold.product_sale_total IS NOT NULL THEN sold.product_sale_total
					ELSE 0::numeric
				END) DESC,
				   product_product.name_template, product_product.name
			),
		inventory_grade AS (
			SELECT sodanca_inventory_status_last12.*, sodanca_inventory_status_last12.weekly_average AS prod_weekly_average, (PERCENT_RANK() OVER (PARTITION BY category ORDER BY total_sold DESC))*100 as rank_qty_sold, (PERCENT_RANK() OVER (PARTITION BY category ORDER BY total_sold*gross_margin DESC))*100 as rank_gr_profit
			,
			CASE
				WHEN PERCENT_RANK() OVER (PARTITION BY category ORDER BY total_sold DESC) <= const.grade_a_margin THEN 'A'
				WHEN PERCENT_RANK() OVER (PARTITION BY category ORDER BY total_sold DESC) <= const.grade_b_margin THEN 'B'
				WHEN PERCENT_RANK() OVER (PARTITION BY category ORDER BY total_sold DESC) <= const.grade_c_margin THEN 'C'
				ELSE 'D'
			END AS grade_qty_sold,
			CASE
				WHEN PERCENT_RANK() OVER (PARTITION BY category ORDER BY total_sold*gross_margin DESC) <= const.grade_a_margin THEN 'A'
				WHEN PERCENT_RANK() OVER (PARTITION BY category ORDER BY total_sold*gross_margin DESC) <= const.grade_b_margin THEN 'B'
				WHEN PERCENT_RANK() OVER (PARTITION BY category ORDER BY total_sold*gross_margin DESC) <= const.grade_c_margin THEN 'C'
				ELSE 'D'
			END AS grade_profit,
			CASE
				WHEN PERCENT_RANK() OVER (PARTITION BY category ORDER BY total_sold*gross_margin DESC) <= const.grade_a_margin THEN ceil(sodanca_inventory_status_last12.weekly_average*const.min_inv_time_a)
				WHEN PERCENT_RANK() OVER (PARTITION BY category ORDER BY total_sold*gross_margin DESC) <= const.grade_b_margin THEN ceil(sodanca_inventory_status_last12.weekly_average*const.min_inv_time_b)
				WHEN PERCENT_RANK() OVER (PARTITION BY category ORDER BY total_sold*gross_margin DESC) <= const.grade_c_margin THEN ceil(sodanca_inventory_status_last12.weekly_average*const.min_inv_time_c)
				ELSE 0
			END AS adjusted_minimum_stock,
			CASE
				WHEN PERCENT_RANK() OVER (PARTITION BY category ORDER BY total_sold*gross_margin DESC) <= const.grade_a_margin THEN ceil(sodanca_inventory_status_last12.weekly_average*const.max_inv_time_a)
				WHEN PERCENT_RANK() OVER (PARTITION BY category ORDER BY total_sold*gross_margin DESC) <= const.grade_b_margin THEN ceil(sodanca_inventory_status_last12.weekly_average*const.max_inv_time_b)
				WHEN PERCENT_RANK() OVER (PARTITION BY category ORDER BY total_sold*gross_margin DESC) <= const.grade_c_margin THEN ceil(sodanca_inventory_status_last12.weekly_average*const.max_inv_time_c)
				ELSE 0
			END AS adjusted_maximum_stock,

			CASE
				WHEN category_id = ANY (const.categ_jz) THEN
					CASE
						WHEN PERCENT_RANK() OVER (PARTITION BY category ORDER BY total_sold DESC) <= const.grade_a_margin THEN const.mod_a_jz
						WHEN PERCENT_RANK() OVER (PARTITION BY category ORDER BY total_sold DESC) <= const.grade_b_margin THEN const.mod_b_jz
						ELSE 1
					END
				WHEN category_id = ANY (const.categ_ba) THEN
					CASE
						WHEN PERCENT_RANK() OVER (PARTITION BY category ORDER BY total_sold DESC) <= const.grade_a_margin THEN const.mod_a_ba
						WHEN PERCENT_RANK() OVER (PARTITION BY category ORDER BY total_sold DESC) <= const.grade_b_margin THEN const.mod_b_ba
						ELSE 1
					END
				WHEN category_id = ANY (const.categ_ch) THEN
					CASE
						WHEN PERCENT_RANK() OVER (PARTITION BY category ORDER BY total_sold DESC) <= const.grade_a_margin THEN const.mod_a_ch
						WHEN PERCENT_RANK() OVER (PARTITION BY category ORDER BY total_sold DESC) <= const.grade_b_margin THEN const.mod_b_ch
						ELSE 1
					END
				ELSE 1

			END AS order_mod
			FROM sodanca_inventory_status_last12, const
			ORDER BY category, name_template, total_sold DESC, sodanca_inventory_status_last12.name, rank_qty_sold

		)


		 --(product_id, grade, min_stock, max_stock, order_mod, box_size, lead_time)
		SELECT id, inventory_grade.prod_weekly_average,
		CASE
			WHEN inventory_grade.grade_profit IS NOT NULL
			THEN inventory_grade.grade_profit
			ELSE 'D'
		END AS grade,
		CASE
			WHEN inventory_grade.adjusted_minimum_stock IS NOT NULL
			THEN inventory_grade.adjusted_minimum_stock
			ELSE 0.0
		END AS min_stock,
		CASE
			WHEN inventory_grade.adjusted_maximum_stock IS NOT NULL
			THEN inventory_grade.adjusted_maximum_stock
			ELSE 0.0
		END AS max_stock,
		CASE
			WHEN inventory_grade.order_mod IS NOT NULL
			THEN inventory_grade.order_mod
			ELSE 1
		END AS order_mod
		FROM product_product
		LEFT JOIN inventory_grade ON inventory_grade.product_id = product_product.id
		WHERE
			product_product.procure_method = 'make_to_stock'
			AND product_product.discontinued_product = false
			AND product_product.active = true

		);
		ALTER TABLE public.sodanca_stock_control
			OWNER to {login};

		-- Update grades on product_product table
		UPDATE product_product SET grade = sodanca_stock_control.grade FROM sodanca_stock_control
		WHERE product_product.id = sodanca_stock_control.id;
		""".format(grade_a_margin = config[companycode]['grade_a_margin'], grade_b_margin = config[companycode]['grade_b_margin'], grade_c_margin = config[companycode]['grade_c_margin'], min_inv_time_a = config[companycode]['min_inv_time_a'], max_inv_time_a = config[companycode]['max_inv_time_a'], min_inv_time_b = config[companycode]['min_inv_time_b'], max_inv_time_b = config[companycode]['max_inv_time_b'], min_inv_time_c = config[companycode]['min_inv_time_c'], max_inv_time_c = config[companycode]['max_inv_time_c'], min_inv_time_d = config[companycode]['min_inv_time_d'], max_inv_time_d = config[companycode]['max_inv_time_d'], categ_ba = config[companycode]['categ_ba'], categ_ch = config[companycode]['categ_ch'], categ_jz = config[companycode]['categ_jz'], categ_tights = config[companycode]['categ_tights'], categ_shoes = config[companycode]['categ_shoes'], categ_dwear = config[companycode]['categ_dwear'], wh_stock = config[companycode]['wh_stock'], customers = config[companycode]['customers'], supplier = config[companycode]['supplier'], login=config[companycode]['login'], mod_a_ba=config[companycode]['a_ba'],mod_b_ba=config[companycode]['b_ba'],mod_a_ch=config[companycode]['a_ch'],mod_b_ch=config[companycode]['b_ch'],mod_a_jz=config[companycode]['a_jz'],mod_b_jz=config[companycode]['b_jz'])

	#sodanca_purchase_plan
	table_queries[1] = """
		-- Create purchase plan table to be used by POG
		DROP TABLE IF EXISTS public.sodanca_purchase_plan;

		CREATE TABLE public.sodanca_purchase_plan
		(
		  id SERIAL,
		  type character(1) COLLATE pg_catalog."default" NOT NULL,
		  vendor integer NOT NULL,
		  vendor_group integer,
		  creation_date date NOT NULL,
		  expected_date date NOT NULL,
		  template_id integer NOT NULL,
		  template_name varchar(64),
		  product_id integer NOT NULL,
		  product_name varchar(64),
		  product_category_id integer,
		  product_grade character(1) COLLATE pg_catalog."default",
		  order_mod smallint,
		  qty_2_ord numeric NOT NULL,
		  qty_2_ord_adj numeric NOT NULL,
		  qty_on_order numeric,
		  qty_on_order_period numeric,
		  qty_committed numeric,
		  qty_sold numeric,
		  expected_on_hand numeric,
		  qty_on_hand numeric,
		  sales_trend numeric,
		  purchase_price numeric,
		  status character(1) DEFAULT 'N',
		  --box_capacity integer,
		  CONSTRAINT sodanca_purchase_plan_pkey PRIMARY KEY (id)
		)
		WITH (
		  OIDS = FALSE
		)
		TABLESPACE pg_default;
		ALTER TABLE public.sodanca_purchase_plan
		  OWNER to {login};
		COMMENT ON TABLE public.sodanca_purchase_plan
		  IS 'Reset nightly, used by stock purchase planner';""".format(
			login=config[companycode]['login'])

	#sodanca_purchase_plan_date
	table_queries[2] = """
		CREATE TABLE IF NOT EXISTS public.sodanca_purchase_plan_date (
		  ship_date date NOT NULL,
		  gen_tstamp timestamp NOT NULL,
		  status character(1) NOT NULL
		)
		TABLESPACE pg_default;
		ALTER TABLE public.sodanca_purchase_plan_date
		  OWNER TO {login};
		COMMENT ON TABLE public.sodanca_purchase_plan_date
		  IS 'Updated via function sd_update_pplan_date';
		""".format(login=config[companycode]['login'])

	#sodanca_shipment_schedule
	table_queries[3] = """
		CREATE TABLE IF NOT EXISTS public.sodanca_shipment_schedule
		(
		    id serial NOT NULL,
		    supplier_name character varying(30) NOT NULL,
		    supplier_id integer NOT NULL,
		    cut_off_date date NOT NULL,
		    expected_date date NOT NULL,
		    PRIMARY KEY (id)
		)
		WITH (
		    OIDS = FALSE
		);

		ALTER TABLE public.sodanca_shipment_schedule
		    OWNER to {login};
			""".format(login=config[companycode]['login'])

	#print(table_queries[0]) #DEBUG
	logfilename = config[companycode]['logfilename']
	try:
		cur = conn.cursor()
		for table_query in table_queries:
			cur.execute(table_query)
			conn.commit()
		cur.close()
		log_entry(logfilename,"Purchase plan tables created successfully.")
	except Exception as e:
		log_entry(logfilename, 'Error creating tables. ERR:008')
		log_entry(logfilename,str(e))
		raise

def create_functions(conn,companycode):
	functions_query = ['']*9

	# Quantity Committed
	functions_query[0] = """
		-- Quantity Committed
		CREATE OR REPLACE FUNCTION public.sd_qcomm(
			pid integer,
			start_date date,
			end_date date)
			RETURNS numeric
			LANGUAGE 'sql'

			COST 100
			VOLATILE
		AS $BODY$

		SELECT
			CASE
				WHEN sum(stock_move.product_qty) != 0
				THEN sum(stock_move.product_qty)
				ELSE 0.0 END
			AS product_committed_total
		FROM stock_move
		WHERE
			stock_move.location_dest_id = {customers}
			AND stock_move.location_id = {wh_stock}
			AND (stock_move.state::text = ANY (ARRAY['confirmed'::character varying, 'assigned'::character varying]::text[]))
			AND date_expected >= $2
			AND date_expected < $3
			AND stock_move.product_id = $1
		GROUP BY stock_move.product_id

		$BODY$;

		ALTER FUNCTION public.sd_qcomm(integer, date, date)
			OWNER TO {login};
		""".format(wh_stock = 12, customers = 9, supplier = 8, login = config[companycode]['login'])

	# Quantity on order
	functions_query[1] = """
		-- Quantity on order
		CREATE OR REPLACE FUNCTION public.sd_qoo(
			pid integer,
			start_date date,
			end_date date)
			RETURNS decimal
			LANGUAGE 'sql'

			COST 100
			VOLATILE
		AS $BODY$

		SELECT
			CASE
			WHEN sum(stock_move.product_qty) != 0
			THEN sum(stock_move.product_qty)
			ELSE 0.0 END
			AS on_order_total
		FROM stock_move
		WHERE
			stock_move.location_dest_id = {wh_stock}
			AND stock_move.location_id = {supplier}
			AND (stock_move.state::text = ANY (ARRAY['confirmed'::character varying, 'assigned'::character varying]::text[]))
			AND date_expected >= $2 --now()::date
			AND date_expected <= $3 --now()::date
			AND stock_move.product_id = $1
		GROUP BY stock_move.product_id

		$BODY$;

		ALTER FUNCTION public.sd_qoo(integer, date, date)
			OWNER TO {login};
		""".format(wh_stock = 12, customers = 9, supplier = 8, login = config[companycode]['login'])

	# Quantity Sold
	functions_query[2] = """
		-- Quantity Sold
		CREATE OR REPLACE FUNCTION public.sd_qs(
			pid integer,
			start_date date,
			end_date date)
			RETURNS numeric
			LANGUAGE 'sql'

			COST 100
			VOLATILE
		AS $BODY$

		SELECT
			CASE
				WHEN sum(stock_move.product_qty) != 0
				THEN sum(stock_move.product_qty)
				ELSE 0.0 END
				AS sold_total
		FROM stock_move
		WHERE
			stock_move.location_dest_id = {customers}
			AND stock_move.location_id = {wh_stock}
			AND (stock_move.state::text = 'done'::character varying)
			AND date_expected >= $2 --start_date
			AND date_expected < $3 --end_date
			AND stock_move.product_id = $1
		GROUP BY stock_move.product_id

		$BODY$;

		ALTER FUNCTION public.sd_qs(integer, date, date)
			OWNER TO {login};
		""".format(wh_stock = 12, customers = 9, supplier = 8, login = config[companycode]['login'])

	# Quantity Sold Last year
	functions_query[3] = """
	    -- Quantity Sold Last year
	    CREATE OR REPLACE FUNCTION public.sd_qs_prev_yr(
	    	pid integer,
	    	start_date date,
	    	end_date date)
	        RETURNS numeric
	        LANGUAGE 'sql'

	        COST 100
	        VOLATILE
	    AS $BODY$

	    SELECT
	    	CASE
	        	WHEN sum(stock_move.product_qty) != 0 THEN sum(stock_move.product_qty) ELSE 0.0 END AS sold_last_year_total
	    FROM stock_move
	    WHERE
	    	stock_move.location_dest_id = 9
	        AND stock_move.location_id = 12
	        AND (stock_move.state::text = 'done'::character varying)
	        AND date_expected >= ($2 - interval '1 year') --start_date
	        AND date_expected < ($3 - interval '1 year') --end_date
	        AND stock_move.product_id = $1
	    GROUP BY stock_move.product_id

	    $BODY$;

	    ALTER FUNCTION public.sd_qs(integer, date, date)
	        OWNER TO {login};
		""".format(wh_stock = 12, customers = 9, supplier = 8, login = config[companycode]['login'])

	# Quantity on hand
	functions_query[4] = """
		-- Quantity on hand
		CREATE OR REPLACE FUNCTION sd_qoh(pid int) RETURNS decimal AS
		$$
		  SELECT
			sum(
				CASE
					WHEN (stock_move.location_dest_id IN ( SELECT stock_location.id
					   FROM stock_location
					  WHERE stock_location.usage::text = 'internal'::text)) AND stock_move.state::text = 'done'::text THEN stock_move.product_qty
					ELSE 0.0
				END) - sum(
				CASE
					WHEN (stock_move.location_id IN ( SELECT stock_location.id
					   FROM stock_location
					  WHERE stock_location.usage::text = 'internal'::text)) AND stock_move.state::text = 'done'::text THEN stock_move.product_qty
					ELSE 0.0
				END) AS quantity_on_hand
		   FROM stock_move
		   WHERE stock_move.product_id = $1
		  GROUP BY stock_move.product_id
		$$ LANGUAGE SQL;

		ALTER FUNCTION public.sd_qoh(integer) OWNER TO {login};
		""".format(wh_stock = 12, customers = 9, supplier = 8, login = config[companycode]['login'])

	# Quantity on hand expected
	functions_query[5] = """
		-- Quantity on hand expected
		CREATE OR REPLACE FUNCTION public.sd_expected_onhand( pid integer, start_date date) RETURNS numeric
		LANGUAGE 'sql'
		COST 100
		VOLATILE AS $BODY$
		SELECT (sd_qoh($1)+COALESCE(sd_qoo($1,(now()-'3 months'::interval)::date,$2),0)-COALESCE(GREATEST(sd_qs_prev_yr($1,now()::date,$2),sd_qcomm($1,(now()-'6 months'::interval)::date,$2)),0));
		$BODY$;

		ALTER FUNCTION public.sd_expected_onhand(integer, date) OWNER TO {login};
		""".format(wh_stock = 12, customers = 9, supplier = 8, login = config[companycode]['login'])

	# Sales trend
	functions_query[6] = """
		-- Sales trend
		CREATE OR REPLACE FUNCTION sd_sales_trend(pid int) RETURNS decimal AS
		$$
		SELECT round(sd_qs($1,(now()-'6 months'::interval)::date, now()::date)/sd_qs($1,(now()- '18 months'::interval)::date,(now()- '12 months'::interval)::date)*100,2) as growth;
		$$ LANGUAGE SQL;

		ALTER FUNCTION public.sd_sales_trend(integer) OWNER TO {login};
		""".format(wh_stock = 12, customers = 9, supplier = 8, login = config[companycode]['login'])

	# Quantity to order - Purchase planner
	functions_query[7] = """
		-- Quantity to order - Purchase planner
		CREATE OR REPLACE FUNCTION public.sd_quantity_to_order(
			pid integer,
			start_date date,
			end_date date
		)
		    RETURNS numeric
		    LANGUAGE 'sql'

		    COST 100
		    VOLATILE

		AS $BODY$
		SELECT GREATEST(COALESCE(sd_qs_prev_yr($1,$2,$3),0),COALESCE(sd_qcomm($1,$2,$3),0))-sd_expected_onhand($1,$2) AS qty_to_order from product_product
		$BODY$;

		ALTER FUNCTION public.sd_quantity_to_order(integer, date, date)
			OWNER TO {login};

		-- Quantity to order - Purchase planner
		CREATE OR REPLACE FUNCTION public.sd_quantity_to_order_no_hist(
			pid integer,
			start_date date,
			end_date date
		)
		    RETURNS numeric
		    LANGUAGE 'sql'

		    COST 100
		    VOLATILE

		AS $BODY$

		SELECT GREATEST(sd_qcomm($1,($2-'6 months'::interval)::date,$3))-COALESCE(sd_expected_onhand($1,$2),0) AS qty_to_order from product_product

		$BODY$;

		ALTER FUNCTION public.sd_quantity_to_order_no_hist(integer, date, date)
			OWNER TO {login};
		""".format(wh_stock = 12, customers = 9, supplier = 8, login = config[companycode]['login'])

	# sd_update_pplan_date
	functions_query[8] = """
		--sd_update_pplan_date
		CREATE OR REPLACE FUNCTION sd_update_pplan_date(sdate date default '1970-01-01' ) RETURNS integer AS $$
		DECLARE
			a_count integer;
			b_count integer;
			c_count integer;
		BEGIN
			UPDATE sodanca_purchase_plan_date set status = 't' WHERE status ='c';
			GET DIAGNOSTICS a_count = ROW_COUNT;
			IF sdate == '1970-01-01' THEN
				INSERT INTO sodanca_purchase_plan_date (ship_date,gen_tstamp,status) VALUES (((SELECT ship_date FROM sodanca_purchase_plan_date WHERE status = 't')::date+'1 week'::interval)::date , now(),'c');
			ELSE
				INSERT INTO sodanca_purchase_plan_date (ship_date,gen_tstamp,status) VALUES (sdate, now(),'c');
			END IF;
			GET DIAGNOSTICS b_count = ROW_COUNT;
			UPDATE sodanca_purchase_plan_date set status = 'o' WHERE status ='t';
			GET DIAGNOSTICS c_count = ROW_COUNT;
			RETURN a_count+b_count+c_count;
		END;
		$$
		LANGUAGE 'plpgsql' VOLATILE;

		ALTER FUNCTION public.sd_update_pplan_date(date)
		    OWNER TO {login};
		""".format(login = config[companycode]['login'])

			#config[companycode]['login']
			#print('functions_query[6]',functions_query[6]) #DEBUG
	logfilename = config[companycode]['logfilename']
	try:
		cur = conn.cursor()
		for function_query in functions_query:
			#print('--'*120)
			#print(function_query) #DEBUG
			cur.execute(function_query)
			conn.commit()
		cur.close()
		log_entry(logfilename,"Functions created successfully.")
	except Exception as e:
		log_entry(logfilename, 'Error creating functions. ERR:009')
		log_entry(logfilename,str(e))
		raise

def add_check_digit(upc_str):

	upc_str = str(upc_str)
	if len(upc_str) != 12:
		raise Exception("Invalid length")

	odd_sum = 0
	even_sum = 0
	for i, char in enumerate(upc_str):
		j = i+1
		if j % 2 == 0:
			even_sum += int(char)
		else:
			odd_sum += int(char)

	total_sum = (odd_sum * 3) + even_sum
	mod = total_sum % 10
	check_digit = 10 - mod
	if check_digit == 10:
		check_digit = 0
	return upc_str + str(check_digit)

def parse_attachments(conn, companycode):

	filepath = config[companycode]['filepath']
	cur = conn.cursor()
	logfilename = config[companycode]['logfilename']

	email_date = now = (datetime.datetime.now()).strftime('%Y-%m-%d')

	check_table_query = "select * from information_schema.tables where table_name = '{0}'".format('sodanca_estoque_pulmao')
	# print(check_table_query)
	cur.execute(check_table_query)
	num_tables = cur.fetchone()
	# print(num_tables)


	create_barcode_audit_query = """
			DROP TABLE IF EXISTS public.sodanca_pp_barcode_audit;

		CREATE TABLE public.sodanca_pp_barcode_audit
		(
			barcode integer NOT NULL,
			product_description character varying(128) COLLATE pg_catalog."default",
			CONSTRAINT sodanca_pp_barcode_audit_pkey PRIMARY KEY (barcode)
		)
		WITH (
			OIDS = FALSE
		)
		TABLESPACE pg_default;

		ALTER TABLE public.sodanca_pp_barcode_audit
			OWNER to {login};
	""".format(login = config[companycode]['login'])
	try:
		cur.execute(create_barcode_audit_query)
	except Exception as e:
		now = (datetime.datetime.now()).strftime('%H:%M:%s %Y-%m-%d')
		log_str = "Cannot drop table sodanca_pp_barcode_audit. ERR:102 {0}\n\n{1}".format(now, str(e))

		log_entry(logfilename, log_str)

	if num_tables == None:
		create_table_sql = """
			CREATE TABLE public.sodanca_estoque_pulmao
			(
				id serial NOT NULL,
				email_date date NOT NULL,
				product_id integer NOT NULL,
				product_name character varying(64) COLLATE pg_catalog."default",
				quantity numeric,
				quantity_available numeric,
				CONSTRAINT sodanca_estoque_pulmao_pkey PRIMARY KEY (id)
			)
			WITH (
				OIDS = FALSE
			)
			TABLESPACE pg_default;

			ALTER TABLE public.sodanca_estoque_pulmao
				OWNER to {login};
			COMMENT ON TABLE public.sodanca_estoque_pulmao
				IS 'This is updated daily from the email sent from Soles, by default the data is cycled every 12 months, this can be adjusted on the config file';
		""".format(login = config[companycode]['login'])
		try:
			cur.execute(create_table_sql)
			conn.commit()
		except Exception as e:
			now = (datetime.datetime.now()).strftime('%H:%M:%s %Y-%m-%d')
			log_str = "Cannot create table sodanca_estoque_pulmao. ERR:012 {1} \n {0}".format(str(e), now)

			log_entry(logfilename,log_str)

	for fn in os.listdir('attachments'):
		filename = filepath+fn
		fileobj = open(filename, 'rt', encoding='iso-8859-1')
		lines = list(csv.reader(fileobj, delimiter=';'))

		for line in lines[1:]:
			qty_in_hotstock =int(line[6])
			product_barcode = add_check_digit(line[13])
			# print("'{0}',".format(product_barcode))

			product_query = """SELECT product_product.id, product_product.name FROM product_barcode
				LEFT JOIN product_product ON product_product.id = product_barcode.product_id
				WHERE product_barcode.barcode = '{0}'
			""".format(str(product_barcode))

			try:
				cur.execute(product_query)
				products = cur.fetchall()
				if len(products) == 0:
					# print(product_barcode, line)
					now = (datetime.datetime.now()).strftime('%H:%M:%s %Y-%m-%d')
					log_str = '{2} Barcode not defined in database barcode {0}, product details {1}'.format(product_barcode, line, now)

					description = line[0]+line[1]+line[2]+line[3]+line[4]+line[5]
					insert_query = "INSERT INTO sodanca_pp_barcode_audit (barcode, product_description) VALUES ({0},{1})".format(product_barcode,description)
					# log_entry(logfilename,log_str)

				for product in products:
					product_id = product[0]
					product_name = product[1]

					insert_query = """ INSERT INTO sodanca_estoque_pulmao (--id,
					email_date, product_id, product_name, quantity, quantity_available) VALUES (
						--default,
						'{0}', {1}, '{2}', {3}, {3})""".format(email_date, product_id, product_name, qty_in_hotstock)
					cur.execute(insert_query)
					conn.commit()

			except Exception as e:
				now = (datetime.datetime.now()).strftime('%H:%M:%s %Y-%m-%d')
				log_str = "Error inserting in sodanca_estoque_pulmao. ERR:103 {0}\n\n{1}".format(now, str(e))

				log_entry(logfilename, log_str)
				pass
		fileobj.close()
	cur.close()

def next_shipping_date(weekday_ship): #weekday number Monday is 0 Sunday is 6
	now = datetime.datetime.now()
	# weekday_ship = 4
	now_weekday = int(now.strftime('%w'))
	# print('DEBUG weekday',now_weekday)
	# if now_weekday <= 2: #Monday or Tuesday
	days_ahead = weekday_ship - now_weekday
	if days_ahead <= 2: # Target day already happened this week
		days_ahead += 7

	else:
		# days_ahead = weekday_ship - now_weekday
		# if days_ahead <= 0: # Target day already happened this week
		days_ahead += 14
	next_date = (now + datetime.timedelta(days_ahead)).strftime('%Y-%m-%d')
	# print('DEBUG weekday text',next_date)
	return (next_date)

def create_hotstock_order(conn, companycode):

	parse_attachments(conn,companycode)
	# print('create_hotstock_order called')
	hotstock_query = """SELECT sodanca_estoque_pulmao.* , sodanca_purchase_plan.id as PP_id, sodanca_purchase_plan.qty_2_ord as PP_q2o,
		sodanca_purchase_plan.qty_2_ord_adj as PP_q2oAdj, sodanca_purchase_plan.*
		FROM sodanca_estoque_pulmao LEFT JOIN sodanca_purchase_plan ON sodanca_estoque_pulmao.product_id = sodanca_purchase_plan.product_id
		WHERE sodanca_estoque_pulmao.email_date = (SELECT MAX(email_date) FROM sodanca_estoque_pulmao) AND sodanca_purchase_plan.type = 'R' """

	# print("DEBUG hotstock_query", hotstock_query)
	cur = conn.cursor()

	now_date = (datetime.datetime.now()).strftime('%Y-%m-%d')
	logfilename = config[companycode]['logfilename']

	now_start = datetime.datetime.now()

	log_str = "Starting run -- Hot stock {0}".format(datetime.datetime.now().strftime('%H:%M:%S - %Y-%m-%d'))
	log_entry(logfilename,log_str)

	try:
		cur.execute(hotstock_query)
		hs_lines = cur.fetchall()
	except Exception as e:
		log_str = "ERR:114\n" + str(e)
		log_entry(logfilename, log_str)
		raise
		sys.exit(1)
	for hs_line in hs_lines:
		pp_q2o = hs_line[7]
		ep_qa = hs_line[5]
		pp_lin_id = hs_line[6]
		ep_lin_id = hs_line[0]
		expected_date = next_shipping_date(4)
		vendor = hs_line[11]
		vendor_group = hs_line[12]
		creation_date = now_date
		template_id = hs_line[15]
		template_name = hs_line[16]
		product_id = hs_line[17]
		product_name = hs_line[18]
		product_category_id = hs_line[19]
		product_grade = hs_line[20]
		order_mod = hs_line[21]
		# qty_2_ord = hs_line[13]
		# qty_2_ord_adj = hs_line[14]
		qty_on_order = hs_line[24]
		qty_on_order_period = hs_line[25]
		qty_committed = hs_line[26]
		qty_sold = hs_line[27]
		expected_on_hand = hs_line[28]
		qty_on_hand = hs_line[29]
		sales_trend = hs_line[30]
		purchase_price = hs_line[31]
		# print('DEBUG hs_line:', hs_line)

		if pp_q2o > ep_qa:
			try:

				pp_new_q2o = ep_qa
				pp_order_qty = pp_q2o-ep_qa
				pp_order_qty_adj = roundup(pp_order_qty,order_mod)
				ep_avail_qty = 0

				insert_query = """INSERT INTO sodanca_purchase_plan (id, type, vendor, vendor_group, creation_date, expected_date, template_id, template_name, product_id,
					product_name, product_category_id, product_grade, order_mod, qty_2_ord, qty_2_ord_adj, qty_on_order, qty_on_order_period, qty_committed, qty_sold,
					expected_on_hand, qty_on_hand, sales_trend, purchase_price) VALUES (default, 'H', {0}, {1}, '{2}'::date, '{3}'::date, {4}, '{5}', {6}, '{7}', {8}, '{9}', {10}, {11}, {12}, {13}, {14},
					{15}, {16}, {17}, {18}, {19}, {20})""".format(vendor, vendor_group, creation_date, expected_date, template_id, template_name, product_id, product_name, product_category_id,
					product_grade, 1, pp_new_q2o, pp_new_q2o, qty_on_order, qty_on_order_period, qty_committed, qty_sold, expected_on_hand, qty_on_hand, sales_trend, purchase_price)
				# print('DEBUG insert_query',insert_query)
				cur2 = conn.cursor()
				cur2.execute(insert_query)
				conn.commit()
				cur2.close()

			except Exception as e:
				now = (datetime.datetime.now()).strftime('%H:%M:%s %Y-%m-%d')
				log_str = "Error updating orders with hot stock quantities. ERR:108 {0}\n\n{1}".format(now, str(e))
				log_entry(logfilename, log_str)

			try:
				if pp_order_qty > 0:
					update_query = """UPDATE sodanca_purchase_plan SET qty_2_ord = {0}, qty_2_ord_adj = {1} WHERE id = {2}""".format(pp_order_qty, pp_order_qty_adj, pp_lin_id)
				elif pp_order_qty == 0:
					update_query = """DELETE FROM sodanca_purchase_plan WHERE id = {0}""".format(pp_lin_id)
				else:
					now = (datetime.datetime.now()).strftime('%H:%M:%s %Y-%m-%d')
					log_str = "Updating hotstock order, quantity does not match > 0 or == 0, ERR:121 - sodanca_purchase_plan line id: {0} - {1}\n".format(pp_lin_id,now)
					log_entry(logfilename, log_str)
				# print('DEBUG update 1', update_query)
				cur2 = conn.cursor()
				cur2.execute(update_query)
				conn.commit()
				cur2.close()
				cur2 = conn.cursor()

			except Exception as e:
				now = (datetime.datetime.now()).strftime('%H:%M:%s %Y-%m-%d')
				log_str = "Error updating orders with hot stock quantities. ERR:109 {0}\n\n{1}".format(now, str(e))
				log_entry(logfilename, log_str)

			try:
				update_query = """UPDATE sodanca_estoque_pulmao SET quantity_available = {0} WHERE id = {1}""".format(0,ep_lin_id)
				# print('DEBUG update 2', update_query)
				cur2 = conn.cursor()
				cur2.execute(update_query)
				conn.commit()
				cur2.close()

			except Exception as e:
				now = (datetime.datetime.now()).strftime('%H:%M:%s %Y-%m-%d')
				log_str = "Error updating orders with hot stock quantities. ERR:110 {0}\n\n{1}".format(now, str(e))
				log_entry(logfilename, log_str)

		elif pp_q2o <= ep_qa:
			try:
				pp_new_q2o = pp_q2o
				pp_order_qty = 0
				pp_order_qty_adj = 0
				ep_avail_qty = ep_qa - pp_q2o

				insert_query = """INSERT INTO sodanca_purchase_plan (id, type, vendor, vendor_group, creation_date, expected_date, template_id, template_name, product_id,
					product_name, product_category_id, product_grade, order_mod, qty_2_ord, qty_2_ord_adj, qty_on_order, qty_on_order_period, qty_committed, qty_sold,
					expected_on_hand, qty_on_hand, sales_trend, purchase_price) VALUES (default, 'H', {0}, {1}, '{2}'::date, '{3}'::date, {4}, '{5}', {6}, '{7}', {8}, '{9}', {10}, {11}, {12}, {13}, {14},
					{15}, {16}, {17}, {18}, {19}, {20})""".format(vendor, vendor_group, creation_date, expected_date, template_id, template_name, product_id, product_name, product_category_id,
					product_grade, 1, pp_new_q2o, pp_new_q2o, qty_on_order, qty_on_order_period, qty_committed, qty_sold, expected_on_hand, qty_on_hand, sales_trend, purchase_price)
				# print('DEBUG insert_query',insert_query)
				cur2 = conn.cursor()
				cur2.execute(insert_query)
				conn.commit()
				cur2.close()

			except Exception as e:
				now = (datetime.datetime.now()).strftime('%H:%M:%s %Y-%m-%d')
				log_str = "Error updating orders with hot stock quantities. ERR:105 {0}\n\n{1}".format(now, str(e))
				log_entry(logfilename, log_str)
				raise

			try:
				if pp_order_qty > 0:
					update_query = """UPDATE sodanca_purchase_plan SET qty_2_ord = {0}, qty_2_ord_adj = {1} WHERE id = {2}""".format(pp_order_qty, pp_order_qty_adj, pp_lin_id)
				elif pp_order_qty == 0:
					update_query = """DELETE FROM sodanca_purchase_plan WHERE id = {0}""".format(pp_lin_id)
				else:
					now = (datetime.datetime.now()).strftime('%H:%M:%s %Y-%m-%d')
					log_str = "Updating hotstock order, quantity does not match > 0 or == 0, ERR:121 - sodanca_purchase_plan line id: {0} - {1}\n".format(pp_lin_id,now)
					log_entry(logfilename, log_str)
				# update_query = """UPDATE sodanca_purchase_plan SET qty_2_ord = {0}, qty_2_ord_adj = {1} WHERE id = {2}""".format(pp_order_qty, pp_order_qty_adj, pp_lin_id)
				# print('DEBUG update 1', update_query)
				cur2 = conn.cursor()
				cur2.execute(update_query)
				conn.commit()
				cur2.close()
				cur2 = conn.cursor()

			except Exception as e:
				now = (datetime.datetime.now()).strftime('%H:%M:%s %Y-%m-%d')
				log_str = "Error updating orders with hot stock quantities. ERR:106 {0}\n\n{1}".format(now, str(e))
				log_entry(logfilename, log_str)
				raise

			try:
				update_query = """UPDATE sodanca_estoque_pulmao SET quantity_available ={0} WHERE id = {1}""".format(0,ep_lin_id)
				# print('DEBUG update 2', update_query)
				cur2 = conn.cursor()
				cur2.execute(update_query)
				conn.commit()
				cur2.close()

			except Exception as e:
				now = (datetime.datetime.now()).strftime('%H:%M:%s %Y-%m-%d')
				log_str = "Error updating orders with hot stock quantities. ERR:107 {0}\n\n{1}".format(now, str(e))
				log_entry(logfilename, log_str)
				raise

	now_finish = datetime.datetime.now()
	run_time = now_finish-now_start
	log_str="Ending run -- Hot Stock {0}\nRun time: {1}".format(now_finish.strftime('%H:%M:%S - %Y-%m-%d'), str(run_time))

	cur.close()

def check_ship_date(conn, companycode):
	cur = conn.cursor()
	logfilename = config[companycode]['logfilename']

	check_date_query = "SELECT * FROM sodanca_purchase_plan_date WHERE status = 'c'"

	try:
		cur.execute(check_date_query)
		numdates = cur.rowcount
		ship_date = cur.fetchall()
		if numdates > 1:
			log_str = "Something is off, too many current dates ERR:112\n"
			for sdate in ship_date:
				log_str += sdate[0]
			log_entry(logfilename, log_str)
		elif numdates == 1:
			cur.close()
			dtime_shipdate = ship_date[0][0] #datetime.datetime.strptime(ship_date[0][0], '%Y-%m-%d')
			return dtime_shipdate
		else:
			return 0
	except Exception as e:
		log_str = "ERR:113\n" + str(e)
		log_entry(logfilename, log_str)
		raise
		sys.exit(1)
### --------------------------------INTERACTIVE INTERFACE -------------------------------- ###

def main_menu():
	# os.system('clear')
	print('SO DANCA PURCHASE PLANNER\n')
	print('-'*25+'Interactive interface'+'-'*25+'\n')
	print('These are the configured companies:\n')
	for key in config:
		if key == 'DEFAULT':
			pass
		else:
			print (key)
	print('\n')
	# print('1 - List/select configured companies')
	print('1 - Run purchase plan manually')
	print('2 - Update/Install configuration')
	print('Q - Quit')
	choice = input(" >> ")
	exec_menu(choice)
	return

def exec_menu(choice):
	# os.system('clear')
	#ch = choice.lower()
	ch = choice
	if ch == '':
		menu_actions['main_menu']()
	else:
		try:
			menu_actions[ch]()
		except KeyError:
			print('Invalid selection. Please try again. \n')
			menu_actions['main_menu']()
	return

def back():
	menu_actions['main_menu']()

def exit():
	sys.exit(0)

def run_all(conn , companycode):
	logfilename = config[companycode]['logfilename']
	lead_normal = int(config[companycode]['lead_normal'])
	plan_period_a = int(config[companycode]['plan_period_a'])
	plan_period_b = int(config[companycode]['plan_period_b'])
	plan_period_c = int(config[companycode]['plan_period_c'])
	plan_period_d = int(config[companycode]['plan_period_d'])

	try:
		create_order(conn, 'N', 'A', plan_period_a, companycode)
		create_order(conn, 'N', 'B', plan_period_b, companycode)
		create_order(conn, 'N', 'C', plan_period_b, companycode)
		create_order(conn, 'R', 'A', plan_period_a, companycode)
		create_order(conn, 'R', 'B', plan_period_b, companycode)
		create_order(conn, 'R', 'C', plan_period_c, companycode)
		create_order(conn, 'R', 'D', plan_period_d, companycode)

		create_hotstock_order(conn, companycode)
		create_tights_order(conn,companycode)

	except KeyboardInterrupt:
		print("Interrupted by user")
		log_entry(logfilename,"Interrupted by user. ERR:006\n")

	except Exception as e:
		log_str = "Something unexpected happened. ERR:007\n\n"+str(e)
		log_entry(logfilename,log_str)
		raise
		pass

def manual_run():
	# os.system('clear')

	types_list = ['R','N','H','T']
	types_descrition = ['Rush','Normal','Hot stock', 'Tights']
	grades_list = ['A','B','C','D']
	print('\nSelect company to to run:')

	company_idx = []
	for key in config:
		company_idx.append(key)

	for k in range(1, len(company_idx)):
		print(k,'-',company_idx[k])

	print('\nM - Main Menu')
	print('Q - Quit')
	while True:
		choice = input(" >> ")
		ch = choice.lower()

		print(ch)
		if ch == 'q':
			print('Good bye!')
			sys.exit(0)
		elif ch == 'm':
			raise
			main_menu()
			break
		elif int(ch) in range(1,len(company_idx)):
			companycode = company_idx[int(ch)]
			break

		else:
			print('Not a valid option. Try again')

	print('\nCompany selected - ',companycode,'\n')

	dbname = config[companycode]['db_name']
	db_server_address = config[companycode]['db_server_address']
	login = config[companycode]['login']
	passwd = config[companycode]['passwd']

	logfilename = config[companycode]['logfilename']#'purchase_planner.log'

	try:
		dsn = ("dbname={0} host={1} user={2} password={3}").format(dbname, db_server_address, login, passwd)
		conn = psycopg2.connect(dsn)
		conn.set_session(autocommit=True)
		log_entry(logfilename,"\n\nProcess started - {0}\n".format((datetime.datetime.now().strftime('%H:%M:%S - %Y-%m-%d'))))
		#print('dsn: {0}\n companycode: {1} \n conn: {2}\n'.format(dsn,companycode,conn)) #DEBUG

	except Exception as e:
		log_str = "I am unable to connect to the database, check companycode ERR:100\n\n" + str(e)
		print(logfilename,log_str)
		log_entry(logfilename,log_str)

	while True:
		print('Select run procedure:')
		print(' Run (A)ll')
		print(' Run by product (G)rade')
		print(' Run by order (T)ype')
		print(' Run (S)ingle selection')
		print('\n M - Main menu')
		print(' Q - Quit')
		choice = input(" >> ")
		ch = choice.lower()
		print('\nOption selected:',choice)

		run_choice = ch
		if run_choice in ['a','g','t','s']:
			break
		elif ch == 'q':
			print('Good bye!')
			sys.exit(0)
		elif ch == 'm':
			main_menu()
			break
		else:
			os.system('clear')
			print('Not a valid option. Try again\n')

	plan_period = {}
	for grade in grades_list:
		varname = 'plan_period_'+str(grade)
		plan_period[grade] =  int(config[companycode][varname])

	if run_choice == 'a':

		log_str = ('Manual run started - Running all grades and order types - started at:{}').format((datetime.datetime.now().strftime('%H:%M:%S - %Y-%m-%d')))
		start_clock = datetime.datetime.now()
		log_entry(config[companycode]['logfilename'],log_str)

		run_all(conn,companycode)

		log_str = 'Manual run - Completion time: {}'.format(datetime.datetime.now().strftime('%H:%M:%S - %Y-%m-%d'))
		log_entry(logfilename,log_str)
		run_time = datetime.datetime.now()- start_clock
		log_entry(logfilename,'Runtime: '+str(run_time))
		log_entry(logfilename,"="*80+"\n")

		log_str = 'Manual run - Starting Hot stock ordering: {}'.format(datetime.datetime.now().strftime('%H:%M:%S - %Y-%m-%d'))
		log_entry(logfilename,log_str)
		create_hotstock_order(conn, companycode)
		run_time = datetime.datetime.now()- start_clock
		log_entry(logfilename,'Runtime: '+str(run_time))
		log_entry(logfilename,"="*80+"\n")

	elif run_choice == 'g':
		while True:
			print('Select product grade to process:')
			for grade in grades_list:
				print(grade)
			choice = input(" >> ")
			run_grade = choice.upper()

			if run_grade in grades_list:
				break
			else:
				print('Option not valid')

		while True:
			print('Clear current results table? (Y/N)')
			choice = input(" >> ")
			ch = choice.lower()
			clear_table =  ch
			if clear_table in ['y','n']:
				break
			else:
				print('Option not valid')

		if clear_table == 'y':
			try:
				drop_results_table(conn,companycode)
				log_str = "Results table cleared."
				log_entry(config[companycode]['logfilename'],log_str)
			except Exception as e:
				log_entry(logfilename,'Could not clear table'+str(e))
				raise

		elif clear_table == 'n':
			pass

		log_str = ('Manual run started - Running only {0} grade and all order types - started at:{1}').format(run_grade,(datetime.datetime.now().strftime('%H:%M:%S - %Y-%m-%d')))
		start_clock = datetime.datetime.now()
		log_entry(config[companycode]['logfilename'],log_str)

		for order_type in types_list:
			create_order(conn, order_type, run_grade, plan_period[run_grade], companycode)

		log_str = 'Manual run - Completion time: {}'.format(datetime.datetime.now().strftime('%H:%M:%S - %Y-%m-%d'))
		log_entry(logfilename,log_str)
		run_time = datetime.datetime.now()- start_clock
		log_entry(logfilename,'Runtime: '+str(run_time))
		log_entry(logfilename,"="*80+"\n")

		log_str = 'Manual run - Starting Hot stock ordering: {}'.format(datetime.datetime.now().strftime('%H:%M:%S - %Y-%m-%d'))
		log_entry(logfilename,log_str)
		create_hotstock_order(conn, companycode)
		log_entry(logfilename,'Runtime: '+str(datetime.datetime.now()- start_clock))
		log_entry(logfilename,"="*80+"\n")


	elif run_choice == 't':
		while True:
			print('Select order type to process:')
			for k in range(0, len(types_list)):
				print("[{0}] - {1}".format(types_list[k],types_descrition[k]))
			choice = input(" >> ")
			order_type = choice.upper()

			if order_type in types_list:
				break
			else:
				print('Option not valid')

		while True:
			print('Clear current results table? (Y/N)')
			choice = input(" >> ")
			ch = choice.lower()
			clear_table =  ch
			if clear_table in ['y','n']:
				break
			else:
				print('Option not valid')

		if clear_table == 'y':
			try:
				drop_results_table(conn,companycode)
				log_str = "Results table cleared."
			except Exception as e:
				log_entry(logfilename,'Could not clear table'+str(e))
				raise

		elif clear_table == 'n':
			pass


		if order_type in ['R','N']:
			start_clock = datetime.datetime.now()
			log_str = ('Manual run started - Running all grades and only order type {0} - started at:{1}').format(order_type,(start_clock.strftime('%H:%M:%S - %Y-%m-%d')))
			log_entry(config[companycode]['logfilename'],log_str)

			for grade in grades_list:

				if grade in ['C','D'] and order_type == 'N':
					log_str = 'Skipping order grade {0}, type {1} - {2}'.format(grade, order_type, datetime.datetime.now().strftime('%H:%M:%S - %Y-%m-%d'))
					log_entry(logfilename,log_str)
				else:
					create_order(conn, order_type, grade, plan_period[grade], companycode)

			log_str = 'Manual run - Completion time: {0}\n'.format(datetime.datetime.now().strftime('%H:%M:%S - %Y-%m-%d'))
			log_entry(logfilename,log_str)
			run_time = datetime.datetime.now()- start_clock
			log_entry(logfilename,'Runtime: '+str(run_time))
			log_entry(logfilename,log_str)
			log_entry(logfilename,"="*80+"\n")
		elif order_type == 'H':
			start_clock = datetime.datetime.now()
			log_str = 'Manual run - Starting Hot stock ordering: {}'.format(start_clock.strftime('%H:%M:%S - %Y-%m-%d'))
			log_entry(logfilename,log_str)
			create_hotstock_order(conn, companycode)
			run_time = datetime.datetime.now()- start_clock
			log_entry(logfilename,'Runtime: '+str(run_time))
			log_entry(logfilename,log_str)
			log_entry(logfilename,"="*80+"\n")
		elif order_type == 'T':
			start_clock = datetime.datetime.now()
			log_str = 'Manual run - Starting Tights ordering: {}'.format(start_clock.strftime('%H:%M:%S - %Y-%m-%d'))
			log_entry(logfilename,log_str)
			create_tights_order(conn, companycode)
			run_time = datetime.datetime.now()- start_clock
			log_entry(logfilename,'Runtime: '+str(run_time))
			log_entry(logfilename,log_str)
			log_entry(logfilename,"="*80+"\n")


	elif run_choice == 's':
		while True:
			print('\nSelect order type to process:')
			for order_type in types_list:
				print(order_type)
			choice = input(" >> ")
			run_type = choice.upper()

			if order_type in types_list:
				break
			else:
				print('Option not valid')

		while True:
			print('\nSelect product grade to process:')
			for grade in grades_list:
				print(grade)
			choice = input(" >> ")
			run_grade = choice.upper()

			if run_grade in grades_list:
				break
			else:
				print('Option not valid')

		while True:
			print('Clear current results table? (Y/N)')
			choice = input(" >> ")
			ch = choice.lower()
			clear_table =  ch
			if clear_table in ['y','n']:
				break
			else:
				print('Option not valid')

		if clear_table == 'y':
			try:
				drop_results_table(conn,companycode)
				log_str = "Results table cleared."
			except Exception as e:
				log_entry(logfilename,'Could not clear table'+str(e))
				raise

		elif clear_table == 'n':
			pass

		start_clock = datetime.datetime.now()
		if order_type in ['R','N']:
			log_str = ('Manual run started - Running only grade {0} and only order type {1} - started at:{2}').format(run_grade, order_type, (datetime.datetime.now().strftime('%H:%M:%S - %Y-%m-%d')))
			log_entry(config[companycode]['logfilename'],log_str)
			# print(order_type)
			create_order(conn, order_type, run_grade, plan_period[run_grade], companycode)

			log_str = 'Manual run - Completion time: {}'.format(datetime.datetime.now().strftime('%H:%M:%S - %Y-%m-%d'))
			log_entry(logfilename,log_str)
			run_time = datetime.datetime.now()- start_clock
			log_entry(logfilename,'Runtime: '+str(run_time))
			log_entry(logfilename,"="*80+"\n")
		elif order_type == 'H':
			log_str = 'Manual run - Starting Hot stock ordering: {}'.format(datetime.datetime.now().strftime('%H:%M:%S - %Y-%m-%d'))
			log_entry(logfilename,log_str)
			create_hotstock_order(conn, companycode)
			run_time = datetime.datetime.now()- start_clock
			log_entry(logfilename,'Runtime: '+str(run_time))
			log_entry(logfilename,"="*80+"\n")


	else:
		log_str="{} Something went wrong. ERR:010".format(datetime.datetime.now().strftime('%H:%M:%S - %Y-%m-%d'))
		log_entry(logfilename,log_str)

def install_update():
	print('Install_update')
	print('\nSelect company to to run:')

	company_idx = []
	for key in config:
		company_idx.append(key)

	for k in range(1, len(company_idx)):
		print(k,'-',company_idx[k])

	print('\nM - Main Menu')
	print('Q - Quit')
	while True:
		choice = input(" >> ")
		ch = choice.lower()

		print(ch)
		if ch == 'q':
			print('Good bye!')
			sys.exit(0)
		elif ch == 'm':
			raise
			main_menu()
			break
		elif int(ch) in range(1,len(company_idx)):

			companycode = company_idx[int(ch)]
			print('\nCompany selected - ',companycode,'\n')
			break

		else:
			print('Not a valid option. Try again')



	dbname = config[companycode]['db_name']
	db_server_address = config[companycode]['db_server_address']
	login = config[companycode]['login']
	passwd = config[companycode]['passwd']

	logfilename = config[companycode]['logfilename']#'purchase_planner.log'
	# print(logfilename) #DEBUG
	try:

		dsn = ("dbname={0} host={1} user={2} password={3}").format(dbname, db_server_address, login, passwd)
		conn = psycopg2.connect(dsn)
		conn.set_session(autocommit=True)
		log_entry(logfilename,"\n\nSetup started - {0}\n".format((datetime.datetime.now().strftime('%H:%M:%S - %Y-%m-%d'))))
		# print('dsn: {0}\n companycode: {1} \n conn: {2}\n'.format(dsn,companycode,conn)) #DEBUG
		print('Creating functions')
		create_functions(conn, companycode)
		print('Functions created')
		print('Creating tables')
		create_tables(conn, companycode)
		print('Tables created')
		print('Checking if ship date exists.')
		ship_date = check_ship_date(conn, companycode)
		cur = conn.cursor()
		if ship_date == 0:
			print('There is no ship date defined')
			print('Define current ship date? (y/n)')
			choice = input(" >> ")
			ch = choice.lower()

			if ch == 'y':
				while 1:
					print('Enter current ship date in "YYYY-MM-DD" format')
					sdate = input (" >> ")
					sdate_query = "INSERT INTO sodanca_purchase_plan_date (ship_date,gen_tstamp,status) VALUES ('{0}', now(),'c');".format(sdate)

					try:
						cur.execute(sdate_query)
						break
					except Exception as e:
						log_str = "Could not insert date. Check format is 'YYYY-MM-DD'.\n {0}".format(str(e))
						log_entry(logfilename,log_str)
			else:
				print('Exiting program.')
				sys.exit(1)

		else:
			print('Current ship date defined as',ship_date)
			print('Would you like to change it? (y/n)')
			while 1:
				choice = input(" >> ")
				ch = choice.lower()
				if ch == 'y':
					print("Enter new ship date in format 'YYYY-MM-DD'")
					sdate = input(" >> ")
					sdate_query = "SELECT sd_update_pplan_date({0})".format(sdate)
					try:
						cur.execute()
						break
					except Exception as e:
						log_str = "Could not update ship date. Check format is 'YYYY-MM-DD'.\n ERR:115{0}".format(str(e))
						log_entry(logfilename,log_str)
						print('Exiting program')
						sys.exit(1)
				elif ch == 'n':
					print('Leaving current ship date as {0}'.format(ship_date))
					print('Exiting program')
					sys.exit(1)
				else:
					print("Please choose (y) or (n)")



	except Exception as e:
		log_str = "I am unable to connect to the database, check companycode ERR:111\n\n" + str(e)
		print(logfilename,log_str)
		log_entry(logfilename,log_str)

### ------------------------------------ MAIN() ------------------------------------------ ###

def main(companycode):
	dbname = config[companycode]['db_name']
	db_server_address = config[companycode]['db_server_address']
	login = config[companycode]['login']
	passwd = config[companycode]['passwd']

	logfilename = config[companycode]['logfilename']#'purchase_planner.log'

	try:
		dsn = ("dbname={0} host={1} user={2} password={3}").format(dbname, db_server_address, login, passwd)
		conn = psycopg2.connect(dsn)
		conn.set_session(autocommit=True)
		# print('dsn: {0}\n companycode: {1} \n conn: {2}\n'.format(dsn,companycode,conn)) #DEBUG
		log_entry(logfilename,"\n\nProcess started - {0}\n".format((datetime.datetime.now().strftime("%H:%M:%S - %Y-%m-%d"))))
		drop_results_table(conn,companycode)
		log_str = ("Running all grades and order types - started at:{}").format((datetime.datetime.now().strftime("%H:%M:%S - %Y-%m-%d")))
		start_clock = datetime.datetime.now()
		log_entry(config[companycode]['logfilename'],log_str)

		run_all(conn, companycode)
		log_str = "Runtime: "+str(datetime.datetime.now()- start_clock)
		log_entry(logfilename,log_str)
		log_entry(logfilename,"="*80+"\n")


	except Exception as e:
		log_str = "I am unable to connect to the database ERR:101\n\n"+ str(e)
		# print(logfilename,log_str)
		log_entry(logfilename,log_str)



# fil.close()
	# print(vendor_parent)
### --------------------------------- GLOBAL SECTION -------------------------------------- ###

config = configparser.ConfigParser()
config.sections()
config.read('config.ini')

### ----------------------------- MENU DEFINITIONS ---------------------------------------- ###

menu_actions = {
	'main_menu' : main_menu,
	'1' : manual_run,
	'2' : install_update,
	'm' : back,
	'q' : exit
}

### -------------------------------- MAIN CALL -------------------------------------------- ###

try:
	cmd_param = sys.argv[1]
except Exception as e:
	print('Missing argument. Try {} -h for help\n'.format(sys.argv[0]))
	sys.exit(2)

if cmd_param in config:
	companycode = str(cmd_param)
	main(companycode)
elif cmd_param == '-i':
	os.system('clear')
	print("Starting interactive mode")
	main_menu()
elif cmd_param == '-h':
	help_str = (open('README','r')).read()
	print(help_str)

else:
	print(cmd_param, 'is not a valid option. Use a company code or -i for interactive mode or try -h for help.\n')
	sys.exit(2)
