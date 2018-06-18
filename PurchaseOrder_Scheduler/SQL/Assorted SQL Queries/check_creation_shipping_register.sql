SELECT 
  public.stock_picking.name, public.shipping_shippingregister.create_uid as register_cuid,public.shipping_shippingregister.create_date as register_cdate, public.shipping_shippingregister_package.*
  FROM 
  public.shipping_shippingregister, 
  public.shipping_shippingregister_package, 
  public.stock_picking
WHERE 
  shipping_shippingregister.picking_id = stock_picking.id AND
  shipping_shippingregister_package.shipping_register_rel = shipping_shippingregister.id
  AND public.stock_picking.name = 'OUT10064271'
 LIMIT 50;
