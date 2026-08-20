-- Paper benchmark RDB schema (Fig.1 from the paper)
-- Compatible with PostgreSQL and MySQL

CREATE TABLE Customers (
    id_customer  SERIAL PRIMARY KEY,
    name         VARCHAR(100),
    email        VARCHAR(100),
    address      TEXT
);

CREATE TABLE Orders (
    id_order     SERIAL PRIMARY KEY,
    id_customer  INT REFERENCES Customers(id_customer),
    orderdate    DATE,
    totalamount  DECIMAL(10,2)
);

CREATE TABLE Products (
    id_prod  SERIAL PRIMARY KEY,
    actor    VARCHAR(100),
    title    VARCHAR(200),
    price    DECIMAL(10,2)
);

CREATE TABLE Orderlines (
    id_orderline  SERIAL PRIMARY KEY,
    order_id      INT REFERENCES Orders(id_order),
    prod_id       INT REFERENCES Products(id_prod),
    quantity      INT,
    orderlinedate DATE
);

CREATE TABLE Inventory (
    id_inv    SERIAL PRIMARY KEY,
    prod_id   INT REFERENCES Products(id_prod),
    quan_in_stock INT,
    sales     INT,
    market_price DECIMAL(10,2)
);

CREATE TABLE Reorder (
    id_reorder  SERIAL PRIMARY KEY,
    prod_id     INT REFERENCES Products(id_prod),
    date_low    DATE,
    quan_low    INT,
    date_reordered DATE,
    quan_reordered INT,
    date_expected DATE
);