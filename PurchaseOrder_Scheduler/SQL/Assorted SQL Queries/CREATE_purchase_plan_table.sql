-- Table: public.sodanca_purchase_plan

DROP TABLE IF EXISTS public.sodanca_purchase_plan;

CREATE TABLE public.sodanca_purchase_plan
(
    id SERIAL,
    type character(1) COLLATE pg_catalog."default" NOT NULL,
    vendor integer NOT NULL,
    vendor_group integer,
    creation_date date NOT NULL,
    expected_date date NOT NULL,
    template_id integer NOT NULL,
    product_id integer NOT NULL,
    product_grade character(1) COLLATE pg_catalog."default",
    order_mod smallint,
    qty_2_ord numeric NOT NULL,
    qty_2_ord_adj numeric NOT NULL,
    qty_on_order numeric,
    qty_on_order_period numeric,
    qty_committed numeric,
    qty_sold numeric,
    expected_on_hand numeric,
    qty_on_hand numeric,
    sales_trend numeric,
    box_capacity integer,
    CONSTRAINT sodanca_purchase_plan_pkey PRIMARY KEY (id)
)
WITH (
    OIDS = FALSE
)
TABLESPACE pg_default;

ALTER TABLE public.sodanca_purchase_plan
    OWNER to sodanca;
COMMENT ON TABLE public.sodanca_purchase_plan
    IS 'Reset nightly, used by stock purchase planner';
