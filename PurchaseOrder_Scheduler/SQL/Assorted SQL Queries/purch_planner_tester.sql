with const AS (
SELECT '2018-07-05'::date as start_date, '2018-07-12'::date as end_date
)
SELECT id,name, 
	sd_qoh(id) AS on_hand, const.start_date, const.end_date,
    sd_qoo(id,(now()-'6 months'::interval)::date,const.start_date) as qty_onorder, 
    sd_qs(id,now()::date,const.start_date) as qty_sold,
    sd_qcomm(id,(now()-'6 months'::interval)::date,const.start_date) as qty_committed,
    GREATEST(sd_qs(id,now()::date,const.start_date),sd_qcomm(id,(now()-'6 months'::interval)::date,const.start_date)) as hist_vs_comm,
--     (sd_qoh(id)+COALESCE(sd_qoo(id,(now()-'6 months'::interval)::date,const.start_date),0)-COALESCE(GREATEST(sd_qs(id,now()::date,const.start_date),sd_qcomm(id,(now()-'6 months'::interval)::date,const.start_date)),0)) as qty_exp_on_hand
    sd_expected_onhand(id,const.start_date) as qty_exp_on_hand,
    sd_quantity_to_order(id,const.start_date,const.end_date)
    
--     GREATEST(sd_qs(id,'2018-01-18','2018-01-25'),sd_qcomm(id,'2018-01-18'))+COALESCE(sd_qoo(id,'2018-01-18','2018-01-25'),0)-COALESCE(sd_expected_onhand(id,'2018-01-18'),0) AS qty_to_order 
    from product_product, const
    --where product_product.id = 16012
-- SELECT (sd_qoh($1) + sd_qoo($1,(now()-'6 months'::interval)::date,$2) -GREATEST(sd_qs($1, now()::date, $2),sd_qcomm($1,$2)))



-- COALESCE(GREATEST(sd_qs(id,'2018-01-01','2018-02-15'),sd_qcomm(id,'2018-01-01'))+sd_qoo(id,'2018-01-01','2018-02-15')-sd_expected_onhand(id,'2018-01-01'),0) AS qty_to_order

-- SELECT sd_quantity_to_order(178630,'2018-07-19' ,'2018-07-26')
-- SELECT sd_quantity_to_order(178630,'2018-04-19' ,'2018-07-26')

-- SELECT (COALESCE(GREATEST(sd_qs(178630, now()::date, '2018-04-19'),sd_qcomm(178630,'2018-04-19')),0)- COALESCE(GREATEST(sd_expected_onhand(178630,'2018-04-19')),0)+ COALESCE(sd_qoo(178630,'2018-04-19','2018-04-26'),0))

-- SELECT sd_qs(178630, '2018-04-19','2018-04-26')
-- SELECT sd_qcomm(178630,'2018-04-19','2018-04-26')

-- SELECT COALESCE(GREATEST(sd_expected_onhand(178630,'2018-04-19')),0)
-- SELECT COALESCE(sd_qoo(178630,'2018-04-19','2018-04-26'),0)
