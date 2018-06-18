SELECT * FROM account_authnet_cim 
LEFT JOIN res_partner ON account_authnet_cim.partner_id = res_partner.id
WHERE res_partner.cust_number = '4757'

UPDATE account_authnet_cim SET name = 'PNR Enterprises' WHERE id = 244