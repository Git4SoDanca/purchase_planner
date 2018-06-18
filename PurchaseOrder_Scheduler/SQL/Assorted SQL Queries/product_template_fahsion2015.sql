SELECT 
  product_template.name, 
  product_tag.id, 
  product_tag.name
FROM 
  public.product_template, 
  public.product_tag, 
  public.product_tag_product_template_rel
WHERE 
  product_template.id = product_tag_product_template_rel.product_template_id AND
  product_tag_product_template_rel.product_tag_id = product_tag.id AND
  LEFT(product_tag.name,12) = 'Fashion 2015'
