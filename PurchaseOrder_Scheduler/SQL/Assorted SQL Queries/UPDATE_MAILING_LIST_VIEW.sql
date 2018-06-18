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
    12 AS weight, -- lbs or oz depending on service never add units
    'Expedited Mail Innovations'::text AS service, -- usually 'Expedited Mail Innovations' if < 1lb or 'Ground' if over 1lb
    'Shipper'::text AS billto, --leave as is
    'Irregulars'::text AS package_type, -- depends, follow guide - For ground use 'Package', for Expedited Mail Innovations use 'Irregulars' if not bendable or uneven surface, if only paper (no bumps and bendable) use 'Standard Flats'
    'Classic_2018'::text AS cost_center -- change to inform what is being shipped
   FROM res_partner
     LEFT JOIN res_country_state ON res_partner.state_id = res_country_state.id
     LEFT JOIN reward_program ON res_partner.reward_program_id = reward_program.id
  WHERE res_partner.send_catalogs = true AND res_country_state.country_id = 235; -- Customers/Partners with send_catalogs flag set to True and only US (country_id = 235)

ALTER TABLE public.sodanca_mailing_list
    OWNER TO sodanca;

