SELECT
  stock_move.product_id,
  product_product.name_template, 
  product_product.name, 
  product_product.default_code,
  SUM(stock_move.product_qty)

FROM 
  public.stock_move, 
  public.product_product

WHERE 
  stock_move.product_id = product_product.id
  AND stock_move.location_dest_id = 9
  AND stock_move.location_id = 12
  AND stock_move.state in ('done')
  AND product_product.product_tmpl_id IN (
	SELECT product_template.id FROM product_template
	LEFT JOIN product_tag_product_template_rel ON
		product_tag_product_template_rel.product_template_id = product_template.id
	LEFT JOIN product_tag ON product_tag_product_template_rel.product_tag_id = product_tag.id
	WHERE product_tag.name IN ('Classic Dancewear 2017','Fashion 2017 - Volume 1')
	ORDER BY product_template.name
  )
  
GROUP BY
  stock_move.product_id,
  product_product.name_template, 
  product_product.name, 
  product_product.default_code
ORDER BY
  product_product.name_template, 
  product_product.default_code

