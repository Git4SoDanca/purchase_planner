SELECT * FROM product_tag ORDER BY name

SELECT * FROM product_template LEFT JOIN product_tag_product_template_rel ON product_template.id = product_tag_product_template_rel.product_template_id WHERE product_tag_product_template_rel.product_tag_id=31

SELECT * FROM product_tag_product_template_rel WHERE product_tag_id IN (32)

DELETE FROM product_tag WHERE id = 31