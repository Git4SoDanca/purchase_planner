DROP TABLE public.sodanca_store_locator;

CREATE TABLE public.sodanca_store_locator AS 
select res_partner.id, res_partner.name, res_partner.street, res_partner.street2, res_partner.street3, res_partner.city, res_country_state.code as state, res_partner.zip, res_country.name as country, res_partner.phone, NULL::DOUBLE PRECISION as lat, NULL::DOUBLE PRECISION as lon
from res_partner
left join res_country_state on res_country_state.id = res_partner.state_id
left join res_country on res_country.id = res_country_state.country_id
where res_partner.store_locator = true;


ALTER TABLE public.sodanca_store_locator OWNER TO sodanca;
