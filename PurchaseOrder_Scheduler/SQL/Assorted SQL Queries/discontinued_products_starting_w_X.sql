UPDATE product_product SET discontinued_product = true WHERE id IN (
SELECT id FROM product_product WHERE discontinued_product = false and LEFT(name,1) = 'X'
)
