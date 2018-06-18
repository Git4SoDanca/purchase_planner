SELECT 
  res_partner.cust_number, 
  res_partner.name, 
  res_partner.city, 
  res_country_state.code as state, 
  res_partner.email, 
  res_partner.phone, 
  res_partner.fax
FROM 
  public.res_partner, 
  public.res_users, 
  public.res_country_state
WHERE 
  res_partner.user_id = res_users.id AND
  res_partner.state_id = res_country_state.id
  AND res_partner.customer = true
  AND res_users.login = 'sandy' 
  AND res_partner.cust_number IS NOT NULL
ORDER BY res_country_state.code, res_partner.city
