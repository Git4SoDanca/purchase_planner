#!/usr/bin/python3
#
# Small script to show PostgreSQL and Pyscopg together
#

import psycopg2
import datetime
from dateutil import rrule
import math

def roundup(x,y):
  return int(math.ceil(x/y))*y;

class reg(object):
    def __init__(self, cursor, registro):
        for (attr, val) in zip((d[0] for d in cursor.description),registro) :
            setattr(self, attr, val)

try:
    conn = psycopg2.connect("dbname='OE-BackupProd-USA-20171117' host='192.168.100.70' user='sodanca' password='iZ638GD'")

except:
    print("I am unable to connect to the database")

#global variables

cur = conn.cursor()
cur2 = conn.cursor()
# cur3 = conn.cursor()

now = datetime.datetime.now()
now_minus_6mo = (datetime.datetime.now()-datetime.timedelta(weeks = 26)).strftime('%Y-%m-%d')
# print(now, now_minus_6mo)


#global constants
#These global vars to be pulled from constants table in the database

vendor_id_list = [68,69] #Trinys, Soles
regular_ship_lead = 9 #in weeks
initial_regular_ship_date = now + datetime.timedelta(weeks = regular_ship_lead)
rush_ship_lead = 5 #in weeks
forecast_window_limit = 26 #weeks
forecast_window_limit_date = now + datetime.timedelta(weeks = forecast_window_limit+regular_ship_lead)
# ^^^ Sets end date for planning window, may be reduced if process takes too long to run, adjust to be made by changing forecast_window_limit

vendor_array = list()

# Clearing results table
clear_table_query = """
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
        product_id integer NOT NULL,
        product_grade character(1) COLLATE pg_catalog."default",
        order_mod smallint,
        qty_2_ord numeric NOT NULL,
        qty_2_ord_adj numeric NOT NULL,
        qty_on_order numeric,
        qty_committed numeric,
        qty_sold numeric,
        expected_on_hand numeric,
        qty_on_hand numeric,
        sales_trend numeric,
        box_capacity integer,
        CONSTRAINT sodanca_purchase_plan_pkey PRIMARY KEY (id)
    )
    WITH (
        OIDS = FALSE
    )
    TABLESPACE pg_default;

    ALTER TABLE public.sodanca_purchase_plan
        OWNER to sodanca;
    COMMENT ON TABLE public.sodanca_purchase_plan
        IS 'Reset nightly, used by stock purchase planner';
"""
try:
    cur.execute(clear_table_query)
    print(conn.notices)
    conn.commit()
    print(conn.notices)
except:
    print(conn.notices)
    print("Cannot clear sodanca_purchase_plan. ERR:000")



for vendor_parent in vendor_id_list:
    vendor_list_query = "SELECT id FROM res_partner WHERE parent_id = {0} and supplier = true".format(vendor_parent)

    try:
        cur.execute(vendor_list_query)
    except:
        print("I can't SELECT from res_partner. ERR:001")

    vendors = cur.fetchall()


    for subvendor in vendors:

        vendor_array.append(tuple((subvendor[0],vendor_parent)))


    vendor_array.append(tuple((vendor_parent,)))

# print(vendor_array[0])

print(now)


