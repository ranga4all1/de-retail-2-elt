# -*- coding: utf-8 -*-

from airflow.decorators import dag, task
from datetime import datetime, timedelta

from airflow.providers.google.cloud.transfers.local_to_gcs import LocalFilesystemToGCSOperator
from airflow.providers.google.cloud.operators.bigquery import BigQueryCreateEmptyDatasetOperator
from astro import sql as aql
from astro.files import File
from airflow.models.baseoperator import chain
from astro.sql.table import Table, Metadata
from astro.constants import FileType

from include.dbt.cosmos_config import DBT_PROJECT_CONFIG, DBT_CONFIG
from cosmos.airflow.task_group import DbtTaskGroup
from cosmos.constants import LoadMode
from cosmos.config import ProjectConfig, RenderConfig

import pandas as pd

@dag(
    start_date=datetime(2024, 1, 1),
    schedule=None,
    catchup=False,
    tags=['retail'],
)

def retail():

    @task
    def process_csv():
        # Read the raw CSV file
        df = pd.read_csv('/usr/local/airflow/include/dataset/online_retail_raw.csv', encoding='latin-1')
              
        # Save the processed data to a new CSV file in udf-8 encoding
        df.to_csv('/usr/local/airflow/include/dataset/online_retail.csv', index=False)

    upload_csv_to_gcs = LocalFilesystemToGCSOperator(
	    task_id = 'upload_csv_to_gcs',
        src='/usr/local/airflow/include/dataset/online_retail.csv',
	    dst='raw/online_retail.csv',
	    bucket='rh_online_retail',
	    gcp_conn_id='gcp',
        mime_type='text/csv',
        )
    
    create_retail_dataset = BigQueryCreateEmptyDatasetOperator(
        task_id='create_retail_dataset',
        dataset_id='retail',
        gcp_conn_id='gcp',
        )
    
    gcs_to_raw = aql.load_file(
        task_id='gcs_to_raw',
        input_file=File(
            'gs://rh_online_retail/raw/online_retail.csv',
            conn_id='gcp',
            filetype=FileType.CSV,
        ),
        output_table=Table(
            name='raw_invoices',
            conn_id='gcp',
            metadata=Metadata(schema='retail')
        ),
        use_native_support=False,
    )

    transform = DbtTaskGroup(
        group_id='transform',
        project_config=DBT_PROJECT_CONFIG,
        profile_config=DBT_CONFIG,
        render_config=RenderConfig(
            load_method=LoadMode.DBT_LS,
            select=['path:models/transform/']
        )
    )

    report = DbtTaskGroup(
        group_id='report',
        project_config=DBT_PROJECT_CONFIG,
        profile_config=DBT_CONFIG,
        render_config=RenderConfig(
            load_method=LoadMode.DBT_LS,
            select=['path:models/report']
        )
    )


    @task.external_python(python='/usr/local/airflow/soda_venv/bin/python')
    def check_load(scan_name='check_load', checks_subpath='sources'):
        from include.soda.check_function import check

        return check(scan_name, checks_subpath) 
    
    @task.external_python(python='/usr/local/airflow/soda_venv/bin/python')
    def check_transform(scan_name='check_transform', checks_subpath='transform'):
        from include.soda.check_function import check

        return check(scan_name, checks_subpath)
    
    @task.external_python(python='/usr/local/airflow/soda_venv/bin/python')
    def check_report(scan_name='check_report', checks_subpath='report'):
        from include.soda.check_function import check

        return check(scan_name, checks_subpath)


    csv_task = process_csv()
    check_load_task = check_load()
    check_transform_task = check_transform()
    check_report_task = check_report()

    chain(
        csv_task,
        upload_csv_to_gcs,
        create_retail_dataset,
        gcs_to_raw,
        check_load_task,
        transform,
        check_transform_task,
        report,
        check_report_task,
    )

    # csv_task >> upload_csv_to_gcs >> create_retail_dataset >> gcs_to_raw >> check_load_task >> transform >> check_transform_task >> report >> check_report_task
    
retail()