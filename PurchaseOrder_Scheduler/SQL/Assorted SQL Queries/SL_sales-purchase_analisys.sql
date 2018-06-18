SELECT product_product.name_template, product_product.name, ON_HAND.quantity_on_hand, SOLD.product_sale_total, COMMITED.product_committed_total, 
ceil(SOLD.product_sale_total/((SELECT EXTRACT (WEEK FROM CURRENT_DATE))-5)) as weekly_average, (ceil(SOLD.product_sale_total/((SELECT EXTRACT (WEEK FROM CURRENT_DATE))-5)) *2) AS MINIMUM_STOCK, (ceil(SOLD.product_sale_total/((SELECT EXTRACT (WEEK FROM CURRENT_DATE))-5)) *5) AS MAXIMUM_STOCK,
CASE 
	WHEN (ceil(SOLD.product_sale_total/((SELECT EXTRACT (WEEK FROM CURRENT_DATE))-5))*5) < ON_HAND.quantity_on_hand THEN 'Overstocked'
	WHEN (ceil(SOLD.product_sale_total/((SELECT EXTRACT (WEEK FROM CURRENT_DATE))-5))*2) > ON_HAND.quantity_on_hand THEN 'Understocked'
	WHEN ((ceil(SOLD.product_sale_total/((SELECT EXTRACT (WEEK FROM CURRENT_DATE))-5))*2) <= ON_HAND.quantity_on_hand 
		AND (ceil(SOLD.product_sale_total/((SELECT EXTRACT (WEEK FROM CURRENT_DATE))-5))*5) >= ON_HAND.quantity_on_hand)
		THEN 'OK'
	ELSE 'Error'
END as Inventory_status

FROM product_product 

--On Hand
LEFT JOIN ( SELECT id, quantity_on_hand 
FROM sodanca_stock_on_hand
WHERE LEFT(template_name,2) = 'SL' --product filter
) AS ON_HAND ON product_product.id = ON_HAND.id

--Sold
LEFT JOIN (SELECT product_id, SUM(stock_move.product_qty) AS product_sale_total
FROM stock_move
LEFT JOIN product_product ON product_product.id = stock_move.product_id
WHERE --completed sale
	location_dest_id = 9    --to customer
	AND location_id = 12   --from stock
	AND state = 'done'    --completed move
	AND LEFT(product_product.name_template,2) = 'SL' --product filter
	AND date >= '2017-01-01'
GROUP BY product_id) AS SOLD ON product_product.id = SOLD.product_id

--Committed
LEFT JOIN (SELECT product_id, SUM(stock_move.product_qty) AS product_committed_total
FROM stock_move
LEFT JOIN product_product ON product_product.id = stock_move.product_id
WHERE --commited
	location_dest_id = 9    --to customer
	AND location_id = 12   --from stock   
	AND state IN ('confirmed','assigned')    --commited
	AND LEFT(product_product.name_template,2) = 'SL' --product filter
	GROUP BY product_id) AS COMMITED ON product_product.id = COMMITED.product_id
WHERE SOLD.product_sale_total>0 OR COMMITED.product_committed_total >0
ORDER BY product_product.name_template, product_product.name