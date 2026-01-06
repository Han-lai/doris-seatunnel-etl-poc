import requests
import logging
from typing import Optional

# 設定日誌
logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")

# 配置參數
DORIS_HOST = "http://10.136.147.130:8030"
DATABASE = "test_variant"
TABLE = "test_routineload_tbl"
USER = "root"
PASSWORD = ""
KAFKA_BROKER_LIST = "10.136.218.207:9092"
KAFKA_TOPIC = "CFX_CFX_Production_WorkCompleted"
ROUTINE_LOAD_NAME = "routine_load_WorkCompleted"


def execute_sql(sql: str) -> Optional[dict]:
    """
    執行 SQL 命令並返回結果。
    """
    # 修正后的 URL
    url = f"{DORIS_HOST}/api/query/{DATABASE}"

    try:
        # 发送 POST 请求来执行 SQL 查询
        response = requests.post(url, auth=(USER, PASSWORD), data={"sql": sql})
        
        response.raise_for_status()  # 如果 HTTP 状态码不为 200，抛出异常
        logging.info("SQL Execution Success")
        return response.json()  # 返回 JSON 格式的响应
    except requests.exceptions.RequestException as e:
        logging.error(f"SQL Execution Failed: {e}")
        return None

def create_table():
    """
    建立 Doris 表格。
    """
    create_table_sql = f"""
    CREATE TABLE IF NOT EXISTS  {DATABASE}.{TABLE} (

        RawData_UniqueID VARCHAR(255)   NULL,
        RawData_RequestID VARCHAR(255)   NULL,
        ProcessedTime DATETIME  NULL,
        
        RawData_MessageName VARCHAR(255)  NULL,
        RawData_Version VARCHAR(255) NOT NULL,
        RawData_TimeStamp VARCHAR(255)   NULL,
        RawData_Source VARCHAR(255)  NULL,
        RawData_Target VARCHAR(255)   NULL,
        Type VARCHAR(255)   NULL,
        TransactionID VARCHAR(255)   NULL,  -- renamed to avoid keyword conflict
        Result VARCHAR(255)  NULL,
        PrimaryIdentifier VARCHAR(255)  NULL,
        HermesIdentifier VARCHAR(255)   NULL,
        UnitCount VARCHAR(255)   NULL,
        Meta_DeviceID VARCHAR(255)   NULL,
        Meta_LineID VARCHAR(255)   NULL,
        Meta_MfgPlantCode VARCHAR(255)    NULL ,
        Meta_Factory VARCHAR(255)    NULL,
        Meta_MessageName VARCHAR(255)   NULL,
        Meta_Source VARCHAR(255)   NULL,  -- renamed to avoid keyword conflict
        MessageID VARCHAR(255)   NULL,
        MessageType VARCHAR(255)   NULL,
        MessageVersion VARCHAR(255)   NULL,
        MessageTime VARCHAR(255)   NULL,
        Sender VARCHAR(255)   NULL
      
    ) ENGINE=OLAP
    UNIQUE KEY(`RawData_UniqueID`, `RawData_RequestID`, `ProcessedTime`)
    PARTITION BY RANGE(`ProcessedTime`)
    (PARTITION p202410 VALUES [('2024-10-01 00:00:00'), ('2024-11-01 00:00:00')),
    PARTITION p202411 VALUES [('2024-11-01 00:00:00'), ('2024-12-01 00:00:00')),
    PARTITION p202412 VALUES [('2024-12-01 00:00:00'), ('2025-01-01 00:00:00')))
    DISTRIBUTED BY HASH(`RawData_UniqueID`) BUCKETS AUTO
    PROPERTIES (
    "replication_allocation" = "tag.location.default: 1",
    "min_load_replica_num" = "-1",
    "is_being_synced" = "false",
    "dynamic_partition.enable" = "true",
    "dynamic_partition.time_unit" = "MONTH",
    "dynamic_partition.time_zone" = "Etc/UTC",
    "dynamic_partition.start" = "-2",
    "dynamic_partition.end" = "2",
    "dynamic_partition.prefix" = "p",
    "dynamic_partition.replication_allocation" = "tag.location.default: 1",
    "dynamic_partition.buckets" = "16",
    "dynamic_partition.create_history_partition" = "false",
    "dynamic_partition.history_partition_num" = "-1",
    "dynamic_partition.hot_partition_num" = "0",
    "dynamic_partition.reserved_history_periods" = "NULL",
    "dynamic_partition.storage_policy" = "",
    "dynamic_partition.start_day_of_month" = "1",
    "storage_medium" = "hdd",
    "storage_format" = "V2",
    "inverted_index_storage_format" = "V1",
    "enable_unique_key_merge_on_write" = "true",
    "light_schema_change" = "true",
    "disable_auto_compaction" = "false",
    "enable_single_replica_compaction" = "false",
    "group_commit_interval_ms" = "10000",
    "group_commit_data_bytes" = "134217728",
    "enable_mow_light_delete" = "false")
    """
    logging.info("Creating table...")
    execute_sql(create_table_sql)

def setup_routine_load():
    """
    設定 Routine Load 任務。
    """
    routine_load_sql = f"""
    CREATE ROUTINE LOAD {DATABASE}.{ROUTINE_LOAD_NAME}
    ON {DATABASE}.{TABLE}
    PROPERTIES (
        "desired_concurrent_number"="3",
        "max_batch_rows"="200000",
        "max_batch_size"="300MB",
        "max_error_number"="100"
    )
    FROM KAFKA (
        "kafka_broker_list" = "{KAFKA_BROKER_LIST}",
        "kafka_topic" = "{KAFKA_TOPIC}",
        "kafka_partitions" = "0,1,2",
        "property.group.id" = "routine_load_group"
    )
    COLUMNS (
        user_id,
        name,
        age
    );
    """
    logging.info("Setting up Routine Load...")
    execute_sql(routine_load_sql)

def main():
    """
    主程式執行邏輯。
    """
    create_table()
    setup_routine_load()

if __name__ == "__main__":
    main()
