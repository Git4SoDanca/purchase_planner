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
  AND stock_move.date <= (now()::date - interval '300d')
  AND stock_move.date > (now()::date - interval '330d')
  
GROUP BY
  stock_move.product_id,
  product_product.name_template, 
  product_product.name, 
  product_product.default_code
ORDER BY
  product_product.name_template, 
  product_product.default_code


  
