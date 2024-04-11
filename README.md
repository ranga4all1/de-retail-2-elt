# de-retail-2-elt
A complete data engineering project with ELT pipeline for online Retail Sales

## Tech Stack

- GitHub codespace
    - Astro CLI - data orchestration with Apache Airflow
    - Astro cosmos - integrated dbt + Airflow
    - soda - data quality tests in data pipelines
    - metabse - Data visualization
- GCP storage bucket - Data lake
- GCP Bigquery - OLAP Data warehouse

## Pipeline

- Airflow DAG

![DAG-retail](include/images/DAG-retail.png)

- BigQuery DWH - Retail

![DWH-retail](include/images/DWH-retail.png)

- soda data quality checks

![soda-checks1](include/images/soda-checks1.png)

![soda-checks2](include/images/soda-check2.png)

- Metabase Dashboard

![dashboard-metabase](include/images/dashboard-metabase.png)
