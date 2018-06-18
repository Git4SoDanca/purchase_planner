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

SELECT id,name,
	sd_quantity_to_order($1,$2,$3) AS to_order,
    sd_qs($1,$2,$3)as qty_sold,
    sd_qcomm($1,$2,$3) as qty_committed,
    GREATEST(sd_qs($1,$2,$3),sd_qcomm($1,$2)) as hist_vs_comm,
    sd_expected_onhand($1,$2) as qty_exp_on_hand ,
    sd_qoo($1,$2,$3) as qty_onorder,
    GREATEST(sd_qs($1,$2,$3),sd_qcomm($1,$2))+COALESCE(sd_qoo($1,$2,$3),0)-COALESCE(sd_expected_onhand($1,$2),0) AS qty_to_order from product_product

$BODY$;

ALTER FUNCTION public.sd_quantity_to_order(integer, date, date)
    OWNER TO sodanca;
