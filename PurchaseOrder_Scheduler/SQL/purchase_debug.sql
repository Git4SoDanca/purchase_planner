WITH const AS ( SELECT
	'2018-04-01'::date as oo_window,
	'2018-07-10'::date as today,
	'2018-08-31'::date as shipment_date,
	'2018-09-07'::date as ship_window,
	115389 as product_id
	)

SELECT 	sd_qoh(const.product_id) as on_hand,
		sd_qs_prev_yr(const.product_id,const.today,const.shipment_date) as sold_last_year_bef0831,
		sd_qs_prev_yr(const.product_id,const.shipment_date,const.ship_window) as sold_last_year_aft0831,
		sd_qcomm(const.product_id,const.today,const.ship_window) as commited,
		sd_qoo(const.product_id,const.oo_window,const.shipment_date) as on_order_bef_0831,
		sd_qoo(const.product_id,const.shipment_date,const.ship_window) as on_order_aft_0831,
		sd_expected_onhand(const.product_id,const.shipment_date) as expected_on_hand,
		sd_quantity_to_order(const.product_id,const.shipment_date,const.ship_window) as qty_to_order,
		COALESCE(sd_expected_onhand(const.product_id,const.shipment_date),0) as expected_on_hand_2,
		GREATEST(COALESCE(sd_qs_prev_yr(const.product_id,const.shipment_date,const.ship_window),0),COALESCE(sd_qcomm(const.product_id,const.shipment_date,const.ship_window),0)-sd_expected_onhand(const.product_id,const.shipment_date) AS qty_to_order2
		FROM const
