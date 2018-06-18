 SELECT
        CASE
            WHEN res_partner.parent_id IS NULL THEN res_partner.id
            ELSE res_partner.parent_id
        END AS grouped_partner_id,
    res_partner.cust_number,
    res_partner.name,
    res_partner.reward_segment AS current_level,
    res_partner.city,
    res_country_state.code,
    res_partner.zip,
    res_country.name AS country,
    res_partner.user_id,
    yrb4Prev_total.invoice_total AS total_sales_year_before_last,
    prevyr_total.invoice_total AS total_sales_lastyr,
    ytd_total.invoice_total AS total_sales_ytd,
        CASE
            WHEN prevyr_total.invoice_total < 6000::numeric THEN '1 Star'::text
            WHEN prevyr_total.invoice_total >= 6000::numeric AND prevyr_total.invoice_total < 10000::numeric THEN '2 Star'::text
            WHEN prevyr_total.invoice_total >= 10000::numeric AND prevyr_total.invoice_total < 20000::numeric THEN '3 Star'::text
            WHEN prevyr_total.invoice_total >= 20000::numeric AND prevyr_total.invoice_total < 30000::numeric THEN '4 Star'::text
            WHEN prevyr_total.invoice_total >= 30000::numeric AND prevyr_total.invoice_total < 50000::numeric THEN '5 Star'::text
            WHEN prevyr_total.invoice_total >= 50000::numeric AND prevyr_total.invoice_total < 100000::numeric THEN 'Superstar'::text
            WHEN prevyr_total.invoice_total >= 100000::numeric AND prevyr_total.invoice_total < 200000::numeric THEN 'Platinum'::text
            WHEN prevyr_total.invoice_total >= 200000::numeric THEN 'Diamond'::text
            ELSE NULL::text
        END AS current_sr_level,
        CASE
            WHEN prevyr_total.invoice_total >= 5400::numeric AND prevyr_total.invoice_total < 6000::numeric THEN '2 Star'::text
            WHEN prevyr_total.invoice_total >= 9900::numeric AND prevyr_total.invoice_total < 10000::numeric THEN '3 Star'::text
            WHEN prevyr_total.invoice_total >= 18000::numeric AND prevyr_total.invoice_total < 20000::numeric THEN '4 Star'::text
            WHEN prevyr_total.invoice_total >= 27000::numeric AND prevyr_total.invoice_total < 30000::numeric THEN '5 Star'::text
            WHEN prevyr_total.invoice_total >= 45000::numeric AND prevyr_total.invoice_total < 50000::numeric THEN 'Superstar'::text
            WHEN prevyr_total.invoice_total >= 90000::numeric AND prevyr_total.invoice_total < 100000::numeric THEN 'Platinum'::text
            WHEN prevyr_total.invoice_total >= 180000::numeric AND prevyr_total.invoice_total < 200000::numeric THEN 'Diamond'::text
            ELSE NULL::text
        END AS possible_srlevel,
    res_users.login
   FROM res_partner
     LEFT JOIN res_country_state ON res_country_state.id = res_partner.state_id
     LEFT JOIN res_country ON res_country.id = res_country_state.country_id
     LEFT JOIN res_users ON res_users.id = res_partner.user_id
     LEFT JOIN ( SELECT
                CASE
                    WHEN res_partner_1.parent_id IS NULL THEN res_partner_1.id
                    ELSE res_partner_1.parent_id
                END AS grouped_partner_id,
            sum(
                CASE
                    WHEN account_invoice.type::text = 'out_invoice'::text THEN account_invoice.amount_total
                    WHEN account_invoice.type::text = 'out_refund'::text THEN '-1'::integer::numeric * account_invoice.amount_total
                    ELSE '9999999999'::bigint::numeric
                END) AS invoice_total
           FROM account_invoice
             LEFT JOIN account_period ON account_period.id = account_invoice.period_id
             LEFT JOIN res_partner res_partner_1 ON res_partner_1.id = account_invoice.partner_id
          WHERE "right"(account_period.name::text, 4) = to_char(now() - '1 year'::interval, 'YYYY'::text) AND account_invoice.state != 'cancel'
          GROUP BY (
                CASE
                    WHEN res_partner_1.parent_id IS NULL THEN res_partner_1.id
                    ELSE res_partner_1.parent_id
                END)
          ORDER BY (
                CASE
                    WHEN res_partner_1.parent_id IS NULL THEN res_partner_1.id
                    ELSE res_partner_1.parent_id
                END)) prevyr_total ON res_partner.id = prevyr_total.grouped_partner_id
          LEFT JOIN ( SELECT
                CASE
                    WHEN res_partner_1.parent_id IS NULL THEN res_partner_1.id
                    ELSE res_partner_1.parent_id
                END AS grouped_partner_id,
            sum(
                CASE
                    WHEN account_invoice.type::text = 'out_invoice'::text THEN account_invoice.amount_total
                    WHEN account_invoice.type::text = 'out_refund'::text THEN '-1'::integer::numeric * account_invoice.amount_total
                    ELSE '9999999999'::bigint::numeric
                END) AS invoice_total
           FROM account_invoice
             LEFT JOIN account_period ON account_period.id = account_invoice.period_id
             LEFT JOIN res_partner res_partner_1 ON res_partner_1.id = account_invoice.partner_id
          WHERE "right"(account_period.name::text, 4) = to_char(now() - '2 year'::interval, 'YYYY'::text) AND account_invoice.state != 'cancel'
          GROUP BY (
                CASE
                    WHEN res_partner_1.parent_id IS NULL THEN res_partner_1.id
                    ELSE res_partner_1.parent_id
                END)
          ORDER BY (
                CASE
                    WHEN res_partner_1.parent_id IS NULL THEN res_partner_1.id
                    ELSE res_partner_1.parent_id
                END)) yrb4Prev_total ON res_partner.id = yrb4Prev_total.grouped_partner_id
     LEFT JOIN ( SELECT
                CASE
                    WHEN res_partner_1.parent_id IS NULL THEN res_partner_1.id
                    ELSE res_partner_1.parent_id
                END AS grouped_partner_id,
            sum(
                CASE
                    WHEN account_invoice.type::text = 'out_invoice'::text THEN account_invoice.amount_total
                    WHEN account_invoice.type::text = 'out_refund'::text THEN '-1'::integer::numeric * account_invoice.amount_total
                    ELSE '9999999999'::bigint::numeric
                END) AS invoice_total
           FROM account_invoice
             LEFT JOIN account_period ON account_period.id = account_invoice.period_id
             LEFT JOIN res_partner res_partner_1 ON res_partner_1.id = account_invoice.partner_id
          WHERE "right"(account_period.name::text, 4) = to_char(now(), 'YYYY'::text) AND account_invoice.state != 'cancel'
          GROUP BY (
                CASE
                    WHEN res_partner_1.parent_id IS NULL THEN res_partner_1.id
                    ELSE res_partner_1.parent_id
                END)
          ORDER BY (
                CASE
                    WHEN res_partner_1.parent_id IS NULL THEN res_partner_1.id
                    ELSE res_partner_1.parent_id
                END)) ytd_total ON res_partner.id = ytd_total.grouped_partner_id
  WHERE res_partner.customer = true AND res_partner.active = true AND res_partner.cust_number IS NOT NULL AND (prevyr_total.invoice_total <> 0::numeric OR ytd_total.invoice_total <> 0::numeric)
  ORDER BY prevyr_total.invoice_total DESC;
