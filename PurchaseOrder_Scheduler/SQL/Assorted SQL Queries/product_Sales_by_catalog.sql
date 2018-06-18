SELECT product_product.name_template, product_product.name, SUM(stock_move.product_qty) AS product_sale_total
FROM stock_move
LEFT JOIN product_product ON product_product.id = stock_move.product_id
WHERE --completed sale
	location_dest_id = 9    --to customer
	AND location_id = 12   --from stock
	AND state = 'done'    --completed move
	AND product_product.name_template IN (
		SELECT 
		  product_template.name
		FROM 
		  public.product_tag, 
		  public.product_tag_product_template_rel, 
		  public.product_template
		WHERE 
		  product_tag.id = product_tag_product_template_rel.product_tag_id AND
		  product_tag_product_template_rel.product_template_id = product_template.id
		  AND product_tag.name = 'Fashion 2017 - Volume 3'
	) --product filter
GROUP BY product_product.name_template, product_product.name
ORDER BY name_template, name