DROP TABLE IF EXISTS sodanca_stock_control_q1_2017;
CREATE TABLE sodanca_stock_control_q1_2017 AS (
WITH
const AS (
select 	.20 as grade_a_margin,
    	.35 as grade_b_margin,
    	.70 as grade_c_margin,
    	9 as lead_time_a,
    	9 as lead_time_b,
    	5 as lead_time_c,
		3 as lead_time_d,
    	1 as min_inv_time_a,
    	2 as max_inv_time_a,
    	4 as min_inv_time_b,
    	6 as max_inv_time_b,
    	1 as min_inv_time_c,
    	12 as max_inv_time_c,
    	0 as min_inv_time_d,
    	0 as max_inv_time_d,
		100 as box_ba_reg,
    	80 as box_ba_larg,
    	36 as box_jz_reg,    
        24 as box_jz_larg,
    	12 as box_ch,
    	10 as mod_ba,
    	4 as mod_jz,
    	4 as mod_ch,
    	array[52,55,47,57] as categ_ba,
    	array[53,54,16,60,61,58,59] as categ_ch,
    	array[56] as categ_jz,
    	'Thursday' AS cutoff_date
)
, sodanca_inventory_status_last12 AS (

     SELECT product_product.name_template,
    product_product.name, product_product.id as product_id,
    CASE
        WHEN product_template.categ_id = 64 -- Tights
        	THEN 'Tights'
    	WHEN product_template.categ_id IN (SELECT id from product_category where parent_id in (8)) -- Child of Shoes
        	THEN 'Shoes'
        WHEN product_template.categ_id IN (SELECT id from product_category where parent_id in (43)) -- Child of Dancewear
        	THEN 'Dancewear'
        WHEN product_template.categ_id = 43 -- Dancewear
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
    ceil(sold.product_sale_total::double precision / 52::double precision) AS weekly_average

   FROM product_product
     LEFT JOIN product_template ON product_template.id = product_product.product_tmpl_id
     LEFT JOIN ( SELECT stock_move.product_id,
            sum(stock_move.product_qty) AS product_sale_total
           FROM stock_move
             LEFT JOIN product_product product_product_1 ON product_product_1.id = stock_move.product_id
          WHERE stock_move.location_dest_id = 9 AND stock_move.location_id = 12 AND stock_move.state::text = 'done'::text
                AND stock_move.date >= ('2017-10-01'::date - '1 year'::interval) AND stock_move.date < ('2017-10-01'::date)
          GROUP BY stock_move.product_id) sold ON product_product.id = sold.product_id
     LEFT JOIN ( SELECT stock_move.product_id,
            sum(stock_move.product_qty) AS product_committed_total
           FROM stock_move
             LEFT JOIN product_product product_product_1 ON product_product_1.id = stock_move.product_id
          WHERE stock_move.location_dest_id = 9 AND stock_move.location_id = 12 AND (stock_move.state::text = ANY (ARRAY['confirmed'::character varying, 'assigned'::character varying]::text[]))
          GROUP BY stock_move.product_id) commited ON product_product.id = commited.product_id
     LEFT JOIN ( SELECT sodanca_stock_on_hand.id,
            sodanca_stock_on_hand.quantity_on_hand
           FROM sodanca_stock_on_hand) on_hand ON product_product.id = on_hand.id
  WHERE
    (sold.product_sale_total > 0::numeric
    OR commited.product_committed_total > 0::numeric)
    AND product_template.exclusive_customer IS NULL
    AND product_template.procure_method = 'make_to_stock'
    AND product_template.type = 'product'
    AND product_product.discontinued_product = false

  ORDER BY (
        CASE
            WHEN sold.product_sale_total IS NOT NULL THEN sold.product_sale_total
            ELSE 0::numeric
        END) DESC,
   		product_product.name_template, product_product.name
	),
inventory_grade AS (
    SELECT sodanca_inventory_status_last12.*, (PERCENT_RANK() OVER (PARTITION BY category ORDER BY total_sold DESC))*100 as rank_qty_sold, (PERCENT_RANK() OVER (PARTITION BY category ORDER BY total_sold*gross_margin DESC))*100 as rank_gr_profit
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
        WHEN PERCENT_RANK() OVER (PARTITION BY category ORDER BY total_sold DESC) <= const.grade_a_margin THEN sodanca_inventory_status_last12.weekly_average*const.min_inv_time_a
        WHEN PERCENT_RANK() OVER (PARTITION BY category ORDER BY total_sold DESC) <= const.grade_b_margin THEN sodanca_inventory_status_last12.weekly_average*const.min_inv_time_b
        WHEN PERCENT_RANK() OVER (PARTITION BY category ORDER BY total_sold DESC) <= const.grade_c_margin THEN sodanca_inventory_status_last12.weekly_average*const.min_inv_time_c
        ELSE 0
    END AS adjusted_minimum_stock,
    CASE
        WHEN PERCENT_RANK() OVER (PARTITION BY category ORDER BY total_sold DESC) <= const.grade_a_margin THEN sodanca_inventory_status_last12.weekly_average*const.max_inv_time_a
        WHEN PERCENT_RANK() OVER (PARTITION BY category ORDER BY total_sold DESC) <= const.grade_b_margin THEN sodanca_inventory_status_last12.weekly_average*const.max_inv_time_b
        WHEN PERCENT_RANK() OVER (PARTITION BY category ORDER BY total_sold DESC) <= const.grade_c_margin THEN sodanca_inventory_status_last12.weekly_average*const.max_inv_time_c
        ELSE 0
    END AS adjusted_maximum_stock,

    CASE
        WHEN category_id = ANY (const.categ_jz) THEN mod_jz
        WHEN category_id = ANY (const.categ_ba) THEN mod_ba
        WHEN category_id = ANY (const.categ_ch) THEN mod_ch
        ELSE 1

    END AS order_mod,
    CASE
        WHEN PERCENT_RANK() OVER (PARTITION BY category ORDER BY total_sold*gross_margin DESC) <= const.grade_a_margin THEN const.lead_time_a -- 'A'
        WHEN PERCENT_RANK() OVER (PARTITION BY category ORDER BY total_sold*gross_margin DESC) <= const.grade_b_margin THEN const.lead_time_b -- 'B'
        WHEN PERCENT_RANK() OVER (PARTITION BY category ORDER BY total_sold*gross_margin DESC) <= const.grade_c_margin THEN const.lead_time_c -- 'C'
        ELSE const.lead_time_d -- 'D'
    END AS lead_time
    FROM sodanca_inventory_status_last12, const
    ORDER BY category, name_template, total_sold DESC, sodanca_inventory_status_last12.name, rank_qty_sold

)


 --(product_id, grade, min_stock, max_stock, order_mod, box_size, lead_time)
SELECT product_id, grade_profit AS grade, adjusted_minimum_stock AS min_stock, adjusted_maximum_stock AS max_stock, order_mod, lead_time
FROM inventory_grade);

