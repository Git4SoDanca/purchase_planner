--Create stock control tables

DROP TABLE IF EXISTS sodanca_stock_control;
CREATE TABLE sodanca_stock_control AS
(
WITH
const AS (
select 	.22 as grade_a_margin,
    	.40 as grade_b_margin,
    	.70 as grade_c_margin,
    	9 as lead_time_a,
    	9 as lead_time_b,
    	5 as lead_time_c,
		  3 as lead_time_d,
    	2 as min_inv_time_a,
    	3 as max_inv_time_a,
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
    (sold.product_sale_total::double precision / 52::double precision) AS weekly_average

   FROM product_product
     LEFT JOIN product_template ON product_template.id = product_product.product_tmpl_id
     LEFT JOIN ( SELECT stock_move.product_id,
            sum(stock_move.product_qty) AS product_sale_total
           FROM stock_move
             LEFT JOIN product_product product_product_1 ON product_product_1.id = stock_move.product_id
          WHERE stock_move.location_dest_id = 9 AND stock_move.location_id = 12 AND stock_move.state::text = 'done'::text
                AND stock_move.date >= (now()::date - '1 year'::interval)
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
END AS order_mod,
    CASE
    WHEN inventory_grade.lead_time IS NOT NULL
    THEN inventory_grade.lead_time
    ELSE 5
END AS lead_time
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
      IS 'Reset nightly, used by stock purchase planner';

--SELECT * FROM product_product WHERE id NOT IN (select product_id FROM sodanca_stock_control ) AND active = true AND procure_method = 'make_to_stock' and discontinued_product = false AND grade is  null order by name_template, default_code

-- +++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++
-- Creating functions
-- +++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++

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

SELECT sum(stock_move.product_qty) AS product_committed_total
FROM stock_move
WHERE
	stock_move.location_dest_id = 9
    AND stock_move.location_id = 12
    AND (stock_move.state::text = ANY (ARRAY['confirmed'::character varying, 'assigned'::character varying]::text[]))
    AND date_expected >= $2
    AND date_expected < $3
    AND stock_move.product_id = $1
GROUP BY stock_move.product_id

$BODY$;

ALTER FUNCTION public.sd_qcomm(integer, date, date)
    OWNER TO sodanca;

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

SELECT sum(stock_move.product_qty) AS on_order_total
FROM stock_move
WHERE
	stock_move.location_dest_id = 12
    AND stock_move.location_id = 8
    AND (stock_move.state::text = ANY (ARRAY['confirmed'::character varying, 'assigned'::character varying]::text[]))
    AND date_expected >= $2 --now()::date
    AND date_expected <= $3 --now()::date
    AND stock_move.product_id = $1
GROUP BY stock_move.product_id

$BODY$;

ALTER FUNCTION public.sd_qoo(integer, date, date)
    OWNER TO sodanca;

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
    	WHEN sum(stock_move.product_qty) != 0 THEN sum(stock_move.product_qty) ELSE 0 END AS on_order_total
FROM stock_move
WHERE
	stock_move.location_dest_id = 9
    AND stock_move.location_id = 12
    AND (stock_move.state::text = 'done'::character varying)
    AND date_expected >= $2 --start_date
    AND date_expected < $3 --end_date
    AND stock_move.product_id = $1
GROUP BY stock_move.product_id

$BODY$;

ALTER FUNCTION public.sd_qs(integer, date, date)
    OWNER TO sodanca;

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


-- Quantity on hand expected
CREATE OR REPLACE FUNCTION public.sd_expected_onhand( pid integer, start_date date) RETURNS numeric
LANGUAGE 'sql'
COST 100
VOLATILE AS $BODY$
SELECT (sd_qoh($1)+COALESCE(sd_qoo($1,(now()-'6 months'::interval)::date,$2),0)-COALESCE(GREATEST(sd_qs($1,now()::date,$2),sd_qcomm($1,(now()-'6 months'::interval)::date,$2)),0));


$BODY$;


ALTER FUNCTION public.sd_expected_onhand(integer, date) OWNER TO sodanca;

-- Sales trend
CREATE FUNCTION sd_sales_trend(pid int) RETURNS decimal AS
$$
SELECT round(sd_qs($1,(now()-'6 months'::interval)::date, now()::date)/sd_qs($1,(now()- '18 months'::interval)::date,(now()- '12 months'::interval)::date)*100,2) as growth;
$$ LANGUAGE SQL;

-- Quantity to order - Purchase planner
CREATE OR REPLACE FUNCTION public.sd_quantity_to_order(
	pid integer,
	start_date date,
	end_date date)
    RETURNS numeric
    LANGUAGE 'sql'

    COST 100
    VOLATILE

AS $BODY$

SELECT GREATEST(sd_qs($1,$2,$3),sd_qcomm($1,$2,$3))+COALESCE(sd_qoo($1,$2,$3),0)-COALESCE(sd_expected_onhand($1,$2),0) AS qty_to_order from product_product

$BODY$;

ALTER FUNCTION public.sd_quantity_to_order(integer, date, date)
    OWNER TO sodanca;
