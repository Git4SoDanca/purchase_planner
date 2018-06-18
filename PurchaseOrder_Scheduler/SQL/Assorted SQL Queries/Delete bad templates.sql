/* Check for bad templates*/

SELECT 
  product_template.id, 
  product_template.name, 
  product_uom.name, 
  product_template.active, 
  product_uom.id
FROM 
  public.product_template, 
  public.product_uom
WHERE 
  product_template.uom_id = product_uom.id AND
  product_template.id Not in (SELECT distinct product_product.product_tmpl_id FROM public.product_product)
  AND product_uom.id =5 
  AND product_template.active = TRUE;

/* Update/Delete bad templates */  

UPDATE public.product_template SET active = false WHERE product_template.id IN (
SELECT 
  product_template.id
FROM 
  public.product_template, 
  public.product_uom
WHERE 
  product_template.uom_id = product_uom.id AND
  product_template.id Not in (SELECT distinct product_product.product_tmpl_id FROM public.product_product)
  AND product_uom.id =5 
  AND product_template.active = TRUE
  );
