#!/usr/bin/python3
#
# Small script to show PostgreSQL and Pyscopg together
#

import psycopg2
import datetime
from dateutil import rrule
import math

class reg(object):
    def __init__(self, cursor, registro):
        for (attr, val) in zip((d[0] for d in cursor.description),registro) :
            setattr(self, attr, val)

logfilename = 'purchase_planner.log'



def roundup(x,y):
  return int(math.ceil(x/y))*y

def create_order(conn, order_type, product_grade, lead_time, period_length):

    # database cursor definitions
    cur = conn.cursor()
    cur2 = conn.cursor()

    now = datetime.datetime.now()
    now_minus_6mo = (datetime.datetime.now()-datetime.timedelta(weeks = 26)).strftime('%Y-%m-%d')
    # print(now, now_minus_6mo)

    #global constants
    #These global vars to be pulled from constants table in the database

    vendor_id_list = [68,69] #Trinys, Soles
    # regular_ship_lead = lead_time #in weeks
    initial_regular_ship_date = now + datetime.timedelta(weeks = lead_time) #lead time in weeks
    # rush_ship_lead = 5 #in weeks
    forecast_window_limit = 26 #weeks
    forecast_window_limit_date = now + datetime.timedelta(weeks = forecast_window_limit+lead_time)
    # ^^^ Sets end date for planning window, may be reduced if process takes too long to run, adjust to be made by changing forecast_window_limit

    print("Starting run -- order_type: {0} Grade: {1} - {2}".format(order_type, product_grade, (datetime.datetime.now().strftime('%H:%M:%S - %Y-%m-%d'))))
    fil.write("Starting run -- order_type: {0} Grade: {1} - {2}".format(order_type, product_grade, (datetime.datetime.now().strftime('%H:%M:%S - %Y-%m-%d'))))

    vendor_array = list()

    for vendor_parent in vendor_id_list:
        vendor_list_query = "SELECT id FROM res_partner WHERE parent_id = {0} and supplier = true".format(vendor_parent)

        try:
            cur.execute(vendor_list_query)
            vendors = cur.fetchall()

        except Exception:
            fil.write("I can't SELECT from res_partner. ERR:001")
            raise

        for subvendor in vendors:
            vendor_array.append(tuple((subvendor[0],vendor_parent)))

        vendor_array.append(tuple((vendor_parent,)))

    # print(vendor_array[0])

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
            AND product_product.grade = '{1}'
            """.format(vendor[0], product_grade)
        # print(vendor)

        try:
            # print(product_list_query)
            cur.execute(product_list_query)
            product_count = cur.rowcount
            product_list = cur.fetchall()

        except Exception:
            fil.write("I can't execute query. ERR:002")
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
            lead_time = product[10]

            purchase_period = period_length #in weeks

            # print(product)

            for pdate in rrule.rrule(rrule.WEEKLY, dtstart = initial_regular_ship_date, until = forecast_window_limit_date):
                start_date = pdate.strftime('%Y-%m-%d')
                # print(start_date)
                end_date = (pdate + datetime.timedelta(weeks = purchase_period)).strftime('%Y-%m-%d')
                start_prev_year = (pdate - datetime.timedelta(weeks = 52)).strftime('%Y-%m-%d')
                end_prev_year = (pdate - datetime.timedelta(weeks = 52) + datetime.timedelta(weeks = purchase_period)).strftime('%Y-%m-%d')
                qto_query = "SELECT COALESCE(sd_quantity_to_order({0},'{1}' ,'{2}'),0)".format(product_id,start_date, end_date)

                # print(vendor,product_template_name,product_name, product_grade,qto_query)
                cur.execute(qto_query) #cur3

                try:

                    cur.execute(qto_query) #cur3
                    product_qto = cur.fetchall()
                    # print(product_qto[0][0])

                except Exception:
                    fil.write("I can't execute query. ERR:003")
                    fil.write(Exception)
                    raise Exception
                    pass

                # if 1: ### TEST
                if product_qto[0][0] > 0: ### Production
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
                    except Exception:
                        fil.write("I can't execute query. ERR:004")
                        fil.write(Exception)
                        raise Exception
                        pass

                    if vendor_parent != 0:
                        product_vendor = vendor_parent
                        product_group = vendor[0]
                    else:
                        product_vendor = vendor[0]
                        product_group = '0'

                    # print(product_vendor, product_group, now.strftime('%Y-%m-%d'), start_date, product_template_id, product_id, product_grade, order_mod, product_qto[0][0],
                    # qto_rounded, prod_details[0][0],prod_details[0][1], prod_details[0][2], prod_details[0][3], prod_details[0][4], prod_details[0][5])

                    insert_query = """INSERT INTO sodanca_purchase_plan (id, type, vendor, vendor_group, creation_date, expected_date, template_id, template_name, product_id, product_name, product_category_id, product_grade, order_mod, qty_2_ord,
                    qty_2_ord_adj, qty_on_order, qty_on_order_period, qty_committed, qty_sold, expected_on_hand, qty_on_hand, sales_trend) VALUES (default, '{20}', {0}, {1}, '{2}'::date, '{3}'::date, {4}, '{5}', {6}, '{7}', {8},
                    '{9}', {10}, {11}, {12}, {13}, {14}, {15}, {16}, {17}, {18}, {19})""".format(product_vendor, product_group, now.strftime('%Y-%m-%d'), start_date, product_template_id, product_template_name, product_id, product_name, category_id, product_grade, order_mod, prod_details[0][0],
                        qto_rounded, prod_details[0][1], prod_details[0][2], prod_details[0][3], prod_details[0][4], prod_details[0][5], prod_details[0][6], prod_details[0][7], order_type)

                    # print(insert_query)

                    try:
                        cur2.execute(insert_query)
                        conn.commit()

                    except Exception:
                        fil.write("Cannot insert results. ERR:005")

    cur.close()
    cur2.close()

    print("Ending run   -- order_type: {0} Grade: {1} - {2}".format(order_type, product_grade, (datetime.datetime.now().strftime('%H:%M:%S - %Y-%m-%d'))))
    fil.write("Ending run   -- order_type: {0} Grade: {1} - {2}".format(order_type, product_grade, (datetime.datetime.now().strftime('%H:%M:%S - %Y-%m-%d'))))

### ------------------------------------ MAIN() ------------------------------------------ ###

try:
    conn = psycopg2.connect("dbname='OE-BackupProd-USA-20171117' host='192.168.100.70' user='sodanca' password='iZ638GD'")

except:
    fil.write("I am unable to connect to the database")

fil = open(logfilename,'a')

fil.write("\n\nProcess started - {0}".format((datetime.datetime.now().strftime('%H:%M:%S - %Y-%m-%d'))))

cur = conn.cursor()

start_clock = datetime.datetime.now()

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
        --box_capacity integer,
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
    conn.commit()
    cur.close()
except Exception:
    print(conn.notices)
    fil.write("Cannot clear sodanca_purchase_plan. ERR:000")
    pass

cur.close()



# create_order(conn, order_type, product_grade, lead_time, period_length)
create_order(conn, 'R', 'A', 5, 1)
create_order(conn, 'R', 'B', 5, 1)
create_order(conn, 'N', 'A', 9, 1)
create_order(conn, 'N', 'B', 9, 1)
create_order(conn, 'R', 'C', 5, 12)
create_order(conn, 'R', 'D', 5, 4)


# cur3.close()
print('Completion time: ',datetime.datetime.now())
fil.write('Completion time: ',datetime.datetime.now())
print('Runtime: ',str(datetime.datetime.now()- start_clock))
fil.write('Runtime: ',str(datetime.datetime.now()- start_clock))
fil.write("="*80,"\n")
fil.close()
    # print(vendor_parent)
