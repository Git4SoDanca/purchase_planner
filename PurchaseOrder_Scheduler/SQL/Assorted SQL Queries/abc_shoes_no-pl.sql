
SELECT 
  product_product.name_template, 
  sodanca_product_sold_12mon.product_id,
  sodanca_product_sold_12mon.name, 
  sodanca_product_sold_12mon.total_sold, 
  product_category.name,
  product_category.parent_id,

    percent_rank() OVER (ORDER BY sodanca_product_sold_12mon.total_sold DESC) AS rank_pct,
        CASE
            WHEN percent_rank() OVER (ORDER BY sodanca_product_sold_12mon.total_sold DESC) <= 0.15::double precision THEN 'A'::text
            WHEN percent_rank() OVER (ORDER BY sodanca_product_sold_12mon.total_sold DESC) > 0.15::double precision AND percent_rank() OVER (ORDER BY sodanca_product_sold_12mon.total_sold DESC) <= 0.5::double precision THEN 'B'::text
            WHEN percent_rank() OVER (ORDER BY sodanca_product_sold_12mon.total_sold DESC) > 0.5::double precision AND percent_rank() OVER (ORDER BY sodanca_product_sold_12mon.total_sold DESC) <= 0.8::double precision THEN 'C'::text
            WHEN percent_rank() OVER (ORDER BY sodanca_product_sold_12mon.total_sold DESC) > 0.8::double precision THEN 'D'::text
            ELSE NULL::text
        END AS rank_letter
  
  
FROM 
  public.sodanca_product_sold_12mon, 
  public.product_product, 
  public.product_template, 
  public.product_category
WHERE 
  sodanca_product_sold_12mon.product_id = product_product.id AND
  product_product.product_tmpl_id = product_template.id AND
  product_template.categ_id = product_category.id AND
  (product_template.categ_id = 8 or product_category.parent_id=8) AND
  product_template.exclusive_customer isNull
GROUP BY 
  product_product.name_template, 
  sodanca_product_sold_12mon.product_id,
  sodanca_product_sold_12mon.name, 
  sodanca_product_sold_12mon.total_sold, 
  product_category.name,
  product_category.parent_id

ORDER BY ( sodanca_product_sold_12mon.total_sold) DESC;


SELECT 
  product_product.name_template, 
  product_product.name, 
  sodanca_product_sold_12mon.product_id, 
  product_template.categ_id, 
  product_category.parent_id, 
  sodanca_product_sold_12mon.total_sold, 
  product_template.list_price, 
  product_template.standard_price,
  (product_template.list_price*sodanca_product_sold_12mon.total_sold)- (product_template.standard_price*sodanca_product_sold_12mon.total_sold) AS gross_profit,
  CASE
    WHEN percent_rank() OVER (ORDER BY (product_template.list_price*sodanca_product_sold_12mon.total_sold)- (product_template.standard_price*sodanca_product_sold_12mon.total_sold) DESC) <= 0.15::double precision THEN 'A'::text
    WHEN percent_rank() OVER (ORDER BY (product_template.list_price*sodanca_product_sold_12mon.total_sold)- (product_template.standard_price*sodanca_product_sold_12mon.total_sold) DESC) > 0.15::double precision AND percent_rank() OVER (ORDER BY (product_template.list_price*sodanca_product_sold_12mon.total_sold)- (product_template.standard_price*sodanca_product_sold_12mon.total_sold) DESC) <= 0.5::double precision THEN 'B'::text
    WHEN percent_rank() OVER (ORDER BY (product_template.list_price*sodanca_product_sold_12mon.total_sold)- (product_template.standard_price*sodanca_product_sold_12mon.total_sold) DESC) > 0.5::double precision AND percent_rank() OVER (ORDER BY (product_template.list_price*sodanca_product_sold_12mon.total_sold)- (product_template.standard_price*sodanca_product_sold_12mon.total_sold) DESC) <= 0.8::double precision THEN 'C'::text
    WHEN percent_rank() OVER (ORDER BY (product_template.list_price*sodanca_product_sold_12mon.total_sold)- (product_template.standard_price*sodanca_product_sold_12mon.total_sold) DESC) > 0.8::double precision THEN 'D'::text
    ELSE NULL::text
  END AS rank_letter
FROM 
  public.sodanca_product_sold_12mon, 
  public.product_product, 
  public.product_template, 
  public.product_category
WHERE 
  sodanca_product_sold_12mon.product_id = product_product.id AND
  product_product.product_tmpl_id = product_template.id AND
  product_template.categ_id = product_category.id AND
  (product_template.categ_id = 8 or product_category.parent_id=8) AND
  product_template.exclusive_customer isNull
ORDER BY gross_profit DESC


