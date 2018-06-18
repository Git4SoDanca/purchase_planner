-- View: public.sodanca_mailing_list

DROP VIEW public.sodanca_mailing_list;

CREATE OR REPLACE VIEW public.sodanca_mailing_list AS
 SELECT res_partner.id,
    res_partner.cust_number,
    res_partner.name,
    res_partner.street,
    res_partner.street2,
    res_partner.street3,
    res_partner.city,
    res_country_state.code AS state,
    res_partner.zip,
    res_partner.user_id,
    reward_program.level,
    2.4 AS weight, -- lbs or oz ( depends on service )
    -- 'Expedited Mail Innovations'::text AS service,
    'Ground'::text AS service,
    'Shipper'::text AS billto,
    -- 'Irregulars'::text AS package_type, 
    'Package'::text AS package_type,
    '2018ClassFash'::text AS cost_center
   FROM res_partner
     LEFT JOIN res_country_state ON res_partner.state_id = res_country_state.id
     LEFT JOIN reward_program ON res_partner.reward_program_id = reward_program.id
  WHERE res_partner.send_catalogs = true AND res_country_state.country_id = 235 AND res_partner.active = true AND res_partner.maincategory NOT IN (13,15,35,1,2,25,4)-- not inactive, closed, employee, private label, showroom, supplier
  ORDER BY res_partner.zip DESC;
ALTER TABLE public.sodanca_mailing_list
    OWNER TO sodanca;

GRANT SELECT ON TABLE public.sodanca_mailing_list TO reportuser;
GRANT SELECT ON TABLE public.sodanca_mailing_list TO sodanca;
GRANT ALL ON TABLE public.sodanca_mailing_list TO postgres;
