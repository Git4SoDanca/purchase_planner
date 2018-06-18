SELECT 
  sodanca_barcode.style_name, 
  sodanca_barcode.name, 
  sodanca_barcode.product_options, 
  sodanca_barcode.description_sale, 
  sodanca_barcode.barcode, 
  product_template.list_price as wholesale_price,
  product_template.list_price *2 as msrp,
  case when (sodanca_barcode.name = 'sd16') then
	(product_template.list_price*2) 
  else 
	((product_template.list_price *2)-(product_template.list_price *.15))
  end as minimum_advertised_price
FROM 
  public.sodanca_barcode, 
  public.product_template
WHERE 
  sodanca_barcode.style_name = product_template.name 
  AND LEFT(barcode,3) != '730';
