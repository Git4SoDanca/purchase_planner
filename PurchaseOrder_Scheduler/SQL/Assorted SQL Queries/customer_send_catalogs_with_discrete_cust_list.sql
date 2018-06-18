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
    1.125 AS weight,
    'Ground' AS service,
    'Shipper' AS billto,
    'Package' AS package_type,
    'Fashion1_2017' AS cost_center
   FROM res_partner
     LEFT JOIN res_country_state ON res_partner.state_id = res_country_state.id
     LEFT JOIN reward_program ON res_partner.reward_program_id = reward_program.id
     JOIN ( SELECT res_partner_1.id,
            sum(account_invoice.amount_total) AS invoice_total
           FROM res_partner res_partner_1,
            account_invoice
          WHERE account_invoice.partner_id = res_partner_1.id AND (res_partner_1.cust_number::text = ANY (ARRAY['2225'::character varying, '4757'::character varying, '5111'::character varying, '5379'::character varying, '5386'::character varying, '5391'::character varying, '2329'::character varying, '4435'::character varying, '2170'::character varying, '2173'::character varying, '2317'::character varying, '2344'::character varying, '3900'::character varying, '2309'::character varying, '5525'::character varying, '5526'::character varying, '5529'::character varying, '5530'::character varying, '5531'::character varying, '5533'::character varying, '5534'::character varying, '5535'::character varying, '5536'::character varying, '5539'::character varying, '5540'::character varying, '5541'::character varying, '5543'::character varying, '5544'::character varying, '5545'::character varying, '5546'::character varying, '5547'::character varying, '5548'::character varying, '5549'::character varying, '5550'::character varying, '5551'::character varying, '5554'::character varying, '5557'::character varying, '5562'::character varying, '5563'::character varying, '5565'::character varying, '5567'::character varying, '5571'::character varying, '5572'::character varying, '5576'::character varying, '5578'::character varying, '5580'::character varying, '5581'::character varying, '5582'::character varying, '5583'::character varying, '5585'::character varying, '5586'::character varying, '5587'::character varying, '5589'::character varying, '5590'::character varying, '5592'::character varying, '5595'::character varying, '5596'::character varying, '5597'::character varying]::text[]))
          GROUP BY res_partner_1.id) invoice_total ON invoice_total.id = res_partner.id
  WHERE res_partner.send_catalogs = true
  ORDER BY res_partner.cust_number;

ALTER TABLE public.sodanca_send_catalogs
  OWNER TO sodanca;
GRANT ALL ON TABLE public.sodanca_send_catalogs TO sodanca;
GRANT SELECT ON TABLE public.sodanca_send_catalogs TO reportuser;