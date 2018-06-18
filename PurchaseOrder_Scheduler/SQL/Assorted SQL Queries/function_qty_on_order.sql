-- FUNCTION: public.sd_qoo(integer, date, date)

-- DROP FUNCTION public.sd_qoo(integer, date, date);

CREATE OR REPLACE FUNCTION public.sd_qoo(
	pid integer,
	start_date date,
	end_date date)
    RETURNS decimal
    LANGUAGE 'sql'

    COST 100
    VOLATILE
    ROWS 0
AS $BODY$

SELECT sum(stock_move.product_qty) AS on_order_total
FROM stock_move
WHERE
	stock_move.location_dest_id = 12
    AND stock_move.location_id = 8
    AND (stock_move.state::text = ANY (ARRAY['confirmed'::character varying, 'assigned'::character varying]::text[]))
    AND date_expected >= $2 --now()::date
    AND date_expected <= $3 --now()::date
    AND stock_move.product_id = $1
GROUP BY stock_move.product_id

$BODY$;

ALTER FUNCTION public.sd_qoo(integer, date, date)
    OWNER TO sodanca;
