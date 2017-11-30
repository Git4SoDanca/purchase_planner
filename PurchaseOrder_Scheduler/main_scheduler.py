#!/home/fsoares/purchase_planner/PurchaseOrder_Scheduler/bin/python
#
# Script to create purchase_planner table
#

import psycopg2
import datetime
from dateutil import rrule
import math
import configparser
import sys,getopt

class reg(object):
    def __init__(self, cursor, registro):
        for (attr, val) in zip((d[0] for d in cursor.description),registro) :
            setattr(self, attr, val)

def log_entry(logfile, entry_text):
    fil = open(logfile,'a')
    fil.write(entry_text)
    fil.close()

def roundup(x,y):
  return int(math.ceil(x/y))*y

def create_order(conn, order_type, product_grade, lead_time, period_length, companycode):

    logfilename = config[companycode]['logfilename']

    # database cursor definitions
    cur = conn.cursor()
    cur2 = conn.cursor()

    now = datetime.datetime.now()
    now_minus_6mo = (datetime.datetime.now()-datetime.timedelta(weeks = 26)).strftime('%Y-%m-%d')
    # print(now, now_minus_6mo)

    initial_regular_ship_date = now + datetime.timedelta(weeks = lead_time) #lead time in weeks
    forecast_window_limit = int(config[companycode]['forecast_window_limit']) #weeks
    forecast_window_limit_date = now + datetime.timedelta(weeks = forecast_window_limit+lead_time)
    # ^^^ Sets end date for planning window, may be reduced if process takes too long to run, adjust to be made by changing forecast_window_limit

    print("Starting run -- order_type: {0} Grade: {1} - {2}".format(order_type, product_grade, (datetime.datetime.now().strftime('%H:%M:%S - %Y-%m-%d'))))
    log_entry(logfilename,"Starting run -- order_type: {0} Grade: {1} - {2}\n".format(order_type, product_grade, (datetime.datetime.now().strftime('%H:%M:%S - %Y-%m-%d'))))

    vendor_array = list()

    for vendor_parent in config[companycode]['vendor_id_list'].split(","):#vendor_id_list:
        vendor_list_query = "SELECT id FROM res_partner WHERE parent_id = {0} and supplier = true".format(int(vendor_parent))

        try:
            cur.execute(vendor_list_query)
            vendors = cur.fetchall()

        except Exception:
            log_entry(logfilename,"I can't SELECT from res_partner. ERR:001\n")

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
            log_entry(logfilename,"I can't execute query. ERR:002\n")

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
                    log_entry(logfilename,"I can't execute query. ERR:003\n")
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
                        log_entry(logfilename,"I can't execute query. ERR:004\n")
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
                        log_entry(logfilename,"Cannot insert results. ERR:005\n")


    cur.close()
    cur2.close()

    print("Ending run   -- order_type: {0} Grade: {1} - {2}".format(order_type, product_grade, (datetime.datetime.now().strftime('%H:%M:%S - %Y-%m-%d'))))
    log_entry(logfilename,"Ending run   -- order_type: {0} Grade: {1} - {2}\n".format(order_type, product_grade, (datetime.datetime.now().strftime('%H:%M:%S - %Y-%m-%d'))))

def drop_results_table(conn):

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
        log_entry(logfilename,"Cannot clear sodanca_purchase_plan. ERR:000\n")
        pass

    cur.close()

