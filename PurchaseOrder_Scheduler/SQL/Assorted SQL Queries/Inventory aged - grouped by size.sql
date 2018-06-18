SELECT * FROM 
	(SELECT 
	  product_template.name,
	  product_template.standard_price,
	  substring(product_product.default_code,0,(Select length(product_product.default_code) - position('_' in reverse(product_product.default_code)) + 1)) as product_size_group,
	  SUM(sodanca_stock_on_hand.quantity_on_hand) as total_on_hand,
	  MAX(stock_move.date) AS last_move
	FROM 
	  public.stock_move 
	  LEFT JOIN public.product_product ON stock_move.product_id = product_product.id
	  LEFT JOIN sodanca_stock_on_hand ON product_product.id = sodanca_stock_on_hand.id
	  LEFT JOIN product_template ON product_product.product_tmpl_id = product_template.id
	WHERE 
		stock_move.state = 'done' AND
		stock_move.location_dest_id = 9
	GROUP BY 
	
		product_size_group,
		product_template.name,
		product_template.standard_price
	ORDER BY 
	  last_move DESC
	) as main
WHERE total_on_hand > 0;

