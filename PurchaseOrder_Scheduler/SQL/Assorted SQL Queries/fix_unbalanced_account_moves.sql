DO
$$

DECLARE mr RECORD;
DECLARE ml RECORD;

BEGIN

  
  FOR mr IN 
	SELECT credits.id as cred_id, credits.name as cred_name, debits.id as deb_id, debits.name as deb_name, credits.move_id, account_move.name, debits.amount as deb_amount, credits.amount as cred_amount
  FROM
	account_move
  LEFT JOIN (SELECT id, move_id, credit as amount, journal_id, name FROM public.account_move_line WHERE credit <> 0 AND create_date >= '2016-01-01') credits
	ON credits.move_id=account_move.id
  LEFT JOIN(SELECT id, move_id, debit as amount, journal_id, name FROM public.account_move_line WHERE debit <> 0 AND create_date >= '2016-01-01') debits
	ON credits.move_id = debits.move_id
  WHERE credits.amount <> debits.amount 
	AND credits.journal_id = 9
  ORDER BY move_id LOOP

	FOR ml IN SELECT * FROM account_move_line WHERE move_id = mr.move_id AND account_id=165 LOOP 	--Copying debit to credit
		--RAISE NOTICE 'UPDATE account_move_line SET credit= % WHERE id = %',ml.debit,mr.cred_id;		--
		UPDATE account_move_line SET credit= ml.debit WHERE id = mr.cred_id;
	   
		--FOR ml IN SELECT * FROM account_move_line WHERE move_id = mr.move_id AND account_id=245 LOOP 	--Copying credit amount to debit
		--RAISE NOTICE 'UPDATE account_move_line SET debit= % WHERE id = %',ml.credit,mr.deb_id;	--

		--UPDATE account_move_line SET debit= ml.credit WHERE id = mr.deb_id;
		
		--RAISE NOTICE 'Move Name % Id % Credit % Debit %',mr.name,ml.id,ml.credit, ml.debit; 

		
	END LOOP;

  END LOOP;
END
$$