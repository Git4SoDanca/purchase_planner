SELECT 
  product_tag.name, 
  product_template.name, 
  product_product.name, 
  --account_invoice_line.name,
  --account_invoice.number
  AVG(product_template.list_price) AS LIST_PRICE, 
  MIN(account_invoice_line.price_unit) AS MIN_INVOICE_PRICE, 
  MAX(account_invoice_line.price_unit) AS MAX_INVOICE_PRICE,
  SUM(account_invoice_line.price_subtotal) AS TOTAL_AMOUNT,
  SUM(account_invoice_line.quantity) AS TOTAL_QUANTITY
FROM 
  public.account_invoice_line
LEFT JOIN public.product_product ON account_invoice_line.product_id = product_product.id
LEFT JOIN public.product_template ON product_product.product_tmpl_id = product_template.id
LEFT JOIN public.product_tag_product_template_rel ON product_tag_product_template_rel.product_template_id = product_template.id
LEFT JOIN public.product_tag ON product_tag_product_template_rel.product_tag_id = product_tag.id
LEFT JOIN public.account_invoice ON account_invoice.id = account_invoice_line.invoice_id
WHERE 
  product_tag.name IN ('Classic Shoes 2017', 'Classic Dancewear 2017') 
  --AND product_product.name = 'TS82 Black L-XL'
  AND account_invoice.type = 'out_invoice'
GROUP BY   
  product_product.name,product_template.name, product_tag.name
ORDER BY 
  product_tag.name, 
  product_template.name, 
  product_product.name  
