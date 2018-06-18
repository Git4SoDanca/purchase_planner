 SELECT product_product.id,
    product_template.name AS template_name,
    product_product.name AS product_name,
    product_product.default_code,
    product_template.standard_price,
    sum(
        CASE
            WHEN (stock_move.location_dest_id IN ( SELECT stock_location.id
               FROM stock_location
              WHERE stock_location.usage::text = 'internal'::text)) AND stock_move.state::text = 'done'::text THEN stock_move.product_qty
            ELSE 0.0
        END) - sum(
        CASE
            WHEN (stock_move.location_id IN ( SELECT stock_location.id
               FROM stock_location
              WHERE stock_location.usage::text = 'internal'::text)) AND stock_move.state::text = 'done'::text THEN stock_move.product_qty
            ELSE 0.0
        END) AS quantity_on_hand
   FROM product_product
     LEFT JOIN stock_move ON stock_move.product_id = product_product.id
     LEFT JOIN product_template ON product_template.id = product_product.product_tmpl_id
  GROUP BY product_template.name, product_product.name, product_product.id, product_product.default_code, product_template.standard_price
  ORDER BY product_template.name, product_product.name, product_product.id, product_product.default_code;