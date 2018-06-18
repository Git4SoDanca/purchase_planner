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
  AND stock_move.location_dest_id = 12
  AND stock_move.location_id = 8
  AND stock_move.state in ('assigned','confirmed','waiting')
  AND stock_move.date_expected < (now()::date + interval '30d')
  
GROUP BY
  stock_move.product_id,
  product_product.name_template, 
  product_product.name, 
  product_product.default_code
ORDER BY
  product_product.name_template, 
  product_product.default_code


  
