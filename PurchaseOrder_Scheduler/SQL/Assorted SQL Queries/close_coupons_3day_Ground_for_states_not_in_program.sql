UPDATE coupons SET state = 'close' WHERE id IN (
SELECT id 
FROM coupons 
WHERE campaigns = 12 AND partner_id 
	NOT IN (
		SELECT id FROM res_partner WHERE state_id IN (
			SELECT id FROM res_country_state WHERE code IN ('AZ','NV','CA','OR','CO','WA','NM','NY')
		)
	)
)

