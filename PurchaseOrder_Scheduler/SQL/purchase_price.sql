SELECT
	pricelist_partnerinfo.price,
	product_supplierinfo.product_id,
	pricelist_partnerinfo.suppinfo_id,
	product_supplierinfo.qty,
	product_template.name,
	product_supplierinfo.min_qty,
	pricelist_partnerinfo.id,
	pricelist_partnerinfo.min_quantity,
	product_supplierinfo.name AS SNAME,
	res_partner.name AS PNAME
FROM
	public.pricelist_partnerinfo,
	public.product_supplierinfo,
	public.product_template,
	public.res_partner
WHERE
	pricelist_partnerinfo.suppinfo_id = product_supplierinfo.id AND
	product_supplierinfo.product_id = product_template.id AND
	product_supplierinfo.name = res_partner.id
ORDER BY
	product_template.name
