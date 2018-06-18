-- -----------------------------------------------------------------------------------------------------------------------------------------------
--  On Hand =
--     SUM of product quantities INTO internal location minus SUM of product quantities OUT OF internal location.
-- ---------------------------------------------------------------------------------------------------------------------------------------------------

	SELECT product_product.id, product_product.name, (
	SUM ( CASE WHEN stock_move.location_dest_id IN ( SELECT stock_location.id from stock_location WHERE usage = 'internal') AND stock_move.state = 'done' THEN stock_move.product_qty ELSE 0.0 END ) -
	SUM ( CASE WHEN stock_move.location_id      IN ( SELECT stock_location.id from stock_location WHERE usage = 'internal') AND stock_move.state = 'done' THEN stock_move.product_qty ELSE 0.0 END ) ) AS on_hand_qty
	FROM product_product LEFT JOIN stock_move ON (stock_move.product_id = product_product.id)
	GROUP BY product_product.name, product_product.id
	ORDER BY product_product.name, product_product.id

-- ---------------------------------------------------------------------------------------------------------------------------------------------------
--  Daily Orders = (for immediate shipping)
--    SUM of product quantities sold in current month and invoiced within 10 days of sale with status "done"
--    minus
--    SUM of product quantities sold in current month and invoiced within 10 days of sale with status "cancel".
-- --------------------------------------------------------------------------------------------------------------------------------------------------

	SELECT product_product.id, product_product.name, (
	SUM    ( CASE WHEN stock_move.location_dest_id IN (SELECT stock_location.id from stock_location WHERE usage = 'customer')
	AND    stock_move.origin IN (SELECT distinct origin from stock_picking WHERE invoice_state = 'invoiced' AND type='out' AND id = stock_move.picking_id)
	AND    stock_move.state = 'done'
	AND    date_trunc('month', stock_move.date) = date_trunc('month', current_date)
	AND    ( date_trunc('day', stock_move.date_expected) >= date_trunc('day', stock_move.date) )
	AND    ( date_trunc('day', stock_move.date_expected) - date_trunc('day', stock_move.date) <= interval '10 day') THEN stock_move.product_qty ELSE 0.0 END ) -
	SUM    ( CASE WHEN stock_move.location_dest_id IN (SELECT stock_location.id from stock_location WHERE usage = 'customer')
	AND    stock_move.origin IN (SELECT distinct origin from stock_picking WHERE invoice_state = 'invoiced' AND type='out' AND id = stock_move.picking_id)
	AND    stock_move.state = 'cancel'
	AND    date_trunc('month', stock_move.date) = date_trunc('month', current_date)
	AND    ( date_trunc('day', stock_move.date_expected) >= date_trunc('day', stock_move.date) )
	AND    ( date_trunc('day', stock_move.date_expected) - date_trunc('day', stock_move.date) <= interval '10 day') THEN stock_move.product_qty ELSE 0.0 END ) ) as daily_orders_qty
	FROM   product_product LEFT JOIN stock_move ON (stock_move.product_id = product_product.id)
	GROUP BY product_product.name, product_product.id
	ORDER BY product_product.name, product_product.id


