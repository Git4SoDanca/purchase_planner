SELECT 
  res_partner.cust_number, 	
  res_partner.name, 
  res_partner.city, 
  res_country_state.code, 
  reward_program.level, 
  SUM(CASE WHEN account_invoice.type='out_invoice' AND account_invoice.state <> 'cancel' THEN account_invoice.amount_total else  0.00 end) - SUM(CASE WHEN account_invoice.type='out_refund' AND account_invoice.state <> 'cancel' THEN account_invoice.amount_total ELSE 0.00 END) AS YTD_TOTAL
FROM 
  public.res_partner, 
  public.res_country_state, 
  public.reward_program, 
  public.account_invoice
WHERE 
  res_partner.reward_program_id = reward_program.id AND
  res_country_state.id = res_partner.state_id AND
  account_invoice.partner_id = res_partner.id AND
  res_partner.customer=true
  
  
GROUP BY 
  res_partner.cust_number,
  res_partner.name,res_partner.city, 
  res_country_state.code, 
  reward_program.level
ORDER BY
  YTD_TOTAL DESC;
