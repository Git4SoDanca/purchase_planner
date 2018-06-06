#!/usr/bin/python3
#
# Small script to show PostgreSQL and Pyscopg together
#

import psycopg2

class reg(object):
    def __init__(self, cursor, registro):
        for (attr, val) in zip((d[0] for d in cursor.description),registro) :
            setattr(self, attr, val)

try:
    conn = psycopg2.connect("dbname='OE-Prod-USA-D1' host='192.168.100.70' user='purchase_planner' password='wy92ugzE98yz'")

except:
    print("I am unable to connect to the database")

cur = conn.cursor()
cur2 = conn.cursor()

table_names = ['sodanca_stock_control_q1_2018','sodanca_stock_control_q2_2018','sodanca_stock_control_q3_2018','sodanca_stock_control_ q4_2018']
qtr_start_dates = ['2018-01-01','2018-04-01','2018-07-01','2018-10-01']
qtr_end_dates = ['2018-03-31','2018-06-30','2018-09-30','2018-12-31']


for n in range(0,3):

    fileout = open(table_names[n]+'.csv','w')
    # fileout.write('style_name,product_name,qty_planned, qty_sold, balance')
    # fileout.write("\n")

    sales_query = """SELECT product_id, to_char(date_expected, 'WW') as week_no, sum(product_qty) AS total_sold
            FROM stock_move WHERE location_id = 12 AND location_dest_id = 9 AND date_expected >= '%s' AND date_expected <= '%s'
            GROUP BY product_id, week_no
            ORDER BY product_id, week_no
            --LIMIT 500
            """ % (qtr_start_dates[n],qtr_end_dates[n])


    try:
        # print(sales_query)
        cur.execute(sales_query)

    except:
        print("I can't SELECT from stock_move")

    rows = cur.fetchall()
    over_stocked = [0,0,0,0]
    under_stocked = [0,0,0,0]
    good_stock = [0,0,0,0]
    total_sold_count = [0,0,0,0]


    for row in rows:
        r = reg(cur, row)
        stock_level_query = """SELECT product_product.name, product_product.name_template, {0}.*
            FROM "{0}"
            LEFT JOIN product_product ON {0}.product_id = product_product.id
            WHERE product_id = {1}""".format(table_names[n], r.product_id) #table_names[n], table_names[n], r.product_id)

        # print(stock_level_query)
        # attrs = vars(r)
        # print (','.join("%s: %s" % item for item in attrs.items()))
        try:
            cur2.execute(stock_level_query)
        except:
            print("I can't SELECT from {}".format(table_names[n]))

        stock_level_set = cur2.fetchall()
        for sls in stock_level_set:
            sls = reg(cur2,sls)
            if r.total_sold < sls.min_stock:
                # print("Less than min stock")
                if (sls.grade) == 'A':
                    over_stocked[0] += 1
                elif (sls.grade) == 'B':
                    over_stocked[1] += 1
                elif (sls.grade) == 'C':
                    over_stocked[2] += 1
                elif (sls.grade) == 'D':
                    over_stocked[3] += 1
            elif r.total_sold > sls.max_stock:
                # print("More than max stock")
                if (sls.grade) == 'A':
                    under_stocked[0] += 1
                elif (sls.grade) == 'B':
                    under_stocked[1] += 1
                elif (sls.grade) == 'C':
                    under_stocked[2] += 1
                elif (sls.grade) == 'D':
                    under_stocked[3] += 1
            else:
                if (sls.grade) == 'A':
                    good_stock[0] += 1
                elif (sls.grade) == 'B':
                    good_stock[1] += 1
                elif (sls.grade) == 'C':
                    good_stock[2] += 1
                elif (sls.grade) == 'D':
                    good_stock[3] += 1
            # print(sls.name, sls.name_template, r.total_sold)

    for n1 in range (0,3):
        total_sold_count[n1] = over_stocked[n1] + under_stocked[n1] + good_stock[n1]
    print("A items")
    print("Q{0} Total styles/week over stocked {1} - Percentage Over stocked: {2}".format(n+1, over_stocked[0], (over_stocked[0]/total_sold_count[0])*100))
    print("Q{0} Total styles/week under stocked {1} - Percentage Under stocked: {2}".format(n+1, under_stocked[0], (under_stocked[0]/total_sold_count[0])*100))
    print("Q{0} Total styles/week good stock {1} - Percentage Good stock: {2}\n".format(n+1, good_stock[0], (good_stock[0]/total_sold_count[0])*100))

    print("B items")
    print("Q{0} Total styles/week over stocked {1} - Percentage Over stocked: {2}".format(n+1, over_stocked[1], (over_stocked[1]/total_sold_count[1])*100))
    print("Q{0} Total styles/week under stocked {1} - Percentage Under stocked: {2}".format(n+1, under_stocked[1], (under_stocked[1]/total_sold_count[1])*100))
    print("Q{0} Total styles/week good stock {1} - Percentage Good stock: {2}\n".format(n+1, good_stock[1], (good_stock[1]/total_sold_count[1])*100))

    print("C items")
    print("Q{0} Total styles/week over stocked {1} - Percentage Over stocked: {2}".format(n+1, over_stocked[2], (over_stocked[2]/total_sold_count[2])*100))
    print("Q{0} Total styles/week under stocked {1} - Percentage Under stocked: {2}".format(n+1, under_stocked[2], (under_stocked[2]/total_sold_count[2])*100))
    print("Q{0} Total styles/week good stock {1} - Percentage Good stock: {2}\n".format(n+1, good_stock[2], (good_stock[2]/total_sold_count[2])*100))

    print("D items - {}".format(total_sold_count[3]))
    try:
        print("Q{0} Total styles/week over stocked {1} - Percentage Over stocked: {2}".format(n+1, over_stocked[3], (over_stocked[3]/total_sold_count[3])*100))
        print("Q{0} Total styles/week under stocked {1} - Percentage Under stocked: {2}".format(n+1, under_stocked[3], (under_stocked[3]/total_sold_count[3])*100))
        print("Q{0} Total styles/week good stock {1} - Percentage Good stock: {2}\n".format(n+1, good_stock[3], (good_stock[3]/total_sold_count[3])*100))
    except:
        print("Q{0} Total styles/week over stocked {1}".format(n+1, over_stocked[3]))
        print("Q{0} Total styles/week under stocked {1}".format(n+1, under_stocked[3]))
        print("Q{0} Total styles/week good stock {1}\n".format(n+1, good_stock[3]))

conn.close()
fileout.close()
