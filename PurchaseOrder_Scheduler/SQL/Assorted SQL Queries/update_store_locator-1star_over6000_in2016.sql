UPDATE res_partner
SET store_locator = true 
WHERE id IN
(SELECT id FROM 
(SELECT 
  res_partner.id, 
  res_partner.cust_number, 
  res_partner.reward_segment,
  res_partner.name, 
  SUM(account_invoice.amount_total) AS Total_2016,
  account_fiscalyear.code
FROM 
  public.res_partner, 
  public.account_invoice, 
  public.account_period, 
  public.account_fiscalyear
WHERE 
  account_invoice.partner_id = res_partner.id AND
  account_invoice.period_id = account_period.id AND
  account_period.fiscalyear_id = account_fiscalyear.id AND 
  account_fiscalyear.code = '2016' AND 
  res_partner.reward_segment = '1 Star'
GROUP BY res_partner.id,res_partner.cust_number, res_partner.reward_segment,
  res_partner.name, account_fiscalyear.code
  ) One_star
WHERE Total_2016 > 5999.99)