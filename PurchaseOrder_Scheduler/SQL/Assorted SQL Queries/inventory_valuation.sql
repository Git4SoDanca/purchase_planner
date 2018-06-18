SELECT 
	public.product_product.name_template, public.product_product.name AS product_name, 
	public.product_template.standard_price, 
	sodanca_stock_on_hand.quantity_on_hand, 
	public.product_template.standard_price*sodanca_stock_on_hand.quantity_on_hand AS Amount
FROM 
	(public.product_product INNER JOIN public.product_template ON public.product_product.product_tmpl_id = public.product_template.id) 
	INNER JOIN public.sodanca_stock_on_hand ON public.product_product.id = sodanca_stock_on_hand.id
ORDER BY public.product_product.name;
