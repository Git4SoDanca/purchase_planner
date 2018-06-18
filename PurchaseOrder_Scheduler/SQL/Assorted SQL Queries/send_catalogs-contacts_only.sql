select res_partner.display_name, res_partner.street, res_partner.city, res_country_state.code, res_partner.zip, parent_partner.sales_rep   --, parent_id, user_id, 
from res_partner 
left join res_country_state ON res_partner.state_id = res_country_state.id
left join (select res_partner.id, res_partner.name, res_users.login as sales_rep from res_partner left join res_users on res_users.id = res_partner.user_id) AS parent_partner ON res_partner.parent_id = parent_partner.id
where res_partner.id in (select id from sodanca_mailing_list where cust_number is null order by state) order by sales_rep,zip, city
