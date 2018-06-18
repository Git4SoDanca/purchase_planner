SELECT * FROM product_template WHERE name = 'D353'

SELECT * FROM product_product WHERE product_tmpl_id in (1591)

SELECT * FROM product_product WHERE product_tmpl_id in (2437,2438,2432)

SELECT * FROM product_template WHERE id in (2437,2438,2432)

DELETE FROM product_template WHERE id in (2437,2438,2432)