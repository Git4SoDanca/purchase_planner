UPDATE stock_move SET packed = false WHERE id IN (
	SELECT id
	FROM stock_move 
	WHERE 
		picking_id IN (
			SELECT id 
			FROM stock_picking 
			WHERE 
				type = 'out' 
				AND state IN ('assigned','confirmed')
				AND shipping_state = 'draft'
		) 
		AND packed = true
		AND state IN ('assigned','confirmed')

	ORDER by origin

)