for vendor in vendor_array:

    try:
        vendor_parent = vendor[1]
    except:
        vendor_parent = 0


    # print(subvendor[0])
    product_list_query = """SELECT product_supplierinfo.product_id, product_template.name, 'vendor_cost from purchase list' AS vendor_cost, categ_id, product_product.name as product_name,
          product_product.id, sodanca_stock_control.grade,
          sodanca_stock_control.min_stock, sodanca_stock_control.max_stock, sodanca_stock_control.order_mod, sodanca_stock_control.lead_time
    FROM product_supplierinfo
    LEFT JOIN product_template ON product_template.id = product_supplierinfo.product_id
    LEFT JOIN product_product ON product_supplierinfo.product_id = product_product.product_tmpl_id
    LEFT JOIN sodanca_stock_control ON sodanca_stock_control.id = product_product.id
    WHERE product_template.procure_method = 'make_to_stock'
        AND product_template.purchase_ok = true
        AND product_template.active = true
        AND product_product.active = true
        AND product_product.discontinued_product = false
        AND product_product.procure_method = 'make_to_stock'
        AND product_supplierinfo.name = {0}
        AND product_product.grade IN ('A','B')
        """.format(vendor[0])

    # print(vendor)



    try:
        # print(product_list_query)
        cur.execute(product_list_query) #cur2
        # cur.commit()
        product_count = cur.rowcount
        product_list = cur.fetchall()
    except:
        print("I can't execute query. ERR:002")

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
        lead_time = product[10]

        purchase_period = 1 #in weeks

        # print(product)

        for pdate in rrule.rrule(rrule.WEEKLY, dtstart = initial_regular_ship_date, until = forecast_window_limit_date):
            start_date = pdate.strftime('%Y-%m-%d')
            # print(start_date)
            end_date = (pdate + datetime.timedelta(weeks = purchase_period)).strftime('%Y-%m-%d')
            start_prev_year = (pdate - datetime.timedelta(weeks = 52)).strftime('%Y-%m-%d')
            end_prev_year = (pdate - datetime.timedelta(weeks = 52) + datetime.timedelta(weeks = purchase_period)).strftime('%Y-%m-%d')
            qto_query = "SELECT COALESCE(sd_quantity_to_order({0},'{1}' ,'{2}'),0)".format(product_id,start_date, end_date)

            # print(vendor,product_template_name,product_name, product_grade,qto_query)

            try:
                cur.execute(qto_query) #cur3
                product_qto = cur.fetchall()
                # print(product_qto[0][0])
            except:
                print("I can't execute query. ERR:003")strftime('%Y-%m-%d')

            # if product_qto[0][0] > 0: ### Production
            if 1: ### TEST
            # print(start_date,vendor[0],product_template_name,product_name, product_grade,product_qto[0][0], qto_query)

                prod_details_query = """SELECT COALESCE(sd_quantity_to_order({0},'{1}','{2}'),0), COALESCE(sd_qoo({0},'{3}','{1}'),0), COALESCE(sd_qoo({0},'{1}','{2}'),0), COALESCE(sd_qcomm({0},'{1}','{2}'),0), COALESCE(sd_qhs({0},'{1}','{2}'),0), COALESCE(sd_expected_onhand({0},'{1}'),0), COALESCE(sd_qoh({0}),0), COALESCE(sd_sales_trend({0}),0)""".format(product_id, start_date, end_date, now_minus_6mo)
                #Still missing box_capacity which should come here maybe as a function or a query
                # print(prod_details_query)
                try:
                    cur.execute(prod_details_query) #cur3
                    prod_details = cur.fetchall()
                    # Rounding qty to order
                    qto_rounded = roundup(prod_details[0][0],order_mod)
                    # print(product_template_name, product_name, product_grade, qto_rounded, prod_details[0][0],prod_details[0][1], prod_details[0][2], prod_details[0][3], prod_details[0][4], prod_details[0][5], prod_details[0][6], prod_details[0][7])

                    # print(prod_details)
                except:
                    print("I can't execute query. ERR:004")

                if vendor_parent != 0:
                    product_vendor = vendor_parent
                    product_group = vendor[0]
                else:
                    product_vendor = vendor[0]
                    product_group = '0'
                #
                # print(prod_details)
                # print(product_vendor)
                # print(product_group)
                # print(now.strftime('%Y-%m-%d'))
                # print(start_date)
                # print(product_template_id)
                # print(product_id)
                # print(product_grade)
                # print(order_mod)
                # print(product_qto[0][0])
                # print(qto_rounded)
                # print('0', prod_details[0][0])
                # print('2', prod_details[0][2])
                # print('1', prod_details[0][1])
                # print('3', prod_details[0][3])
                # print('4', prod_details[0][4])
                # print(prod_details[0][5])
                #
                # print(product_vendor, product_group, now.strftime('%Y-%m-%d'), start_date, product_template_id, product_id, product_grade, order_mod, product_qto[0][0], qto_rounded, prod_details[0][0],prod_details[0][1], prod_details[0][2], prod_details[0][3], prod_details[0][4], prod_details[0][5])

                insert_query = """INSERT INTO sodanca_purchase_plan (id, type, vendor, vendor_group, creation_date, expected_date, template_id, product_id, product_grade, order_mod, qty_2_ord,
                qty_2_ord_adj, qty_on_order, qty_on_order_period, qty_committed, qty_sold, expected_on_hand, qty_on_hand, sales_trend, box_capacity) VALUES (default, 'N', {0}, {1}, '{2}'::date, '{3}'::date, {4}, {5}, '{6}', {7}, {8},
                {9}, {10}, {11}, {12}, {13}, {14}, {15}, {16}, 0)""".format(product_vendor, product_group, now.strftime('%Y-%m-%d'), start_date, product_template_id, product_id, product_grade, order_mod, prod_details[0][0], qto_rounded, prod_details[0][1], prod_details[0][2], prod_details[0][3], prod_details[0][4], prod_details[0][5], prod_details[0][6], prod_details[0][7])

                # print(insert_query)

                try:
                    cur2.execute(insert_query)
                    # print(conn.notices)
                    conn.commit()
                    # print(conn.notices)
                except:
                    print("Cannot insert results. ERR:005")
        #qto_query = "SELECT sd_quantity_to_order({0})".format(product)

        #try:
            #cur3.execute(qto_query)
            #qto = cur3.fetchall()
            #print ("Quantity to order {0} - {1}").format(product, qto)
        #except:


        # print(product)
cur.close()
cur2.close()
# cur3.close()
print(datetime.datetime.now())
print('Runtime: ',datetime.datetime.now()-now)
    # print(vendor_parent)
