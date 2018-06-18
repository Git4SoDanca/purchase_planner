﻿SELECT product_product.name_template, product_product.name, ON_HAND.quantity_on_hand, ON_ORDER.quantity_on_order, SOLD.product_sale_total, COMMITED.product_committed_total
FROM product_product 
-- no date params set
--On Hand
LEFT JOIN ( SELECT id, quantity_on_hand 
FROM sodanca_stock_on_hand
WHERE left(template_name,2) = 'UG' --template_name IN ('UG201','UG202','UG203','UG204','UG207','UG208') --product filter
) AS ON_HAND ON product_product.id = ON_HAND.id

--On Order
LEFT JOIN (SELECT product_id, SUM(stock_move.product_qty) AS quantity_on_order
FROM stock_move
LEFT JOIN product_product ON product_product.id = stock_move.product_id
WHERE --completed sale
	location_dest_id = 12    --to stock
	AND location_id = 8   --from supplier
	AND state IN ('confirmed','assigned')    --to do move
	AND left(product_product.name_template,2) = 'UG' --product filter
GROUP BY product_id) AS ON_ORDER ON product_product.id = ON_ORDER.product_id

--Sold
LEFT JOIN (SELECT product_id, SUM(stock_move.product_qty) AS product_sale_total
FROM stock_move
LEFT JOIN product_product ON product_product.id = stock_move.product_id
WHERE --completed sale
	location_dest_id = 9    --to customer
	AND location_id = 12   --from stock
	AND state = 'done'    --completed move
	AND left(product_product.name_template,2) = 'UG' --product filter
GROUP BY product_id) AS SOLD ON product_product.id = SOLD.product_id

--Committed
LEFT JOIN (SELECT product_id, SUM(stock_move.product_qty) AS product_committed_total
FROM stock_move
LEFT JOIN product_product ON product_product.id = stock_move.product_id
WHERE --commited
	location_dest_id = 9    --to customer
	AND location_id = 12   --from stock   
	AND state = 'confirmed'    --commited
	AND left(product_product.name_template,2) = 'UG' --product filter
	GROUP BY product_id) AS COMMITED ON product_product.id = COMMITED.product_id
WHERE SOLD.product_sale_total>0 OR COMMITED.product_committed_total >0
ORDER BY product_product.name_template, product_product.name