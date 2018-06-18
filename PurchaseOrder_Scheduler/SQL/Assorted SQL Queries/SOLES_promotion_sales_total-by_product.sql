SELECT 
  promotion, name_template, sum(price_subtotal), sum(quantity) --to_char(start_date, 'YYYY/MM') as period,
FROM (SELECT
  account_invoice.name, account_invoice.amount_total, account_period.name AS period_name, account_period.date_start as start_date, product_product.name_template, account_invoice_line.price_subtotal, account_invoice_line.quantity,
	  CASE WHEN (substring(account_invoice.name, 'HALLOWEEN') IS NOT NULL) THEN 'HALLOWEEN'
	  WHEN (substring(account_invoice.name, 'LABOR') IS NOT NULL) THEN 'LABOR'
	  WHEN (substring(account_invoice.name, 'SUMMER') IS NOT NULL) THEN 'SUMMER'
	  ELSE NULL
	  END AS promotion
FROM 
  public.account_invoice
  LEFT JOIN public.account_period ON public.account_period.id = account_invoice.period_id
  LEFT JOIN public.account_invoice_line ON public.account_invoice_line.invoice_id = public.account_invoice.id
  LEFT JOIN public.product_product ON product_product.id = account_invoice_line.product_id
  ) as invoices
WHERE promotion IS NOT NULL
GROUP BY promotion, name_template
ORDER BY promotion, name_template