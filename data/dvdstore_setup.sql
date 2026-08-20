-- Dell DVD Store schema (subset used for DVD Store adapter)
-- Source: linux.dell.com/dvdstore

CREATE TABLE CATEGORIES (
    category     SMALLINT     PRIMARY KEY,
    categoryname VARCHAR(50)  NOT NULL
);

CREATE TABLE PRODUCTS (
    prod_id        SERIAL       PRIMARY KEY,
    category       SMALLINT     REFERENCES CATEGORIES(category),
    title          VARCHAR(50)  NOT NULL,
    actor          VARCHAR(50)  NOT NULL,
    price          NUMERIC(5,2) NOT NULL,
    special        SMALLINT,
    common_prod_id INT
);

CREATE TABLE CUSTOMERS (
    customerid          SERIAL       PRIMARY KEY,
    firstname           VARCHAR(50)  NOT NULL,
    lastname            VARCHAR(50)  NOT NULL,
    address1            VARCHAR(50),
    address2            VARCHAR(50),
    city                VARCHAR(50),
    state               VARCHAR(50),
    zip                 INT,
    country             VARCHAR(50),
    phone               VARCHAR(50),
    email               VARCHAR(50)  NOT NULL,
    username            VARCHAR(50)  NOT NULL UNIQUE,
    password            VARCHAR(50)  NOT NULL,
    creditcardtype      SMALLINT,
    creditcard          VARCHAR(50),
    creditcardexpiration VARCHAR(10),
    age                 SMALLINT,
    income              INT,
    gender              CHAR(1)
);

CREATE TABLE ORDERS (
    orderid     SERIAL        PRIMARY KEY,
    orderdate   DATE          NOT NULL,
    customerid  INT           REFERENCES CUSTOMERS(customerid),
    netamount   NUMERIC(8,2)  NOT NULL,
    tax         NUMERIC(8,2)  NOT NULL,
    totalamount NUMERIC(8,2)  NOT NULL
);

CREATE TABLE ORDERLINES (
    orderlineid SERIAL  PRIMARY KEY,
    orderid     INT     REFERENCES ORDERS(orderid),
    prod_id     INT     REFERENCES PRODUCTS(prod_id),
    quantity    SMALLINT NOT NULL,
    orderdate   DATE    NOT NULL
);