UPDATE 
    public.product_product
SET discontinued_product = true
WHERE  
  product_tmpl_id IN (
    SELECT 
      product_tag_product_template_rel.product_template_id
    FROM 
      public.product_tag_product_template_rel
    WHERE product_template_id NOT IN (
        SELECT 
	    product_tag_product_template_rel.product_template_id
        FROM 
	    public.product_tag_product_template_rel
        WHERE 
            product_tag_id IN (9,10,11,12,13,15)
    )
  )
