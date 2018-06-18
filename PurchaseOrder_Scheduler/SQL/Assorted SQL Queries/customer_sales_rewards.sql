--Star rewards report
SELECT 
	CASE
		WHEN res_partner.parent_id IS NULL THEN res_partner.id
		ELSE res_partner.parent_id 
	END as grouped_partner_id,
	res_partner.cust_number, 
	res_partner.name, 
	res_partner.reward_segment AS level_2016, 
	res_partner.city,  
	res_country_state.code, 
	res_partner.zip, 
	res_country.name as country, 
	res_partner.user_id, 
	totals_2016.invoice_total as total_sales_2016,
	totals_2015.invoice_total as total_sales_2015,
	CASE 
		WHEN totals_2015.invoice_total = 0 THEN 1.00
		ELSE (totals_2016.invoice_total/totals_2015.invoice_total)-1 
	END as net_sales_growth,
	CASE 
		WHEN totals_2016.invoice_total < 6000 THEN '1 Star'
		WHEN totals_2016.invoice_total >= 6000 AND totals_2016.invoice_total < 10000 THEN '2 Star'
		WHEN totals_2016.invoice_total >= 10000 AND totals_2016.invoice_total < 20000 THEN '3 Star'
		WHEN totals_2016.invoice_total >= 20000 AND totals_2016.invoice_total < 30000 THEN '4 Star'
		WHEN totals_2016.invoice_total >= 30000 AND totals_2016.invoice_total < 50000 THEN '5 Star'
		WHEN totals_2016.invoice_total >= 50000 AND totals_2016.invoice_total < 100000 THEN 'Superstar'
		WHEN totals_2016.invoice_total >= 100000 AND totals_2016.invoice_total < 200000 THEN 'Platinum'
		WHEN totals_2016.invoice_total >= 200000 THEN 'Diamond' END as level_2017,
	CASE 
		WHEN totals_2016.invoice_total >= 5400 AND totals_2016.invoice_total < 10000 THEN '2 Star'
		WHEN totals_2016.invoice_total >= 9900 AND totals_2016.invoice_total < 10000 THEN '3 Star'
		WHEN totals_2016.invoice_total >= 18000 AND totals_2016.invoice_total < 20000 THEN '4 Star'
		WHEN totals_2016.invoice_total >= 27000 AND totals_2016.invoice_total < 30000 THEN '5 Star'
		WHEN totals_2016.invoice_total >= 45000 AND totals_2016.invoice_total < 50000 THEN 'Superstar'
		WHEN totals_2016.invoice_total >= 90000 AND totals_2016.invoice_total < 100000 THEN 'Platinum'
		WHEN totals_2016.invoice_total >= 180000 AND totals_2016.invoice_total < 200000 THEN 'Diamond'
		END as possible_level_2017,
	res_users.login
FROM res_partner 
LEFT JOIN 
	res_country_state ON res_country_state.id = res_partner.state_id
LEFT JOIN 
	res_country ON res_country.id = res_country_state.country_id
LEFT JOIN
	res_users ON res_users.id = res_partner.user_id
LEFT JOIN
	(SELECT 
		CASE
			WHEN (res_partner.parent_id IS NULL) THEN res_partner.id
			ELSE (res_partner.parent_id) 
		END as grouped_partner_id,
		SUM(CASE 
			WHEN account_invoice.type = 'out_invoice' THEN (account_invoice.amount_total) 
			WHEN account_invoice.type = 'out_refund' THEN (-1*(account_invoice.amount_total))
			ELSE 9999999999 
		END) as invoice_total
	FROM 
		public.account_invoice
	LEFT JOIN account_period ON account_period.id = account_invoice.period_id
	LEFT JOIN res_partner ON res_partner.id = account_invoice.partner_id
	WHERE RIGHT(account_period.name,4) = '2016'
	GROUP BY
		grouped_partner_id
	ORDER BY grouped_partner_id) as totals_2016 ON res_partner.id = totals_2016.grouped_partner_id
LEFT JOIN
	(SELECT 
		CASE
			WHEN (res_partner.parent_id IS NULL) THEN res_partner.id
			ELSE (res_partner.parent_id) 
		END as grouped_partner_id,
		SUM(CASE 
			WHEN account_invoice.type = 'out_invoice' THEN (account_invoice.amount_total) 
			WHEN account_invoice.type = 'out_refund' THEN (-1*(account_invoice.amount_total))
			ELSE 9999999999
		END) as invoice_total
	FROM 
		public.account_invoice
	LEFT JOIN account_period ON account_period.id = account_invoice.period_id
	LEFT JOIN res_partner ON res_partner.id = account_invoice.partner_id
	WHERE RIGHT(account_period.name,4) = '2015'
	GROUP BY
		grouped_partner_id
	ORDER BY grouped_partner_id) as totals_2015 ON res_partner.id = totals_2015.grouped_partner_id
WHERE res_partner.customer = true AND res_partner.active = true AND res_partner.cust_number is not null AND (totals_2016.invoice_total != 0 OR totals_2015.invoice_total != 0)
ORDER BY totals_2016.invoice_total DESC
