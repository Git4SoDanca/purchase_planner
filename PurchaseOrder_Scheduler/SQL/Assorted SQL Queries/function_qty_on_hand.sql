CREATE FUNCTION sd_qoh(pid int) RETURNS decimal AS
$$ 
  SELECT
    sum(
        CASE
            WHEN (stock_move.location_dest_id IN ( SELECT stock_location.id
               FROM stock_location
              WHERE stock_location.usage::text = 'internal'::text)) AND stock_move.state::text = 'done'::text THEN stock_move.product_qty
            ELSE 0.0
        END) - sum(
        CASE
            WHEN (stock_move.location_id IN ( SELECT stock_location.id
               FROM stock_location
              WHERE stock_location.usage::text = 'internal'::text)) AND stock_move.state::text = 'done'::text THEN stock_move.product_qty
            ELSE 0.0
        END) AS quantity_on_hand
   FROM stock_move
   WHERE stock_move.product_id = $1
  GROUP BY stock_move.product_id
$$ LANGUAGE SQL;

  