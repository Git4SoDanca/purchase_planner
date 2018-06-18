-- FUNCTION: public.sd_qcomm(integer, date)

-- DROP FUNCTION public.sd_qcomm(integer, date);

CREATE OR REPLACE FUNCTION public.sd_qcomm(
	pid integer,
    start_date date,
	end_date date)
    RETURNS numeric
    LANGUAGE 'sql'

    COST 100
    VOLATILE 
AS $BODY$
 
SELECT sum(stock_move.product_qty) AS product_committed_total
FROM stock_move
WHERE 
	stock_move.location_dest_id = 9 
    AND stock_move.location_id = 12 
    AND (stock_move.state::text = ANY (ARRAY['confirmed'::character varying, 'assigned'::character varying]::text[])) 
    AND date_expected >= $2
    AND date_expected < $3
    AND stock_move.product_id = $1
GROUP BY stock_move.product_id

$BODY$;

ALTER FUNCTION public.sd_qcomm(integer, date)
    OWNER TO sodanca;
