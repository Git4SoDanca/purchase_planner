WITH sodanca_inventory_status_last12 AS (

     SELECT product_product.name_template,
    product_product.name,
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
          WHERE stock_move.location_dest_id = 9 AND stock_move.location_id = 12 AND stock_move.state::text = 'done'::text AND stock_move.date >= (now() - '1 year'::interval)
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
        END) DESC, product_product.name_template, product_product.name
)



SELECT sodanca_inventory_status_last12.*, (PERCENT_RANK() OVER (PARTITION BY category ORDER BY total_sold DESC))*100 as rank_qty_sold, (PERCENT_RANK() OVER (PARTITION BY category ORDER BY total_sold*gross_margin DESC))*100 as rank_gr_profit
,
CASE
	WHEN PERCENT_RANK() OVER (PARTITION BY category ORDER BY total_sold DESC ) <= .22 THEN 'A'
    WHEN PERCENT_RANK() OVER (PARTITION BY category ORDER BY total_sold DESC) <= .40 THEN 'B'
    WHEN PERCENT_RANK() OVER (PARTITION BY category ORDER BY total_sold DESC) <= .70 THEN 'C'
    ELSE 'D'
END AS grade_qty_sold,
CASE
	WHEN PERCENT_RANK() OVER (PARTITION BY category ORDER BY total_sold*gross_margin DESC) <= .22 THEN 'A'
    WHEN PERCENT_RANK() OVER (PARTITION BY category ORDER BY total_sold*gross_margin DESC) <= .40 THEN 'B'
    WHEN PERCENT_RANK() OVER (PARTITION BY category ORDER BY total_sold*gross_margin DESC) <= .70 THEN 'C'
    ELSE 'D'
END AS grade_profit,
CASE
	WHEN PERCENT_RANK() OVER (PARTITION BY category ORDER BY total_sold DESC ) <= .22 THEN sodanca_inventory_status_last12.weekly_average*4
    WHEN PERCENT_RANK() OVER (PARTITION BY category ORDER BY total_sold DESC) <= .40 THEN sodanca_inventory_status_last12.weekly_average*2
    WHEN PERCENT_RANK() OVER (PARTITION BY category ORDER BY total_sold DESC) <= .70 THEN 1
    ELSE 0
END AS adjusted_minimum_stock,
CASE
	WHEN PERCENT_RANK() OVER (PARTITION BY category ORDER BY total_sold DESC ) <= .22 THEN sodanca_inventory_status_last12.weekly_average*8
    WHEN PERCENT_RANK() OVER (PARTITION BY category ORDER BY total_sold DESC) <= .40 THEN sodanca_inventory_status_last12.weekly_average*5
    WHEN PERCENT_RANK() OVER (PARTITION BY category ORDER BY total_sold DESC) <= .70 THEN 1
    ELSE 0
END AS adjusted_maximum_stock
FROM sodanca_inventory_status_last12
ORDER BY category, name_template, total_sold DESC, sodanca_inventory_status_last12.name, rank_qty_sold
