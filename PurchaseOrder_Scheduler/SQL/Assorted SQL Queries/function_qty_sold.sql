-- FUNCTION: public.sd_qs(integer, date, date)

-- DROP FUNCTION public.sd_qs(integer, date, date);

CREATE OR REPLACE FUNCTION public.sd_qs(
	pid integer,
	start_date date,
	end_date date)
    RETURNS numeric
    LANGUAGE 'sql'

    COST 100
    VOLATILE 
AS $BODY$

SELECT 
	CASE
    	WHEN sum(stock_move.product_qty) != 0 THEN sum(stock_move.product_qty) ELSE 0 END AS on_order_total
FROM stock_move
WHERE 
	stock_move.location_dest_id = 9 
    AND stock_move.location_id = 12
    AND (stock_move.state::text = 'done'::character varying)
    AND date_expected >= $2 --start_date
    AND date_expected < $3 --end_date
    AND stock_move.product_id = $1
GROUP BY stock_move.product_id

$BODY$;

ALTER FUNCTION public.sd_qs(integer, date, date)
    OWNER TO sodanca;