ALTER TABLE public.sodanca_stock_control_q1_2017
    OWNER to sodanca;

DROP TABLE IF EXISTS sodanca_stock_control_q2_2017;
CREATE TABLE sodanca_stock_control_q2_2017 AS (
WITH
const AS (
select 	.20 as grade_a_margin,
    	.35 as grade_b_margin,
    	.70 as grade_c_margin,
    	9 as lead_time_a,
    	9 as lead_time_b,
    	5 as lead_time_c,
		3 as lead_time_d,
    	1 as min_inv_time_a,
    	2 as max_inv_time_a,
    	4 as min_inv_time_b,
    	6 as max_inv_time_b,
    	1 as min_inv_time_c,
    	12 as max_inv_time_c,
    	0 as min_inv_time_d,
    	0 as max_inv_time_d,
		100 as box_ba_reg,
    	80 as box_ba_larg,
    	36 as box_jz_reg,
        24 as box_jz_larg,
    	12 as box_ch,
    	10 as mod_ba,
    	4 as mod_jz,
    	4 as mod_ch,
    	array[52,55,47,57] as categ_ba,
    	array[53,54,16,60,61,58,59] as categ_ch,
    	array[56] as categ_jz,
    	'Thursday' AS cutoff_date
)
, sodanca_inventory_status_last12 AS (

     SELECT product_product.name_template,
    product_product.name, product_product.id as product_id,
    CASE
        WHEN product_template.categ_id = 64 -- Tights
        	THEN 'Tights'
    	WHEN product_template.categ_id IN (SELECT id from product_category where parent_id in (8)) -- Child of Shoes
        	THEN 'Shoes'
        WHEN product_template.categ_id IN (SELECT id from product_category where parent_id in (43)) -- Child of Dancewear
        	THEN 'Dancewear'
        WHEN product_template.categ_id = 43 -- Dancewear
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
    ceil(sold.product_sale_total::double precision / 52::double precision) AS weekly_average

   FROM product_product
     LEFT JOIN product_template ON product_template.id = product_product.product_tmpl_id
     LEFT JOIN ( SELECT stock_move.product_id,
            sum(stock_move.product_qty) AS product_sale_total
           FROM stock_move
             LEFT JOIN product_product product_product_1 ON product_product_1.id = stock_move.product_id
          WHERE stock_move.location_dest_id = 9 AND stock_move.location_id = 12 AND stock_move.state::text = 'done'::text
                AND stock_move.date >= ('2017-10-01'::date - '1 year'::interval) AND stock_move.date < ('2017-10-01'::date)
          GROUP BY stock_move.product_id) sold ON product_product.id = sold.product_id
     LEFT JOIN ( SELECT stock_move.product_id,
            sum(stock_move.product_qty) AS product_committed_total
           FROM stock_move
             LEFT JOIN product_product product_product_1 ON product_product_1.id = stock_move.product_id
          WHERE stock_move.location_dest_id = 9 AND stock_move.location_id = 12 AND (stock_move.state::text = ANY (ARRAY['confirmed'::character varying, 'assigned'::character varying]::text[]))
          GROUP BY stock_move.product_id) commited ON product_product.id = commited.product_id
     LEFT JOIN ( SELECT sodanca_stock_on_hand.id,
            sodanca_stock_on_hand.quantity_on_hand
           FROM sodanca_stock_on_hand) on_hand ON product_product.id = on_hand.id
  WHERE
    (sold.product_sale_total > 0::numeric
    OR commited.product_committed_total > 0::numeric)
    AND product_template.exclusive_customer IS NULL
    AND product_template.procure_method = 'make_to_stock'
    AND product_template.type = 'product'
    AND product_product.discontinued_product = false

  ORDER BY (
        CASE
            WHEN sold.product_sale_total IS NOT NULL THEN sold.product_sale_total
            ELSE 0::numeric
        END) DESC,
   		product_product.name_template, product_product.name
	),
inventory_grade AS (
    SELECT sodanca_inventory_status_last12.*, (PERCENT_RANK() OVER (PARTITION BY category ORDER BY total_sold DESC))*100 as rank_qty_sold, (PERCENT_RANK() OVER (PARTITION BY category ORDER BY total_sold*gross_margin DESC))*100 as rank_gr_profit
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
        WHEN PERCENT_RANK() OVER (PARTITION BY category ORDER BY total_sold DESC) <= const.grade_a_margin THEN sodanca_inventory_status_last12.weekly_average*const.min_inv_time_a
        WHEN PERCENT_RANK() OVER (PARTITION BY category ORDER BY total_sold DESC) <= const.grade_b_margin THEN sodanca_inventory_status_last12.weekly_average*const.min_inv_time_b
        WHEN PERCENT_RANK() OVER (PARTITION BY category ORDER BY total_sold DESC) <= const.grade_c_margin THEN sodanca_inventory_status_last12.weekly_average*const.min_inv_time_c
        ELSE 0
    END AS adjusted_minimum_stock,
    CASE
        WHEN PERCENT_RANK() OVER (PARTITION BY category ORDER BY total_sold DESC) <= const.grade_a_margin THEN sodanca_inventory_status_last12.weekly_average*const.max_inv_time_a
        WHEN PERCENT_RANK() OVER (PARTITION BY category ORDER BY total_sold DESC) <= const.grade_b_margin THEN sodanca_inventory_status_last12.weekly_average*const.max_inv_time_b
        WHEN PERCENT_RANK() OVER (PARTITION BY category ORDER BY total_sold DESC) <= const.grade_c_margin THEN sodanca_inventory_status_last12.weekly_average*const.max_inv_time_c
        ELSE 0
    END AS adjusted_maximum_stock,

    CASE
        WHEN category_id = ANY (const.categ_jz) THEN mod_jz
        WHEN category_id = ANY (const.categ_ba) THEN mod_ba
        WHEN category_id = ANY (const.categ_ch) THEN mod_ch
        ELSE 1

    END AS order_mod,
    CASE
        WHEN PERCENT_RANK() OVER (PARTITION BY category ORDER BY total_sold*gross_margin DESC) <= const.grade_a_margin THEN const.lead_time_a -- 'A'
        WHEN PERCENT_RANK() OVER (PARTITION BY category ORDER BY total_sold*gross_margin DESC) <= const.grade_b_margin THEN const.lead_time_b -- 'B'
        WHEN PERCENT_RANK() OVER (PARTITION BY category ORDER BY total_sold*gross_margin DESC) <= const.grade_c_margin THEN const.lead_time_c -- 'C'
        ELSE const.lead_time_d -- 'D'
    END AS lead_time
    FROM sodanca_inventory_status_last12, const
    ORDER BY category, name_template, total_sold DESC, sodanca_inventory_status_last12.name, rank_qty_sold

)


 --(product_id, grade, min_stock, max_stock, order_mod, box_size, lead_time)
SELECT product_id, grade_profit AS grade, adjusted_minimum_stock AS min_stock, adjusted_maximum_stock AS max_stock, order_mod, lead_time
FROM inventory_grade);