def create_tables(conn, companycode):
    table_query = """
    DROP TABLE IF EXISTS sodanca_stock_control;
    CREATE TABLE sodanca_stock_control AS
    (
    WITH
    const AS (
    select 	{grade_a_margin} as grade_a_margin,
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
        	{mod_ba} as mod_ba,
        	{mod_jz} as mod_jz,
        	{mod_ch} as mod_ch,
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
            WHEN category_id = ANY (const.categ_jz) THEN mod_jz
            WHEN category_id = ANY (const.categ_ba) THEN mod_ba
            WHEN category_id = ANY (const.categ_ch) THEN mod_ch
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
        OWNER to sodanca;

    -- Update grades on product_product table
    UPDATE product_product SET grade = sodanca_stock_control.grade FROM sodanca_stock_control
    WHERE product_product.id = sodanca_stock_control.id;

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
          IS 'Reset nightly, used by stock purchase planner';""".format()

    logfilename = config[companycode]['logfilename']
    try:
        cur = conn.cursor()
        cur.execute(table_query)
        cur.commit()
        cur.close()
        log_entry(logfilename,"sodanca_stock_control created successfully.")
    except Exception as e:
        log_entry(logfilename, 'Error creating sodanca_stock_control. ERR:008')
        log_entry(logfilename,str(e))
        raise

def create_views(conn, companycode):

def create_functions(conn,companycode):


### ------------------------------------ MAIN() ------------------------------------------ ###

def main(companycode):
    dbname = config[companycode]['db_name']
    db_server_address = config[companycode]['db_server_address']
    login = config[companycode]['login']
    passwd = config[companycode]['passwd']

    logfilename = config[companycode]['logfilename']#'purchase_planner.log'

    try:
        dsn = ("dbname={0} host={1} user={2} password={3}").format(dbname, db_server_address, login, passwd)
        print(dsn)
        conn = psycopg2.connect(dsn)
        log_entry(logfilename,"\n\nProcess started - {0}\n".format((datetime.datetime.now().strftime('%H:%M:%S - %Y-%m-%d'))))
        drop_results_table(conn)

    except:
        print(logfilename,"I am unable to connect to the database\n")
        log_entry(logfilename,"I am unable to connect to the database\n")

    # create_order(conn, order_type, product_grade, lead_time, period_length)

    lead_normal = int(config[companycode]['lead_normal'])
    lead_rush = int(config[companycode]['lead_rush'])
    plan_period_a = int(config[companycode]['plan_period_a'])
    plan_period_b = int(config[companycode]['plan_period_b'])
    plan_period_c = int(config[companycode]['plan_period_c'])
    plan_period_d = int(config[companycode]['plan_period_d'])

    try:
        create_order(conn, 'R', 'A', lead_rush, plan_period_a, companycode)
        create_order(conn, 'R', 'B', lead_rush, plan_period_b, companycode)
        create_order(conn, 'N', 'A', lead_normal, plan_period_a, companycode)
        create_order(conn, 'N', 'B', lead_normal, plan_period_b, companycode)
        create_order(conn, 'R', 'C', lead_rush, plan_period_c, companycode)
        create_order(conn, 'R', 'D', lead_rush, plan_period_d, companycode)

    except KeyboardInterrupt:
        print("Interrupted by user")
        log_entry(logfilename,"Interrupted by user. ERR:006\n")

    except Exception as e:
        print("Error on execution. ERR:007")
        log_entry(logfilename,"Something unexpected happened. ERR:007\n")
        raise
        pass


    # cur3.close()
    print('Completion time: ',datetime.datetime.now())
    log_entry(logfilename,'Completion time: '+(datetime.datetime.now().strftime('%H:%M:%S - %Y-%m-%d')))
    print('Runtime: ',str(datetime.datetime.now()- start_clock))
    log_entry(logfilename,'Runtime: '+str(datetime.datetime.now()- start_clock))
    log_entry(logfilename,"="*80+"\n")
# fil.close()
    # print(vendor_parent)
# ========================== EXECUTION CALL ========================================================== #

config = configparser.ConfigParser()
config.sections()
config.read('config.ini')

cmd_param = sys.argv[1]

if cmd_param in config:
    companycode = str(cmd_param)
    main(companycode)
elif cmd_param == '-i':
    print("Start interactive")
else:
    print(cmd_param, 'is not a valid option. Use a company code or -i for interactive mode')
    sys.exit(2)
