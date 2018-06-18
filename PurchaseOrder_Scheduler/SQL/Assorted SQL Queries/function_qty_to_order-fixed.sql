-- FUNCTION: public.sd_quantity_to_order(integer, date, date)

-- DROP FUNCTION public.sd_quantity_to_order(integer, date, date);

CREATE OR REPLACE FUNCTION public.sd_quantity_to_order(
	pid integer,
	start_date date,
	end_date date)
    RETURNS numeric
    LANGUAGE 'sql'

    COST 100
    VOLATILE 
AS $BODY$

SELECT GREATEST(sd_qhs($1,$2,$3),sd_qcomm($1,$2,$3))-COALESCE(sd_qoo($1,$2,$3),0)-COALESCE(sd_expected_onhand($1,$2),0) AS qty_to_order from product_product

$BODY$;

ALTER FUNCTION public.sd_quantity_to_order(integer, date, date)
    OWNER TO sodanca;