ALTER TABLE public.sodanca_stock_control_q2_2017
    OWNER to sodanca;

DROP TABLE IF EXISTS sodanca_stock_control_q3_2017;
CREATE TABLE sodanca_stock_control_q3_2017 AS (
WITH
const AS (
select 	.20 as grade_a_margin,
    	.35 as grade_b_margin,
    	.70 as grade_c_margin,
    	9 as lead_time_a,
    	9 as lead_time_b,
    	5 as lead_time_c,
		3 as lead_time_d,
    	1 as min_inv_time_a,
    	2 as max_inv_time_a,
    	4 as min_inv_time_b,
    	6 as max_inv_time_b,
    	1 as min_inv_time_c,
    	12 as max_inv_time_c,
    	0 as min_inv_time_d,
    	0 as max_inv_time_d,
		100 as box_ba_reg,
    	80 as box_ba_larg,
    	36 as box_jz_reg,
        24 as box_jz_larg,
    	12 as box_ch,
    	10 as mod_ba,
    	4 as mod_jz,
    	4 as mod_ch,
    	array[52,55,47,57] as categ_ba,
    	array[53,54,16,60,61,58,59] as categ_ch,
    	array[56] as categ_jz,
    	'Thursday' AS cutoff_date
)
, sodanca_inventory_status_last12 AS (

     SELECT product_product.name_template,
    product_product.name, product_product.id as product_id,
    CASE
        WHEN product_template.categ_id = 64 -- Tights
        	THEN 'Tights'
    	WHEN product_template.categ_id IN (SELECT id from product_category where parent_id in (8)) -- Child of Shoes
        	THEN 'Shoes'
        WHEN product_template.categ_id IN (SELECT id from product_category where parent_id in (43)) -- Child of Dancewear
        	THEN 'Dancewear'
        WHEN product_template.categ_id = 43 -- Dancewear
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
    ceil(sold.product_sale_total::double precision / 52::double precision) AS weekly_average

   FROM product_product
     LEFT JOIN product_template ON product_template.id = product_product.product_tmpl_id
     LEFT JOIN ( SELECT stock_move.product_id,
            sum(stock_move.product_qty) AS product_sale_total
           FROM stock_move
             LEFT JOIN product_product product_product_1 ON product_product_1.id = stock_move.product_id
          WHERE stock_move.location_dest_id = 9 AND stock_move.location_id = 12 AND stock_move.state::text = 'done'::text
                AND stock_move.date >= ('2017-10-01'::date - '1 year'::interval) AND stock_move.date < ('2017-10-01'::date)
          GROUP BY stock_move.product_id) sold ON product_product.id = sold.product_id
     LEFT JOIN ( SELECT stock_move.product_id,
            sum(stock_move.product_qty) AS product_committed_total
           FROM stock_move
             LEFT JOIN product_product product_product_1 ON product_product_1.id = stock_move.product_id
          WHERE stock_move.location_dest_id = 9 AND stock_move.location_id = 12 AND (stock_move.state::text = ANY (ARRAY['confirmed'::character varying, 'assigned'::character varying]::text[]))
          GROUP BY stock_move.product_id) commited ON product_product.id = commited.product_id
     LEFT JOIN ( SELECT sodanca_stock_on_hand.id,
            sodanca_stock_on_hand.quantity_on_hand
           FROM sodanca_stock_on_hand) on_hand ON product_product.id = on_hand.id
  WHERE
    (sold.product_sale_total > 0::numeric
    OR commited.product_committed_total > 0::numeric)
    AND product_template.exclusive_customer IS NULL
    AND product_template.procure_method = 'make_to_stock'
    AND product_template.type = 'product'
    AND product_product.discontinued_product = false

  ORDER BY (
        CASE
            WHEN sold.product_sale_total IS NOT NULL THEN sold.product_sale_total
            ELSE 0::numeric
        END) DESC,
   		product_product.name_template, product_product.name
	),
inventory_grade AS (
    SELECT sodanca_inventory_status_last12.*, (PERCENT_RANK() OVER (PARTITION BY category ORDER BY total_sold DESC))*100 as rank_qty_sold, (PERCENT_RANK() OVER (PARTITION BY category ORDER BY total_sold*gross_margin DESC))*100 as rank_gr_profit
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
        WHEN PERCENT_RANK() OVER (PARTITION BY category ORDER BY total_sold DESC) <= const.grade_a_margin THEN sodanca_inventory_status_last12.weekly_average*const.min_inv_time_a
        WHEN PERCENT_RANK() OVER (PARTITION BY category ORDER BY total_sold DESC) <= const.grade_b_margin THEN sodanca_inventory_status_last12.weekly_average*const.min_inv_time_b
        WHEN PERCENT_RANK() OVER (PARTITION BY category ORDER BY total_sold DESC) <= const.grade_c_margin THEN sodanca_inventory_status_last12.weekly_average*const.min_inv_time_c
        ELSE 0
    END AS adjusted_minimum_stock,
    CASE
        WHEN PERCENT_RANK() OVER (PARTITION BY category ORDER BY total_sold DESC) <= const.grade_a_margin THEN sodanca_inventory_status_last12.weekly_average*const.max_inv_time_a
        WHEN PERCENT_RANK() OVER (PARTITION BY category ORDER BY total_sold DESC) <= const.grade_b_margin THEN sodanca_inventory_status_last12.weekly_average*const.max_inv_time_b
        WHEN PERCENT_RANK() OVER (PARTITION BY category ORDER BY total_sold DESC) <= const.grade_c_margin THEN sodanca_inventory_status_last12.weekly_average*const.max_inv_time_c
        ELSE 0
    END AS adjusted_maximum_stock,

    CASE
        WHEN category_id = ANY (const.categ_jz) THEN mod_jz
        WHEN category_id = ANY (const.categ_ba) THEN mod_ba
        WHEN category_id = ANY (const.categ_ch) THEN mod_ch
        ELSE 1

    END AS order_mod,
    CASE
        WHEN PERCENT_RANK() OVER (PARTITION BY category ORDER BY total_sold*gross_margin DESC) <= const.grade_a_margin THEN const.lead_time_a -- 'A'
        WHEN PERCENT_RANK() OVER (PARTITION BY category ORDER BY total_sold*gross_margin DESC) <= const.grade_b_margin THEN const.lead_time_b -- 'B'
        WHEN PERCENT_RANK() OVER (PARTITION BY category ORDER BY total_sold*gross_margin DESC) <= const.grade_c_margin THEN const.lead_time_c -- 'C'
        ELSE const.lead_time_d -- 'D'
    END AS lead_time
    FROM sodanca_inventory_status_last12, const
    ORDER BY category, name_template, total_sold DESC, sodanca_inventory_status_last12.name, rank_qty_sold

)


 --(product_id, grade, min_stock, max_stock, order_mod, box_size, lead_time)
SELECT product_id, grade_profit AS grade, adjusted_minimum_stock AS min_stock, adjusted_maximum_stock AS max_stock, order_mod, lead_time
FROM inventory_grade);

