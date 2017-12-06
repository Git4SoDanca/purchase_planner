#!/home/fsoares/purchase_planner/PurchaseOrder_Scheduler/bin/python
#
# Script to parse attachments with hot item stock
#

import psycopg2
import configparser
import datetime
import os
import csv

def roundup(x,y):
  return int(math.ceil(x/y))*y

def log_entry(logfile, entry_text):
    try:
        fil = open(logfile,'a')
        fil.write(entry_text)
        fil.close()
    except Exception as e:
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

config_file = 'config.ini'

companycode = 'USA'

filepath='attachments/'

config = configparser.ConfigParser()
config.sections()
config.read('config.ini')


dbname = config[companycode]['db_name']
db_server_address = config[companycode]['db_server_address']
login = config[companycode]['login']
passwd = config[companycode]['passwd']

logfilename = config[companycode]['logfilename']#'purchase_planner.log'

dsn = ("dbname={0} host={1} user={2} password={3}").format(dbname, db_server_address, login, passwd)
conn = psycopg2.connect(dsn)

cur = conn.cursor()

email_date = now = (datetime.datetime.now()).strftime('%Y-%m-%d')

check_table_query = "select * from information_schema.tables where table_name = '{0}'".format('sodanca_estoque_pulmao')
# print(check_table_query)
cur.execute(check_table_query)
num_tables = cur.fetchone()
print(num_tables)

if num_tables == None:
    create_table_sql = """
        -- Table: public.sodanca_estoque_pulmao

        DROP TABLE IF EXISTS public.sodanca_estoque_pulmao;

        CREATE TABLE public.sodanca_estoque_pulmao
        (
            -- id integer NOT NULL DEFAULT nextval('sodanca_estoque_pulmao_id_seq'::regclass),
            email_date date NOT NULL,
            product_id integer NOT NULL,
            product_name character varying(64) COLLATE pg_catalog."default",
            quantity numeric --,
            --CONSTRAINT sodanca_estoque_pulmao_pkey PRIMARY KEY (id)
        )
        WITH (
            OIDS = FALSE
        )
        TABLESPACE pg_default;

        ALTER TABLE public.sodanca_estoque_pulmao
            OWNER to sodanca;
        COMMENT ON TABLE public.sodanca_estoque_pulmao
            IS 'This is updated daily from the email sent from Soles, by default the data is cycled every 12 months, this can be adjusted on the config file';
    """

    try:
        cur.execute(create_table_sql)
        conn.commit()
    except Exception as e:
        now = (datetime.datetime.now()).strftime('%H:%M:%s %Y-%m-%d')
        log_str = "Cannot create table sodanca_estoque_pulmao. ERR:012 {1} \n {0}".format(str(e), now)
        print(log_str)
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
        # print("({0}),".format(product_query))
        # print("DEBUG product query: {0}".format(product_query))\

        # if 1:
        try:
            # print('DEBUG line:', line)
            cur.execute(product_query)
            # rowcount = cur.rowcount()
            # if rowcount == 0:
            #     print(product_barcode, line)
            # if rowcount() > 1:
            #     try_again = rowcount
            products = cur.fetchall()
            if len(products) == 0:
                print(product_barcode, line)
                now = (datetime.datetime.now()).strftime('%H:%M:%s %Y-%m-%d')
                log_str = '{2} Barcode not defined in database barcode {0}, product details {1}'.format(product_barcode, line, now)
                # print(log_str)
                log_entry(logfilename,log_str)

            for product in products:
                product_id = product[0]
                product_name = product[1]

                insert_query = """ INSERT INTO sodanca_estoque_pulmao (--id,
                email_date, product_id, product_name, quantity) VALUES (
                    --default,
                    '{0}', {1}, '{2}', {3})""".format(email_date, product_id, product_name, qty_in_hotstock)
                # print('DEBUG insert query:',insert_query)
                cur.execute(insert_query)
                conn.commit()

                check_order = "SELECT * FROM sodanca_purchase_plan WHERE type = 'R' AND product_id = {0} ORDER BY expected_date LIMIT 1".format(product_id)
                # print(check_order)
                try:
                    cur.execute(check_order)
                    order_result = cur.fetchall()
                    for order in order_result:
                        qty_2_ord = order[13]
                        line_id = order[0]
                        order_mod = order[12]


                        print(order[9],order[13], qty_in_hotstock, order[13]-qty_in_hotstock)
                        if (qty_2_ord > 0):
                            if qty_in_hotstock >= qty_2_ord:
                                qty_2_ord = 0
                                qty_2_ord_adj = 0
                                update_sql = "UDPATE sodanca_purchase_plan SET (qty_2_ord, qty_2_ord_adj) VALUES (0,0) WHERE id = {}".format(line_id)
                                print(update_sql)
                                # cur.execute(update_sql)
                                # conn.commit()
                                # insert_query = create_order()
                            elif qty_in_hotstock < qty_2_ord:
                                qty_2_ord = qty_2_ord - qty_in_hotstock
                                qty_2_ord_adj = roundup(qty_2_ord,order_mod)
                                update_sql = "UDPATE sodanca_purchase_plan SET (qty_2_ord, qty_2_ord_adj) VALUES (0,0) WHERE id = {}".format(line_id)
                                print(update_sql)
                        # print(order)
                except Exception as e:
                    print(str(e))

        except Exception as e:

            pass
    fileobj.close()

    # try:
    #     insert_query = """ INSERT INTO sodanca_estoque_pulmao (id, email_date, product_id, product_name, quantity) VALUES
    #         default, {0}, {1}, {2}, {3}""".format(email_date, product_id, product_name, qty_in_hotstock)
    #     cur.execute(insert_query)
    #     cur.commit()
    #     pass
    # except Exception as e:
    #     now = (datetime.datetime.now()).strftime('%H:%M:%s %Y-%m-%d')
    #     log_str = "Could not insert into sodanca_estoque_pulmao. ERR: 013 {0}\n {1}".format(now, str(e))
    #     raise
        # pass
