SELECT 
  promotion, to_char(start_date, 'YYYY/MM') as period, sum(amount_total)
FROM
(SELECT 
  account_invoice.name, account_invoice.amount_total, account_period.name AS period_name, account_period.date_start as start_date,
  CASE WHEN (substring(account_invoice.name, 'HALLOWEEN') IS NOT NULL) THEN 'HALLOWEEN'
  WHEN (substring(account_invoice.name, 'LABOR') IS NOT NULL) THEN 'LABOR'
  WHEN (substring(account_invoice.name, 'SUMMER') IS NOT NULL) THEN 'SUMMER'
  ELSE NULL
  END AS promotion
FROM 
  public.account_invoice
LEFT JOIN public.account_period ON public.account_period.id = account_invoice.period_id) as invoices
WHERE promotion IS NOT NULL
GROUP BY promotion, period
ORDER BY promotion, period