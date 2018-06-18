DO $$

DECLARE 
	smove RECORD;
    invoice RECORD;
	invoice_qty_total DECIMAL;
BEGIN
	RAISE NOTICE 'Running';
    FOR smove IN SELECT origin, SUM(product_qty) as total FROM stock_move WHERE create_date > '2017-01-01 00:00:00' AND LEFT(origin,2) = 'SO' AND state = 'done' GROUP BY origin LIMIT 500 LOOP 
    	--RAISE NOTICE 'Stock move -- Line: % Origin: %', quote_ident(smove.origin), smove.total;
        invoice_qty_total = 0;
    	FOR invoice IN SELECT right(origin,10) as so_origin, left(origin,10) as delivery, SUM(quantity) as total FROM account_invoice_line WHERE RIGHT(origin,10) = smove.origin AND left(name,4) not in ('[SHI','[RSF','[DIS','[DSF', 'Ship') GROUP BY so_origin, delivery LOOP
        	invoice_qty_total = invoice_qty_total + invoice.total;
    		--RAISE NOTICE 'Invoice -- Origin: %, Sum: %', quote_ident(invoice.so_origin), invoice.total;
        END LOOP;
        --RAISE NOTICE 'Invoice Total: %', invoice_qty_total;
        IF invoice_qty_total < smove.total THEN
        	RAISE NOTICE 'Mismatch -- Delivery: %  Invoice: %  Invoice Total: %  Stock Move Total: %',quote_ident(invoice.delivery), quote_ident(invoice.so_origin), invoice_qty_total, smove.total;
            --SELECT * FROM quote_ident(smove.origin) AS Stock_move_origin, quote_ident(invoice.so_origin) as Invoice_origin, invoice_qty_total as invoice_total, smove.total as stock_move_total;
        END IF;
    END LOOP;
    
END;


$$ LANGUAGE plpgsql;
