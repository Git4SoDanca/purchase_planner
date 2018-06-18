SELECT 
  product_template.name, 
  product_product.name, 
  product_variant_dimension_option.name, 
  product_variant_dimension_option.code, 
  product_variant_dimension_option.select_name, 
  product_variant_dimension_type.name, 
  product_variant_dimension_type.product_category
FROM 
  public.product_product, 
  public.product_template, 
  public.product_product_dimension_rel, 
  public.product_variant_dimension_option, 
  public.product_variant_dimension_type, 
  public.product_variant_dimension_value
WHERE 
  product_product.product_tmpl_id = product_template.id AND
  product_product_dimension_rel.product_id = product_product.id AND
  product_variant_dimension_option.dimension_id = product_variant_dimension_type.id AND
  product_variant_dimension_value.dimension_id = product_product_dimension_rel.dimension_id AND
  product_variant_dimension_value.option_id = product_variant_dimension_option.id AND 
	product_variant_dimension_type.name = 'Color'
