SELECT credits.id as cred_id, credits.name as cred_name, debits.id as deb_id, debits.name as deb_name, credits.move_id, account_move.name,
 --CASE WHEN credits.amount > debits.amount THEN credits.amount
 --ELSE debits.amount
 --END as amount_greater,
 --CASE WHEN credits.amount < debits.amount THEN credits.amount
 --ELSE debits.amount
 --END as amount_smaller,
 debits.amount as deb_amount, credits.amount as cred_amount
 --credits.amount-debits.amount as difference
 FROM
(SELECT id, move_id, credit as amount, journal_id, name FROM public.account_move_line WHERE credit <> 0 AND create_date >= '2016-01-01') credits
LEFT JOIN
(SELECT id, move_id, debit as amount, journal_id, name FROM public.account_move_line WHERE debit <> 0 AND create_date >= '2016-01-01') debits
ON credits.move_id = debits.move_id
LEFT JOIN
 account_move ON credits.move_id=account_move.id
WHERE credits.amount <> debits.amount 
  AND credits.journal_id = 9