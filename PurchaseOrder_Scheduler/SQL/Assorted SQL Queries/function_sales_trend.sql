CREATE FUNCTION sd_sales_trend(pid int) RETURNS decimal AS
$$
SELECT round(sd_qs($1,(now()-'6 months'::interval)::date, now()::date)/sd_qs($1,(now()- '18 months'::interval)::date,(now()- '12 months'::interval)::date)*100,2) as growth;
$$ LANGUAGE SQL;
