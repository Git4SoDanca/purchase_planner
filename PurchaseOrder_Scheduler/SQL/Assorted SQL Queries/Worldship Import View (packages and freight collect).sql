 SELECT stock_picking.name AS out_number,
    sale_order.name AS so_number_number,
    CASE WHEN sale_order.customer_payment_method =20 THEN 1 
    ELSE 0
    END AS COD_flag,
    res_partner.cust_number,
    res_partner.name,
    res_partner.street,
    res_partner.street2,
    res_partner.street3,
    res_partner.city,
    res_country_state.code AS state,
    res_country.code AS country_code,
    res_country.name AS country,
    res_partner.phone,
    stock_picking.number_of_packages,
    stock_picking.collect_charge,
    shipping_codes.description AS ship_via,
    stock_picking.saturday_delivery,
    stock_picking.shipping_account,
    res_partner.email AS out_email,
    sale_order.partner_id AS so_partner,
    sale_order.client_order_ref AS so_customer_po,
    true AS qvn_option,
    res_partner.zip,
    collect_charges.account_no as collect_account
   FROM stock_picking
     LEFT JOIN sale_order ON stock_picking.origin::text = sale_order.name::text
     LEFT JOIN res_partner ON stock_picking.partner_id = res_partner.id
     LEFT JOIN res_country ON res_partner.country_id = res_country.id
     LEFT JOIN res_country_state ON res_partner.state_id = res_country_state.id
     LEFT JOIN shipping_codes ON stock_picking.service_type = shipping_codes.id
     LEFT JOIN collect_charges ON stock_picking.shipping_account = collect_charges.id
  WHERE (stock_picking.state::text = 'confirmed'::text OR stock_picking.state::text = 'assigned'::text) AND stock_picking.type= 'out' --LEFT(stock_picking.name,3)='OUT'
  ORDER BY stock_picking.name DESC;
  
  worldship_pickingout_view
