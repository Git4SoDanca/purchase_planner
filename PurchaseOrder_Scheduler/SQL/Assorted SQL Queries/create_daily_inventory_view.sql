CREATE OR REPLACE VIEW public.sodanca_daily_inventory AS 
 SELECT DISTINCT sodanca_stock_on_hand.product_name,
    sodanca_stock_on_hand.template_name AS style,
    sodanca_stock_on_hand.default_code AS sku,
    sodanca_stock_on_hand.quantity_on_hand,
    product_barcode.barcode,
    product_template.list_price AS wholesale_price,
    product_template.list_price * 2::numeric AS msrp
   FROM sodanca_stock_on_hand
     LEFT JOIN product_barcode ON product_barcode.product_id = sodanca_stock_on_hand.id
     LEFT JOIN product_product ON product_product.id = sodanca_stock_on_hand.id
     LEFT JOIN product_template ON product_template.id = product_product.product_tmpl_id
  WHERE 
     product_template.exclusive_customer IS NULL 
     AND product_product.exclusive_customer IS NULL
     AND product_product.active = true 
     AND product_product.procure_method::text = 'make_to_stock'::text 
     AND product_product.discontinued_product = false AND product_product.no_discount = false
     AND product_template.type = 'product'
  ORDER BY sodanca_stock_on_hand.template_name, sodanca_stock_on_hand.product_name;

ALTER TABLE public.sodanca_daily_inventory
  OWNER TO sodanca;

