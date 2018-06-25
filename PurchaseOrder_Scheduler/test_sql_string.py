import configparser

config = configparser.ConfigParser()
config.sections()
config.read('config.ini')
companycode = 'USA'

table_queries = ['']*2
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
		OWNER to {login};
	-- Update grades on product_product table
	UPDATE product_product SET grade = sodanca_stock_control.grade FROM sodanca_stock_control
	WHERE product_product.id = sodanca_stock_control.id;
	""".format(grade_a_margin = config[companycode]['grade_a_margin'], grade_b_margin = config[companycode]['grade_b_margin'], grade_c_margin = config[companycode]['grade_c_margin'], min_inv_time_a = config[companycode]['min_inv_time_a'], max_inv_time_a = config[companycode]['max_inv_time_a'], min_inv_time_b = config[companycode]['min_inv_time_b'], max_inv_time_b = config[companycode]['max_inv_time_b'], min_inv_time_c = config[companycode]['min_inv_time_c'], max_inv_time_c = config[companycode]['max_inv_time_c'], min_inv_time_d = config[companycode]['min_inv_time_d'], max_inv_time_d = config[companycode]['max_inv_time_d'], categ_ba = config[companycode]['categ_ba'], categ_ch = config[companycode]['categ_ch'], categ_jz = config[companycode]['categ_jz'], categ_tights = config[companycode]['categ_tights'], categ_shoes = config[companycode]['categ_shoes'], categ_dwear = config[companycode]['categ_dwear'], wh_stock = config[companycode]['wh_stock'], customers = config[companycode]['customers'], supplier = config[companycode]['supplier'], login=config[companycode]['login'])
print(table_queries[0])
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
				# grade_a_margin = config[companycode]['grade_a_margin'],
				# grade_b_margin = config[companycode]['grade_b_margin'],
				# grade_c_margin = config[companycode]['grade_c_margin'],
				# min_inv_time_a = config[companycode]['min_inv_time_a'],
				# max_inv_time_a = config[companycode]['max_inv_time_a'],
				# min_inv_time_b = config[companycode]['min_inv_time_b'],
				# max_inv_time_b = config[companycode]['max_inv_time_b'],
				# min_inv_time_c = config[companycode]['min_inv_time_c'],
				# max_inv_time_c = config[companycode]['max_inv_time_c'],
				# min_inv_time_d = config[companycode]['min_inv_time_d'],
				# max_inv_time_d = config[companycode]['max_inv_time_d'],
				# categ_ba = config[companycode]['categ_ba'],
				# categ_ch = config[companycode]['categ_ch'],
				# categ_jz = config[companycode]['categ_jz'],
				# categ_tights = config[companycode]['categ_tights'],
				# categ_shoes = config[companycode]['categ_shoes'],
				# categ_dwear = config[companycode]['categ_dwear'],
				# wh_stock = config[companycode]['wh_stock'],
				# customers = config[companycode]['customers'],
				# supplier = config[companycode]['supplier'],
				login=config[companycode]['login'])
print(table_queries[0])
