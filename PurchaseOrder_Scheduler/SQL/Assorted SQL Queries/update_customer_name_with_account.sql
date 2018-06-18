UPDATE 
	res_partner 
SET 
	display_name=(' ['||cust_number||'] '||name) 
WHERE id IN (SELECT id FROM res_partner WHERE cust_number is not NULL AND LEFT(display_name,2)<>' [')
