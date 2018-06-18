-- FUNCTION: public.sd_expected_onhand(integer, date)
 -- DROP FUNCTION public.sd_expected_onhand(integer, date);

CREATE OR REPLACE FUNCTION public.sd_expected_onhand( pid integer, start_date date) RETURNS numeric
LANGUAGE 'sql'
COST 100
VOLATILE AS $BODY$
SELECT (sd_qoh($1)+COALESCE(sd_qoo($1,(now()-'6 months'::interval)::date,$2),0)-COALESCE(GREATEST(sd_qs($1,now()::date,$2),sd_qcomm($1,(now()-'6 months'::interval)::date,$2)),0));


$BODY$;


ALTER FUNCTION public.sd_expected_onhand(integer, date) OWNER TO sodanca;
