SELECT 
	* , 
	substring(valuation.default_code,0,(Select length(valuation.default_code) - position('_' in reverse(valuation.default_code)) + 1)) as product_size_group,
	CASE
		WHEN stock_moves.MAXDATE < (current_date - INTERVAL'365 days')
			THEN 'Older than 1 year'
		WHEN stock_moves.MAXDATE >= (current_date - INTERVAL '365 days')
			THEN 'Current'	
		ELSE 'ERROR'
	    END AS age
FROM 
	(SELECT 
		public.product_product.id AS product_id,
		public.product_product.name_template, 
		public.product_product.name AS product_name, 
		public.product_product.default_code,
		public.product_template.standard_price, 
		sodanca_stock_on_hand.quantity_on_hand, 
		public.product_template.standard_price*sodanca_stock_on_hand.quantity_on_hand AS Amount
	FROM 
		(public.product_product INNER JOIN public.product_template ON public.product_product.product_tmpl_id = public.product_template.id) 
		INNER JOIN public.sodanca_stock_on_hand ON public.product_product.id = sodanca_stock_on_hand.id
	ORDER BY public.product_product.name) AS valuation
inner JOIN 
	(
	SELECT 
		product_id,MAX(date) as MAXDATE
	    
	FROM 
		public.stock_move
	WHERE product_id in (
		SELECT id 	
		FROM 
			sodanca_stock_on_hand
		WHERE 
			quantity_on_hand > 0
	
		)
	GROUP BY product_id
	) as stock_moves
 ON valuation.product_id = stock_moves.product_id
 WHERE 
	quantity_on_hand > 0
 ORDER BY 
	age,
	product_size_group;