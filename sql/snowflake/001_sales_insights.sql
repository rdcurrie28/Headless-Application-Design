CREATE SCHEMA IF NOT EXISTS SALES_INSIGHTS;
USE SCHEMA SALES_INSIGHTS;

CREATE TABLE IF NOT EXISTS ENTITLEMENTS (
    customer_id     STRING        NOT NULL,
    sku             STRING        NOT NULL,
    product_name    STRING        NOT NULL,
    product_family  STRING,
    quantity        NUMBER(18,2)  NOT NULL,
    arr             NUMBER(18,2)  NOT NULL,
    start_date      DATE          NOT NULL,
    end_date        DATE          NOT NULL
);

CREATE TABLE IF NOT EXISTS USAGE_DAILY (
    customer_id     STRING        NOT NULL,
    sku             STRING        NOT NULL,
    usage_date      DATE          NOT NULL,
    consumed_units  NUMBER(18,2)  NOT NULL
)
CLUSTER BY (customer_id, usage_date);

CREATE TABLE IF NOT EXISTS PROPENSITY_SCORES (
    customer_id     STRING         NOT NULL,
    model_name      STRING         NOT NULL,
    model_version   STRING,
    score           FLOAT          NOT NULL,
    scored_at       TIMESTAMP_NTZ  NOT NULL,
    top_drivers     ARRAY
);

CREATE OR REPLACE VIEW PROPENSITY_LATEST AS
SELECT customer_id, LOWER(model_name) AS model_name, model_version, score, scored_at, top_drivers
FROM PROPENSITY_SCORES
QUALIFY ROW_NUMBER() OVER (PARTITION BY customer_id, LOWER(model_name) ORDER BY scored_at DESC) = 1;

CREATE OR REPLACE VIEW PRODUCT_HEALTH AS
WITH cur AS (
    SELECT customer_id, sku, AVG(consumed_units) AS avg_units
    FROM USAGE_DAILY
    WHERE usage_date >= DATEADD(day, -30, CURRENT_DATE())
    GROUP BY customer_id, sku
),
prev AS (
    SELECT customer_id, sku, AVG(consumed_units) AS avg_units
    FROM USAGE_DAILY
    WHERE usage_date >= DATEADD(day, -60, CURRENT_DATE())
      AND usage_date <  DATEADD(day, -30, CURRENT_DATE())
    GROUP BY customer_id, sku
),
scored AS (
    SELECT e.customer_id, e.sku, e.product_name,
           ROUND(DIV0(COALESCE(cur.avg_units, 0), e.quantity) * 100, 1) AS utilization_pct,
           ROUND(DIV0NULL(cur.avg_units - prev.avg_units, prev.avg_units) * 100, 1) AS trend_30d_pct
    FROM ENTITLEMENTS e
    LEFT JOIN cur  ON cur.customer_id  = e.customer_id AND cur.sku  = e.sku
    LEFT JOIN prev ON prev.customer_id = e.customer_id AND prev.sku = e.sku
    WHERE e.end_date >= CURRENT_DATE()
)
SELECT customer_id, sku, product_name, utilization_pct, trend_30d_pct,
       ROUND(LEAST(utilization_pct, 100) * 0.7
             + LEAST(GREATEST(50 + COALESCE(trend_30d_pct, 0), 0), 100) * 0.3, 0) AS health_score,
       CASE
           WHEN health_score >= 70 THEN 'healthy'
           WHEN health_score >= 40 THEN 'watch'
           ELSE 'at_risk'
       END AS status
FROM scored;

CREATE ROLE IF NOT EXISTS INSIGHTS_API_RO;
GRANT USAGE ON SCHEMA SALES_INSIGHTS TO ROLE INSIGHTS_API_RO;
GRANT SELECT ON ALL TABLES IN SCHEMA SALES_INSIGHTS TO ROLE INSIGHTS_API_RO;
GRANT SELECT ON ALL VIEWS  IN SCHEMA SALES_INSIGHTS TO ROLE INSIGHTS_API_RO;
