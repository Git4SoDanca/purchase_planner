SELECT product_product.name_template, product_product.name, ON_HAND.quantity_on_hand, ON_ORDER.quantity_on_order, SOLD.product_sale_total, COMMITED.product_committed_total
FROM product_product 

--On Hand
LEFT JOIN ( SELECT id, quantity_on_hand 
FROM sodanca_stock_on_hand
WHERE template_name IN ('TS69','TS70','TS73','TS74','TS77','TS78','TS81','TS82','TS95','TS96','TS98')  --product filter
) AS ON_HAND ON product_product.id = ON_HAND.id

--On Order
LEFT JOIN (SELECT product_id, SUM(stock_move.product_qty) AS quantity_on_order
FROM stock_move
LEFT JOIN product_product ON product_product.id = stock_move.product_id
WHERE --completed sale
	location_dest_id = 12    --to stock
	AND location_id = 8   --from supplier
	AND state IN ('confirmed','assigned')    --completed move
	AND product_product.name_template IN ('TS69','TS70','TS73','TS74','TS77','TS78','TS81','TS82','TS95','TS96','TS98')  --product filter
GROUP BY product_id) AS ON_ORDER ON product_product.id = ON_ORDER.product_id

--Sold
LEFT JOIN (SELECT product_id, SUM(stock_move.product_qty) AS product_sale_total
FROM stock_move
LEFT JOIN product_product ON product_product.id = stock_move.product_id
WHERE --completed sale
	location_dest_id = 9    --to customer
	AND location_id = 12   --from stock
	AND state = 'done'    --completed move
	AND product_product.name_template IN ('TS69','TS70','TS73','TS74','TS77','TS78','TS81','TS82','TS95','TS96','TS98')  --product filter
GROUP BY product_id) AS SOLD ON product_product.id = SOLD.product_id

--Committed
LEFT JOIN (SELECT product_id, SUM(stock_move.product_qty) AS product_committed_total
FROM stock_move
LEFT JOIN product_product ON product_product.id = stock_move.product_id
WHERE --commited
	location_dest_id = 9    --to customer
	AND location_id = 12   --from stock   
	AND state = 'confirmed'    --commited
	AND product_product.name_template IN ('TS69','TS70','TS73','TS74','TS77','TS78','TS81','TS82','TS95','TS96','TS98')  --product filter
	GROUP BY product_id) AS COMMITED ON product_product.id = COMMITED.product_id
WHERE SOLD.product_sale_total>0 OR COMMITED.product_committed_total >0
ORDER BY product_product.name_template, product_product.name