DROP VIEW public.sodanca_send_catalogs;

CREATE OR REPLACE VIEW public.sodanca_send_catalogs AS 

SELECT res_partner.cust_number,
    res_partner.name,
    res_partner.street,
    res_partner.street2,
    res_partner.street3,
    res_partner.city,
    res_country_state.code AS state,
    res_partner.zip,
    res_partner.user_id,
    reward_program.level,
    1.4 AS weight,
    'Ground' AS service,
    'Shipper' AS billto,
    'Package' AS package_type,
    'Classic_2017' AS cost_center
   FROM res_partner
     LEFT JOIN res_country_state ON res_partner.state_id = res_country_state.id
     LEFT JOIN reward_program ON res_partner.reward_program_id = reward_program.id
     JOIN ( SELECT res_partner_1.id,
            sum(account_invoice.amount_total) AS invoice_total
           FROM res_partner res_partner_1,
            account_invoice
          WHERE account_invoice.partner_id = res_partner_1.id 
          GROUP BY res_partner_1.id) invoice_total ON invoice_total.id = res_partner.id
  WHERE res_partner.send_catalogs = true AND LEFT(res_partner.street,1) NOT IN ('P','p')
  ORDER BY cust_number;

  ALTER TABLE public.sodanca_send_catalogs
  OWNER TO sodanca;
GRANT ALL ON TABLE public.sodanca_send_catalogs TO sodanca;
GRANT SELECT ON TABLE public.sodanca_send_catalogs TO reportuser