ALTER TABLE public.sodanca_stock_control_q3_2017
    OWNER to sodanca;

DROP TABLE IF EXISTS sodanca_stock_control_q4_2017;
CREATE TABLE sodanca_stock_control_q4_2017 AS (
WITH
const AS (
select 	.20 as grade_a_margin,
    	.35 as grade_b_margin,
    	.70 as grade_c_margin,
    	9 as lead_time_a,
    	9 as lead_time_b,
    	5 as lead_time_c,
		3 as lead_time_d,
    	1 as min_inv_time_a,
    	2 as max_inv_time_a,
    	4 as min_inv_time_b,
    	6 as max_inv_time_b,
    	1 as min_inv_time_c,
    	12 as max_inv_time_c,
    	0 as min_inv_time_d,
    	0 as max_inv_time_d,
		100 as box_ba_reg,
    	80 as box_ba_larg,
    	36 as box_jz_reg,
        24 as box_jz_larg,
    	12 as box_ch,
    	10 as mod_ba,
    	4 as mod_jz,
    	4 as mod_ch,
    	array[52,55,47,57] as categ_ba,
    	array[53,54,16,60,61,58,59] as categ_ch,
    	array[56] as categ_jz,
    	'Thursday' AS cutoff_date
)
, sodanca_inventory_status_last12 AS (

     SELECT product_product.name_template,
    product_product.name, product_product.id as product_id,
    CASE
        WHEN product_template.categ_id = 64 -- Tights
        	THEN 'Tights'
    	WHEN product_template.categ_id IN (SELECT id from product_category where parent_id in (8)) -- Child of Shoes
        	THEN 'Shoes'
        WHEN product_template.categ_id IN (SELECT id from product_category where parent_id in (43)) -- Child of Dancewear
        	THEN 'Dancewear'
        WHEN product_template.categ_id = 43 -- Dancewear
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
    ceil(sold.product_sale_total::double precision / 52::double precision) AS weekly_average

   FROM product_product
     LEFT JOIN product_template ON product_template.id = product_product.product_tmpl_id
     LEFT JOIN ( SELECT stock_move.product_id,
            sum(stock_move.product_qty) AS product_sale_total
           FROM stock_move
             LEFT JOIN product_product product_product_1 ON product_product_1.id = stock_move.product_id
          WHERE stock_move.location_dest_id = 9 AND stock_move.location_id = 12 AND stock_move.state::text = 'done'::text
                AND stock_move.date >= ('2017-10-01'::date - '1 year'::interval) AND stock_move.date < ('2017-10-01'::date)
          GROUP BY stock_move.product_id) sold ON product_product.id = sold.product_id
     LEFT JOIN ( SELECT stock_move.product_id,
            sum(stock_move.product_qty) AS product_committed_total
           FROM stock_move
             LEFT JOIN product_product product_product_1 ON product_product_1.id = stock_move.product_id
          WHERE stock_move.location_dest_id = 9 AND stock_move.location_id = 12 AND (stock_move.state::text = ANY (ARRAY['confirmed'::character varying, 'assigned'::character varying]::text[]))
          GROUP BY stock_move.product_id) commited ON product_product.id = commited.product_id
     LEFT JOIN ( SELECT sodanca_stock_on_hand.id,
            sodanca_stock_on_hand.quantity_on_hand
           FROM sodanca_stock_on_hand) on_hand ON product_product.id = on_hand.id
  WHERE
    (sold.product_sale_total > 0::numeric
    OR commited.product_committed_total > 0::numeric)
    AND product_template.exclusive_customer IS NULL
    AND product_template.procure_method = 'make_to_stock'
    AND product_template.type = 'product'
    AND product_product.discontinued_product = false

  ORDER BY (
        CASE
            WHEN sold.product_sale_total IS NOT NULL THEN sold.product_sale_total
            ELSE 0::numeric
        END) DESC,
   		product_product.name_template, product_product.name
	),
inventory_grade AS (
    SELECT sodanca_inventory_status_last12.*, (PERCENT_RANK() OVER (PARTITION BY category ORDER BY total_sold DESC))*100 as rank_qty_sold, (PERCENT_RANK() OVER (PARTITION BY category ORDER BY total_sold*gross_margin DESC))*100 as rank_gr_profit
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
        WHEN PERCENT_RANK() OVER (PARTITION BY category ORDER BY total_sold DESC) <= const.grade_a_margin THEN sodanca_inventory_status_last12.weekly_average*const.min_inv_time_a
        WHEN PERCENT_RANK() OVER (PARTITION BY category ORDER BY total_sold DESC) <= const.grade_b_margin THEN sodanca_inventory_status_last12.weekly_average*const.min_inv_time_b
        WHEN PERCENT_RANK() OVER (PARTITION BY category ORDER BY total_sold DESC) <= const.grade_c_margin THEN sodanca_inventory_status_last12.weekly_average*const.min_inv_time_c
        ELSE 0
    END AS adjusted_minimum_stock,
    CASE
        WHEN PERCENT_RANK() OVER (PARTITION BY category ORDER BY total_sold DESC) <= const.grade_a_margin THEN sodanca_inventory_status_last12.weekly_average*const.max_inv_time_a
        WHEN PERCENT_RANK() OVER (PARTITION BY category ORDER BY total_sold DESC) <= const.grade_b_margin THEN sodanca_inventory_status_last12.weekly_average*const.max_inv_time_b
        WHEN PERCENT_RANK() OVER (PARTITION BY category ORDER BY total_sold DESC) <= const.grade_c_margin THEN sodanca_inventory_status_last12.weekly_average*const.max_inv_time_c
        ELSE 0
    END AS adjusted_maximum_stock,

    CASE
        WHEN category_id = ANY (const.categ_jz) THEN mod_jz
        WHEN category_id = ANY (const.categ_ba) THEN mod_ba
        WHEN category_id = ANY (const.categ_ch) THEN mod_ch
        ELSE 1

    END AS order_mod,
    CASE
        WHEN PERCENT_RANK() OVER (PARTITION BY category ORDER BY total_sold*gross_margin DESC) <= const.grade_a_margin THEN const.lead_time_a -- 'A'
        WHEN PERCENT_RANK() OVER (PARTITION BY category ORDER BY total_sold*gross_margin DESC) <= const.grade_b_margin THEN const.lead_time_b -- 'B'
        WHEN PERCENT_RANK() OVER (PARTITION BY category ORDER BY total_sold*gross_margin DESC) <= const.grade_c_margin THEN const.lead_time_c -- 'C'
        ELSE const.lead_time_d -- 'D'
    END AS lead_time
    FROM sodanca_inventory_status_last12, const
    ORDER BY category, name_template, total_sold DESC, sodanca_inventory_status_last12.name, rank_qty_sold

)


 --(product_id, grade, min_stock, max_stock, order_mod, box_size, lead_time)
SELECT product_id, grade_profit AS grade, adjusted_minimum_stock AS min_stock, adjusted_maximum_stock AS max_stock, order_mod, lead_time
FROM inventory_grade);

ALTER TABLE public.sodanca_stock_control_q4_2017
    OWNER to sodanca;
