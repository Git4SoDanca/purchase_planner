-- Table: public.sodanca_estoque_pulmao

-- DROP TABLE public.sodanca_estoque_pulmao;

CREATE TABLE public.sodanca_estoque_pulmao
(
    id integer NOT NULL DEFAULT nextval('sodanca_estoque_pulmao_id_seq'::regclass),
    date date NOT NULL,
    product_id integer NOT NULL,
    product_name character varying(64) COLLATE pg_catalog."default",
    quantity numeric,
    CONSTRAINT sodanca_estoque_pulmao_pkey PRIMARY KEY (id)
)
WITH (
    OIDS = FALSE
)
TABLESPACE pg_default;

ALTER TABLE public.sodanca_estoque_pulmao
    OWNER to sodanca;
COMMENT ON TABLE public.sodanca_estoque_pulmao
    IS 'This is updated daily from the email sent from Soles, by default the data is cycled every 12 months, this can be adjusted on the config file';
