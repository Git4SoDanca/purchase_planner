SELECT product_template.name FROM product_template
LEFT JOIN product_tag_product_template_rel ON
	product_tag_product_template_rel.product_template_id = product_template.id
LEFT JOIN product_tag ON product_tag_product_template_rel.product_tag_id = product_tag.id
WHERE product_tag.name IN ('Fashion 2016 - Volume 3','Fashion 2017 - Volume 1')
ORDER BY product_template.name