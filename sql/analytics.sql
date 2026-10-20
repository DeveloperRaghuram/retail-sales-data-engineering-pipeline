-- Run these queries against output/retail_warehouse.db using SQLite.
-- Monthly revenue trend
SELECT substr(order_date, 1, 7) AS month,
       ROUND(SUM(revenue), 2) AS revenue,
       SUM(quantity) AS units_sold,
       COUNT(*) AS transaction_count
FROM sales
GROUP BY substr(order_date, 1, 7)
ORDER BY month;

-- Revenue by category
SELECT category, ROUND(SUM(revenue), 2) AS revenue
FROM sales
GROUP BY category
ORDER BY revenue DESC;

-- Regional performance
SELECT region, ROUND(SUM(revenue), 2) AS revenue,
       COUNT(*) AS transaction_count
FROM sales
GROUP BY region
ORDER BY revenue DESC;
