CREATE TABLE public.sodanca_shipment_schedule
(
    id serial NOT NULL,
    supplier_name character varying(30) NOT NULL,
    supplier_id integer NOT NULL,
    cut_off_date date NOT NULL,
    expected_date date NOT NULL,
    PRIMARY KEY (id)
)
WITH (
    OIDS = FALSE
);

ALTER TABLE public.sodanca_shipment_schedule
    OWNER to purchase_planner;
