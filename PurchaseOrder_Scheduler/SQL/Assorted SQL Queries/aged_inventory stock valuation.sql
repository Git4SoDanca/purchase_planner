SELECT 
  sodanca_stock_on_hand.id, 
  sodanca_stock_on_hand.template_name, 
  sodanca_stock_on_hand.product_name, 
  sodanca_stock_on_hand.default_code, 
  sodanca_stock_on_hand.standard_price, 
  sodanca_stock_on_hand.quantity_on_hand, 
  (sodanca_stock_on_hand.standard_price*sodanca_stock_on_hand.quantity_on_hand) AS ext_total,
  CASE 
    WHEN (MAX(sodanca_last_product_move.max)> (current_date - INTERVAL '1 year'))
	THEN 'current'
	ELSE 'old'
    END
    AS inventory_status
FROM 
  public.sodanca_stock_on_hand

LEFT JOIN 
  public.sodanca_last_product_move ON sodanca_last_product_move.product_id = sodanca_stock_on_hand.id

WHERE 
  sodanca_stock_on_hand.quantity_on_hand > 0
  
GROUP BY 
  sodanca_stock_on_hand.id, 
  sodanca_stock_on_hand.template_name, 
  sodanca_stock_on_hand.product_name, 
  sodanca_stock_on_hand.default_code, 
  sodanca_stock_on_hand.standard_price, 
  sodanca_stock_on_hand.quantity_on_hand
ORDER BY 
  sodanca_stock_on_hand.template_name, 
  sodanca_stock_on_hand.product_name