-- ---------------------------------------------------------------------------------------------------------------------------------------------------
--  On Order =
--    SUM of product quantities with status "assigned" from stock location "supplier".
--    Quantities grouped by month for the next 4 months.
--    All quantities from orders with date smaller than current date are added to current month's quantity.
-- ---------------------------------------------------------------------------------------------------------------------------------------------------

	SELECT product_product.id, product_product.name,
	SUM ( CASE WHEN stock_move.location_id IN (SELECT stock_location.id from stock_location WHERE usage = 'supplier')
	AND stock_move.date_expected < (date_trunc('month', current_date) + interval '1 month')
	AND stock_move.state IN ('assigned') THEN stock_move.product_qty ELSE 0.0 END ) AS on_order_qty_1,
	SUM ( CASE WHEN stock_move.location_id IN (SELECT stock_location.id from stock_location WHERE usage = 'supplier')
	AND stock_move.date_expected >= (date_trunc('month', current_date) + interval '1 month') AND stock_move.date_expected < (date_trunc('month', current_date) + interval '2 month')
	AND stock_move.state IN ('assigned') THEN stock_move.product_qty ELSE 0.0 END ) AS on_order_qty_2,
	SUM ( CASE WHEN stock_move.location_id IN (SELECT stock_location.id from stock_location WHERE usage = 'supplier')
	AND stock_move.date_expected >= (date_trunc('month', current_date) + interval '2 month') AND stock_move.date_expected < (date_trunc('month', current_date) + interval '3 month')
	AND stock_move.state IN ('assigned') THEN stock_move.product_qty ELSE 0.0 END ) AS on_order_qty_3,
	SUM ( CASE WHEN stock_move.location_id IN (SELECT stock_location.id from stock_location WHERE usage = 'supplier')
	AND stock_move.date_expected >= (date_trunc('month', current_date) + interval '3 month') AND stock_move.date_expected < (date_trunc('month', current_date) + interval '4 month')
	AND stock_move.state IN ('assigned') THEN stock_move.product_qty ELSE 0.0 END ) AS on_order_qty_4
	FROM product_product LEFT JOIN stock_move ON (stock_move.product_id = product_product.id)
	GROUP BY product_product.name, product_product.id
	ORDER BY product_product.name, product_product.id


-- ---------------------------------------------------------------------------------------------------------------------------------------------------
--  Committed =
--    SUM of product quantities sold but not invoiced (open orders) with status <> "done" and status <> "cancel"
--    Quantities grouped by month for the next 4 months.
--    All quantities from orders with date within the past 3 months are added to current month's quantity.
-- ---------------------------------------------------------------------------------------------------------------------------------------------------

	SELECT product_product.id, product_product.name,
	SUM ( CASE WHEN stock_move.location_dest_id IN (SELECT stock_location.id from stock_location WHERE usage = 'customer')
	AND stock_move.state NOT IN ('done', 'cancel')
	AND stock_move.date_expected >= (date_trunc('month', current_date) - interval '3 month')
	AND stock_move.date_expected <  (date_trunc('month', current_date) + interval '1 month') THEN stock_move.product_qty ELSE 0.0 END ) AS committed_qty_1,
	SUM ( CASE WHEN stock_move.location_dest_id IN (SELECT stock_location.id from stock_location WHERE usage = 'customer')
	AND stock_move.state NOT IN ('done', 'cancel')
	AND stock_move.date_expected >= (date_trunc('month', current_date) + interval '1 month')
	AND stock_move.date_expected <  (date_trunc('month', current_date) + interval '2 month') THEN stock_move.product_qty ELSE 0.0 END ) AS committed_qty_2,
	SUM ( CASE WHEN stock_move.location_dest_id IN (SELECT stock_location.id from stock_location WHERE usage = 'customer')
	AND stock_move.state NOT IN ('done', 'cancel')
	AND stock_move.date_expected >= (date_trunc('month', current_date) + interval '2 month')
	AND stock_move.date_expected <  (date_trunc('month', current_date) + interval '3 month') THEN stock_move.product_qty ELSE 0.0 END ) AS committed_qty_3,
	SUM ( CASE WHEN stock_move.location_dest_id IN (SELECT stock_location.id from stock_location WHERE usage = 'customer')
	AND stock_move.state NOT IN ('done', 'cancel')
	AND stock_move.date_expected >= (date_trunc('month', current_date) + interval '3 month')
	AND stock_move.date_expected <  (date_trunc('month', current_date) + interval '4 month') THEN stock_move.product_qty ELSE 0.0 END ) AS committed_qty_4
	FROM product_product LEFT JOIN stock_move ON (stock_move.product_id = product_product.id)
	GROUP BY product_product.name, product_product.id
	ORDER BY product_product.name, product_product.id
