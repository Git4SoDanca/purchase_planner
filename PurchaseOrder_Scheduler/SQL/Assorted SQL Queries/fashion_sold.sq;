SELECT product_product.name_template, product_product.name, SOLD.product_sale_total
FROM product_product

--Sold
LEFT JOIN (SELECT product_id, SUM(stock_move.product_qty) AS product_sale_total
FROM stock_move
LEFT JOIN product_product ON product_product.id = stock_move.product_id
WHERE --completed sale
	location_dest_id = 9    --to customer
	AND location_id = 12   --from stock
	AND state = 'done'    --completed move
	AND product_product.name_template IN (SELECT product_template.name FROM product_template
LEFT JOIN product_tag_product_template_rel ON
	product_tag_product_template_rel.product_template_id = product_template.id
LEFT JOIN product_tag ON product_tag_product_template_rel.product_tag_id = product_tag.id
WHERE product_tag.name IN ('Fashion 2016 - Volume 3','Fashion 2016 - Volume 2','Fashion 2016 - Volume 1','Fashion 2017 - Volume 1','Fashion 2017 - Volume 2')
ORDER BY product_template.name) --product filter
GROUP BY product_id) AS SOLD ON product_product.id = SOLD.product_id
