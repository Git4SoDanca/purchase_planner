SELECT * FROM res_partner WHERE reward_segment = '1 Star' and maincategory != 13
SELECT * FROM res_partner WHERE reward_segment = '2 Star' and maincategory != 13
SELECT * FROM res_partner WHERE reward_segment = '3 Star' and maincategory != 13
SELECT * FROM res_partner WHERE reward_segment = '4 Star' and maincategory != 13
SELECT * FROM res_partner WHERE reward_segment = '5 Star' and maincategory != 13
SELECT * FROM res_partner WHERE reward_segment = 'Superstar Gold' and maincategory != 13
SELECT * FROM res_partner WHERE reward_segment = 'Superstar Platinum' and maincategory != 13
SELECT * FROM res_partner WHERE reward_segment = 'Superstar Diamond' and maincategory != 13
SELECT * FROM res_partner WHERE maincategory = 23

UPDATE res_partner SET maincategory = 16 WHERE reward_segment = '1 Star' and maincategory != 13;
UPDATE res_partner SET maincategory = 23 WHERE reward_segment = '2 Star' and maincategory != 13;
UPDATE res_partner SET maincategory = 19 WHERE reward_segment = '3 Star' and maincategory != 13;
UPDATE res_partner SET maincategory = 21 WHERE reward_segment = '4 Star' and maincategory != 13;
UPDATE res_partner SET maincategory = 17 WHERE reward_segment = '5 Star' and maincategory != 13;
UPDATE res_partner SET maincategory = 24 WHERE reward_segment = 'Superstar Gold' and maincategory != 13;
UPDATE res_partner SET maincategory = 31 WHERE reward_segment = 'Superstar Platinum' and maincategory != 13;
UPDATE res_partner SET maincategory = 32 WHERE reward_segment = 'Superstar Diamond' and maincategory != 13;

SELECT * FROM res_partner_category WHERE parent_id is null ORDER BY name

UPDATE res_partner SET maincategory = 23 WHERE reward_segment = '2 Star' and maincategory != 13 and cust_number = '1918';