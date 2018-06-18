SELECT product_product.name_template, product_product.name, pq.total FROM
	(select product_id , SUM(quantity) as total
	from account_invoice_line
	where 
		partner_id IN (
			select id from res_partner where cust_number in ('3664','5445') 
		) 
		and product_id in (
			select id from product_product where name_template in (
			'D4670','D3670','D2828','D374','D7500','D6500','D293','D193','D401','D715','D256','D156','D7600','D6600','D722','D723','D2518','D6731','D257','D157','D946','D947'
			'L534','L535','L543','L545','L573','L575','L948','L1031','L1059','L1123','RDE1551','RDE1559','RDE1598','RDE1608','RDE1613','D151','D154','D1561','D225','D251','D2916'
			)
	)
	GROUP BY product_id
	) AS pq
LEFT JOIN product_product ON product_product.id = pq.product_id ORDER BY product_product.name_template, product_product.name