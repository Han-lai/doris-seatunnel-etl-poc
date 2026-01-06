# Apache Doris 研究主題
[TOC]
# 其他配置紀錄
[seatunnel 與doris配置紀錄](https://codimd-10-136-218-208.traefik.me/0ndDMpvnTCWxz-mMafMkqQ?both)
[數據上架測試內容](https://codimd-10-136-218-208.traefik.me/cL3ZCVHJSiumb5EuM9Mmhg?view)
# 資料模型 (Data Model)
Apache Doris 提供三種資料模型，以滿足不同場景需求：

## Duplicate Key Model
* 適用場景：適合需要記錄全量數據的場景，如日志數據或寬表。
* 特點：直接插入數據，不進行重複值處理。
* 優勢：高效寫入，適合不需去重的大量數據場景。

```SQL
CREATE TABLE duplicate_table (
    id BIGINT,
    name VARCHAR,
    value DOUBLE
) ENGINE=OLAP
DUPLICATE KEY(id)
DISTRIBUTED BY HASH(id) BUCKETS 10;
```

## Unique Key Model
* 適用場景：適合對唯一值有嚴格需求的場景，如需要更新的訂單或用戶數據。
* 特點：會基於 Key 去重，當遇到重複的 Key 時僅保留最新數據。
* 優勢：保證數據唯一性。
```
CREATE TABLE unique_table (
    user_id BIGINT,
    name VARCHAR,
    last_login TIMESTAMP
) ENGINE=OLAP
UNIQUE KEY(user_id)
DISTRIBUTED BY HASH(user_id) BUCKETS 10;
```

## Aggregate Key Model

* 適用場景：適合需要聚合計算的場景，如 OLAP 報表。
* 特點：基於 Key 聚合，並使用指定的聚合方法（如 SUM、MIN、MAX）。
* 優勢：匯入過程中自動進行聚合，減少查詢時的計算負擔。

# 分層儲存 (Tiered Storage)

* 建立 Resource
* 建立不同的儲存資源（如 S3、HDFS），用於分層儲存數據，以減少成本。
```
CREATE RESOURCE "s3_resource"
PROPERTIES (
    "type"="s3",
    "aws.s3.endpoint"="your_s3_endpoint",
    "aws.s3.access_key"="your_access_key",
    "aws.s3.secret_key"="your_secret_key"
);
```

## 建立 Storage Policy
建立Storage Policy 控制數據冷卻時間，可用相對或絕對的設定，僅能選一個不可同時使用
* 相對時間
```
CREATE STORAGE POLICY testPolicy
PROPERTIES(
  "storage_resource" = "remote_s3",  --所使用上述建立的storage resource
  "cooldown_ttl" = "1d" --一天後冷卻
);
```
* 絕對時間
```
CREATE STORAGE POLICY testPolicyForTTlDatatime
PROPERTIES(
  "storage_resource" = "remote_s3",
  "cooldown_datetime" = "2024-09-07 21:00:00"
);
```
### 確認storage policy 狀態
```
SHOW STORAGE POLICY
Show storage policy using;
```
### 更改storage policy 冷熱時間
```
ALTER STORAGE POLICY test_policy PROPERTIES("cooldown_datetime" = "2024-09-30 00:00:00");
ALTER STORAGE POLICY test_policy PROPERTIES ("cooldown_ttl" = "1d");
```

### partition or tablet設置storage policy
```
CREATE TABLE IF NOT EXISTS `${database}`.`${table}`
(
`TimeStamp` Datetime,
${rowtype_fields},
) ENGINE=OLAP
DUPLICATE KEY(`TimeStamp`, `UniqueID`)
PARTITION BY RANGE(`TimeStamp`)
(
PARTITION p202408 VALUES LESS THAN ('2024-09-01'),
PARTITION p202409 VALUES LESS THAN ('2024-10-01')
)
DISTRIBUTED BY HASH(`UniqueID`) BUCKETS 5
PROPERTIES (
"replication_allocation" = "tag.location.default: 1",
"storage_policy" = "test_policy", -- 設定storage_policy
)      
```

假設只針對一個partition 設置policy ，只須於partition後面新增`("storage_policy" = "${policy_name}")`
```
CREATE TABLE IF NOT EXISTS `${database}`.`${table}`
(
`TimeStamp` Datetime,
${rowtype_fields},
) ENGINE=OLAP
DUPLICATE KEY(`TimeStamp`, `UniqueID`)
PARTITION BY RANGE(`TimeStamp`)
(
PARTITION p202408 VALUES LESS THAN ('2024-09-01')("storage_policy" = "${policy_name}"),
PARTITION p202409 VALUES LESS THAN ('2024-10-01')
)
```

# 分區和 Tablet 用法 (Partition/Tablet)

Doris 支援按日期、ID 分區，並分散到多個 Tablet 中，提升查詢與寫入效率
```
CREATE TABLE partitioned_table (
    id BIGINT,
    name VARCHAR,
    event_date DATE
)
PARTITION BY RANGE(event_date) (
    PARTITION p2023 VALUES LESS THAN ('2023-01-01'),
    PARTITION p2024 VALUES LESS THAN ('2024-01-01')
);
```

## 動態分區 (Dynamic Partition)
適合持續增長的數據，Doris 可根據設定自動新增或刪除分區。
```
ALTER TABLE your_table
SET (
    "dynamic_partition.enable" = "true",
    "dynamic_partition.time_unit" = "DAY",
    "dynamic_partition.end" = "3",
    "dynamic_partition.prefix" = "p",
    "dynamic_partition.buckets" = "3"
);
```


##  Auto Partition vs Auto Bucket

### Partition
* 靜態分區：必須手動指定每個分區範圍。
* 動態分區 (Auto Partition)：Doris 可以自動生成特定時間範圍內的分區，例如依據天、月或年來自動擴展。
```
start 和 end 決定自動分區的範圍。
time_unit 表示分區的單位，如月、日、年。
prefix 為自動分區的名稱前綴。
```
```
PROPERTIES (
    "dynamic_partition.enable" = "true",
    "dynamic_partition.time_unit" = "MONTH",
    "dynamic_partition.start" = "-2",
    "dynamic_partition.end" = "2",
    "dynamic_partition.prefix" = "p",
    "dynamic_partition.buckets" = "8"
)
```
![](/uploads/upload_2dbdff84ec1332b89b19e706d8967b85.png)



*  避免資料不完整或分區衝突

> dynamic_partition 動態建立未來範圍內的分區，根據指定時間單位（如 WEEK、MONTH）自動生成。但若資料表中已有超過動態範圍的歷史資料，需手動建立對應分區，以避免資料遺漏或衝突。
> 例如，若動態分區範圍設為「前 2 週至後 2 週」，但資料表中還包含 8 月或更早的資料，則需手動建立 p202408 等歷史分區，因這些範圍不會自動生成。




*  初始化階段的靜態分區
> 在初始化資料表時，手動定義足夠的歷史分區。動態分區則負責未來的自動管理。

*  避免時間單位的衝突避免時間單位的衝突
> 確認手動分區與動態分區的設計一致，避免重複定義或時間單位不匹配的錯誤。例如，若 `dynamic_partition.time_unit` 設為 WEEK，但手動分區是以月為單位（如 `p202408`、`p202409`），可能導致 Doris 無法正確劃分資料。



### Bucket
* 靜態桶分配：在建立表時手動指定桶數（如 2、5、8）。
```
DISTRIBUTED BY HASH(`UniqueID`) BUCKETS 5;
```
* Auto Bucket：Doris 可以自動根據資料量和查詢負載來調整桶數，達到最佳化。

### Auto Partition vs Auto Bucket

| 比較項目     | Auto Partition                 | Auto Bucket                         |
|--------------|--------------------------------|------------------------------------|
| **主要目的** | 自動生成分區來支持時間序列資料 | 自動調整桶數以最佳化查詢和寫入性能 |
| **使用場合** | 適用於需要定期增量數據的場景，如月報或日報 | 適用於資料量動態變化大的場景     |
| **設置方式** | 動態分區屬性設定               | 預期支援自動桶數分配（未來功能可能提供） |
| **效能優化** | 減少查詢範圍，提高查詢效率     | 自動負載平衡，提高讀寫性能         |
| **限制**     | 需小心規劃分區範圍，避免過多分區影響性能 | 靜態設定時需預估桶數，避免過多或過少 |

---

## DEMO



| TABLE | CREATE TABLE | APPEND TABLE | COOL DOWN | PARITION | BUCKET |
| -------- | -------- | -------- | -------- | -------- | -------- |
| CFX_WorkCompleted     | WJ03     | WJ02   | allpartition | 靜態 | 5 |
| CFX_WorkCompleted_dynamic     | WJ03     | WJ02     | allpartition | 動態 | 5 |
| CFX_WorkCompleted_autobkt     | WJ03     | WJ02     | allpartition | 動態 | auto |

---
* 不同partition可以掛不同的policy，需要另外設定
```
ALTER TABLE my_table MODIFY PARTITION p1 SET ("storage_policy" = "POLICY_TEST1")
ALTER TABLE my_table MODIFY PARTITION p2 SET ("storage_policy" = "POLICY_TEST2")
```
















## 批次提交 (Group Commit)
Doris 支援 Group Commit，可減少多筆寫入的提交次數，提升寫入效能。
```
enable_group_commit = true
group_commit_interval_ms = 1000
```

# 大量數據插入時的 FE/BE 最佳化設定
針對大量數據插入，可對 Frontend (FE) 和 Backend (BE) 進行最佳化配置。

### FE 設定
* max_allowed_packet：增大封包大小以避免分批傳輸。
* fe_batch_flush_interval_ms：降低值以增加批次提交頻率。
### BE 設定
* write_buffer_size：增大緩衝區避免小批次寫入。
* compaction_score_threshold：增高數值以減少 Compaction 頻率。
* load_parallel_instance_num：提升並行實例數，增強處理效能。


# Stream Load
## 使用情境
Stream Load 尤其適合需要低延遲的即時數據流或頻繁的小批量導入的場景。以下是典型的應用情境：

* 即時監控數據：如 IoT 設備的數據收集、用戶行為的追蹤，Stream Load 可將即時數據迅速導入 Doris 進行即時分析。
* 小批量數據導入：適合持續性但單次數據量小的導入情境，如網頁訪問日誌、訂單流轉等。
* 數據修補：在實時修補少量數據或補充錯漏數據時，Stream Load 提供簡便的方法，無需重新上傳大批數據。

使用方式
Stream Load 提供 REST API，可直接通過 HTTP 請求提交數據。
```
curl -XPUT http://fe_host:8030/api/database_name/table_name/_stream_load
-u user:password
-H "format: json"
-H "column_separator: ,"
-T /path/to/your_data.csv
```

配置選項
* timeout：設定請求超時時間。
* max_filter_ratio：設置數據過濾比例，用於忽略少量錯誤數據。

##  運用Seatunel進行streamload到doris 的配置

Seatunnel 支援 Streamload 到 Apache Doris 的配置，你需要配置 Seatunnel 的 Source（源）和 Sink（目標）部分。

### 配置 Doris 作為 Sink
Doris 作為目標（Sink）是通過 Seatunnel 的 Doris Sink 插件實現的。Seatunnel 提供了對 Doris 的內建支持，允許從多種數據源（如 Kafka、MySQL、HDFS 等）進行實時數據流式寫入
* Doris Sink 配置示例:
```
{
  "sink": {
    "name": "Doris",
    "doris": {
      "fenodes": "fe_host1:8030,fe_host2:8030",
      "table": "your_table_name",
      "database": "your_database_name",
      "user": "your_doris_user",
      "password": "your_doris_password",
      "sink_batch_size": 200000,
      "sink_max_retries": 3,
      "timeout": 30,
      "columns": [
        "column1", "column2", "column3"
      ],
      "partitioned_by": "column_name"
    }
  }
}
```
* fenodes: Doris FE 節點的地址，這是 Doris 集群的 Frontend 節點的地址列表。
* table: 目標表名，數據將被寫入這個表。
* database: Doris 中的數據庫名稱。
* user 和 password: 連接 Doris 的用戶名和密碼。
* sink_batch_size: 批量寫入的大小，控制每次寫入的行數。
* sink_max_retries: 寫入失敗後的最大重試次數。
* timeout: 超時時間設置，單位為秒。
* columns: 寫入 Doris 的列名列表，必須與 Doris 表的結構對應。
* partitioned_by: 指定根據某個列來進行數據的分區。這是可選的，但如果表有分區的需求，應配置該選項。

###  配置數據源（Source）

配置源數據通常根據實際需要來選擇合適的數據來源。例如，如果你的源數據在 Kafka 中，你需要配置 Kafka 作為 Source。
* Kafka Source 配置示例：
```
{
  "source": {
    "name": "kafka",
    "kafka": {
      "bootstrap.servers": "kafka_host1:9092,kafka_host2:9092",
      "topic": "your_topic_name",
      "group.id": "your_group_id",
      "poll_timeout_ms": 100,
      "key.deserializer": "org.apache.kafka.common.serialization.StringDeserializer",
      "value.deserializer": "org.apache.kafka.common.serialization.StringDeserializer"
    }
  }
}
```


###  完整的 Seatunnel 配置範例

綜合上述配置，這是一個從 Kafka 實時流式加載數據到 Doris 的完整 Seatunnel 配置示例：
```
{
  "source": {
    "name": "kafka",
    "kafka": {
      "bootstrap.servers": "kafka_host1:9092,kafka_host2:9092",
      "topic": "your_topic_name",
      "group.id": "your_group_id",
      "poll_timeout_ms": 100,
      "key.deserializer": "org.apache.kafka.common.serialization.StringDeserializer",
      "value.deserializer": "org.apache.kafka.common.serialization.StringDeserializer"
    }
  },
  "transform": [],
  "sink": {
    "name": "Doris",
    "doris": {
      "fenodes": "fe_host1:8030,fe_host2:8030",
      "table": "your_table_name",
      "database": "your_database_name",
      "user": "your_doris_user",
      "password": "your_doris_password",
      "sink_batch_size": 200000,
      "sink_max_retries": 3,
      "timeout": 30,
      "columns": [
        "column1", "column2", "column3"
      ],
      "partitioned_by": "column_name"
    }
  }
}
```

[TOC]

![image](https://hackmd.io/_uploads/S1k-A1v00.png)


# DORIS Data Model
[Data Model 官方文件](https://doris.apache.org/docs/table-design/data-model/overview/)
## Duplicate Key Model
DUPLICATE KEY 模型是 Doris 中的一種表模型，用來處理重複鍵值的數據。當插入具有相同 TimeStamp 和 UniqueID 的數據時，不會自動進行去重處理，而是允許重複數據的存在。
* 允許重複鍵值：
   DUPLICATE KEY 模型允許插入多條具有相同鍵值的記錄。這意味着如果兩條數據的鍵（如 TimeStamp 和 UniqueID）相同，它們依然可以同時存在於表中，不會相互覆蓋。
* 更新方式：
  與 UNIQUE KEY 不同，DUPLICATE KEY 模型不會自動進行更新。插入相同鍵值的數據時，系統只是將新數據插入表中，而不會替換已有的數據。因此，每次插入操作都會新增一條記錄，適合日誌、交易記錄等情況，這些情況下每筆記錄都應保留。
* 性能影響：
  由於允許重複的鍵值，當插入大量數據時，會造成表中存在很多重複的鍵值。這種情況下，查詢性能可能會受到影響，特別是在進行鍵值查找時。因此，在需要頻繁查詢和更新的應用中，這種模型可能不如 UNIQUE KEY 高效。
* 應用場景：
  常見應用場景包括日誌數據、監控數據或消息隊列，這些情況下每次插入的數據都是新的事件，即使具有相同的鍵值，系統也需要保留所有歷史記錄。
```
 """
        CREATE TABLE IF NOT EXISTS `${database}`.`${table}`
        (
            `TimeStamp` Datetime,
            `UniqueID` VARCHAR(255) COMMENT "UniqueID",
            ${rowtype_fields},
            MessageBody VARIANT NOT NULL COMMENT "MessageBody",
            create_time DATETIME DEFAULT CURRENT_TIMESTAMP
        ) ENGINE=OLAP
        DUPLICATE KEY(`TimeStamp`, `UniqueID`)
        PARTITION BY RANGE(`TimeStamp`)
        (
            PARTITION p202408 VALUES LESS THAN ('2024-09-01'),
            PARTITION p202409 VALUES LESS THAN ('2024-10-01')
        )
        DISTRIBUTED BY HASH(`UniqueID`) BUCKETS 5
        PROPERTIES (
            "replication_allocation" = "tag.location.default: 1",
            "storage_policy" = "test_policy",
            "min_load_replica_num" = "-1",
            "is_being_synced" = "false",
            "storage_medium" = "hdd", 
            "in_memory" = "false",
            "storage_format" = "V2",
            "inverted_index_storage_format" = "V1",
            "light_schema_change" = "true",
            "disable_auto_compaction" = "false",
            "enable_single_replica_compaction" = "false",
            "group_commit_interval_ms" = "10000",
            "group_commit_data_bytes" = "134217728"
        )"""
```
## Unique Key Model

* 唯一性約束：每個 orderedId 都是唯一的，確保數據不會重複插入。如果插入具有相同 orderedId 的數據，新的數據會覆蓋舊的數據。
* 寫入和更新：對於使用 UNIQUE KEY 的表，Doris 會自動將重複的數據進行更新處理（Upsert），這對於需要追蹤數據狀態或頻繁更新的場景非常適用。
* 分布和性能：根據 orderedId 進行哈希分布，有助於在大規模數據集上分散讀寫負載，從而提高查詢效率。

```
CREATE TABLE IF NOT EXISTS `${database}`.ORDEREDID_PK_MessageBody_data (
orderedId BIGINT,
TimeStamp Datetime,
  ${rowtype_fields},
  MessageBody VARIANT
) ENGINE=OLAP
UNIQUE KEY (orderedId)
DISTRIBUTED BY HASH (orderedId)
PROPERTIES (
  "replication_allocation" = "tag.location.default: 1",
  "in_memory" = "false",
  "storage_format" = "V2",
  "disable_auto_compaction" = "false"
)
 
```       



## Aggregate Key Model 
尚未測試


---

# Tiered Storage
## create Resource
建立minio s3的resource，作為未來冷數據預備存入的object store，
```
CREATE RESOURCE IF NOT EXISTS "remote_s3"
        PROPERTIES(
            "type"="s3",
            "s3.endpoint" = "(http://10.136.218.207:9001)",
            "s3.region" = "us-east-1",
            "s3.root.path" = "dataplatform/doris",
            "s3.access_key" = "Mivcp6lLE8G5R0bfFMZV",
            "s3.secret_key" = "${S3SK}",
            "s3.connection.maximum" = "50",
            "s3.connection.request.timeout" = "3000",
            "s3.connection.timeout" = "1000",
            "s3.bucket" = "dataplatform"
        );
```

## Create Storage Policy
建立Storage Policy 控制數據冷卻時間，可用相對或絕對的設定
* 相對時間
```
CREATE STORAGE POLICY testPolicy
PROPERTIES(
  "storage_resource" = "remote_s3",  --所使用上述建立的storage resource
  "cooldown_ttl" = "1d" --一天後冷卻
);
```
* 絕對時間
```
CREATE STORAGE POLICY testPolicyForTTlDatatime
PROPERTIES(
  "storage_resource" = "remote_s3",
  "cooldown_datetime" = "2024-09-07 21:00:00"
);
```
## 確認storage policy 狀態
```
SHOW STORAGE POLICY

Show storage policy using;
```
## 更改storage policy 冷熱時間
```
ALTER STORAGE POLICY test_policy PROPERTIES("cooldown_datetime" = "2024-09-30 00:00:00");
ALTER STORAGE POLICY test_policy PROPERTIES ("cooldown_ttl" = "1d");
```
### partition or tablet設置storage policy
```
CREATE TABLE IF NOT EXISTS `${database}`.`${table}`
        (
            `TimeStamp` Datetime,
            `UniqueID` VARCHAR(255) COMMENT "UniqueID",
            ${rowtype_fields},
            MessageBody VARIANT NOT NULL COMMENT "MessageBody",
            create_time DATETIME DEFAULT CURRENT_TIMESTAMP 
        ) ENGINE=OLAP
        DUPLICATE KEY(`TimeStamp`, `UniqueID`)
        PARTITION BY RANGE(`TimeStamp`)
        (
            PARTITION p202408 VALUES LESS THAN ('2024-09-01'),
            PARTITION p202409 VALUES LESS THAN ('2024-10-01')
        )
        DISTRIBUTED BY HASH(`UniqueID`) BUCKETS 5
        PROPERTIES (
            "replication_allocation" = "tag.location.default: 1",
            "storage_policy" = "test_policy", -- 設定storage_policy
            "min_load_replica_num" = "-1",
            "is_being_synced" = "false",
            "storage_medium" = "hdd", 
            "in_memory" = "false",
            "storage_format" = "V2",
            "inverted_index_storage_format" = "V1",
            "light_schema_change" = "true",
            "disable_auto_compaction" = "false",
            "enable_single_replica_compaction" = "false",
            "group_commit_interval_ms" = "10000",
            "group_commit_data_bytes" = "134217728"
        )      
```

假設只針對一個partition 設置policy ，只須於partition後面新增`("storage_policy" = "${policy_name}")`
```
PARTITION BY RANGE(`TimeStamp`)
        (
            PARTITION p202408 VALUES LESS THAN ('2024-09-01')("storage_policy" = "${policy_name}"),
            PARTITION p202409 VALUES LESS THAN ('2024-10-01')
        )

```

### 確認數據冷熱狀態
Tablet 資訊中區分了 LocalDataSize 和 RemoteDataSize，前者表示存儲在本地的數據，後者表示已經冷卻並移動到物件存儲上的數據。
```
show tablets from wj_c03_WorkCompleted
```
```

|TabletId|ReplicaId|BackendId|SchemaHash|Version|LstSuccessVersion|LstFailedVersion|LstFailedTime|LocalDataSize|RemoteDataSize|RowCount|State |LstConsistencyCheckTime|CheckVersion|VisibleVersionCount|VersionCount|QueryHits|PathHash            |Path                        |MetaUrl                                         |CompactionStatus                                              |CooldownReplicaId|CooldownMetaId|
|--------|---------|---------|----------|-------|-----------------|----------------|-------------|-------------|--------------|--------|------|-----------------------|------------|-------------------|------------|---------|--------------------|----------------------------|------------------------------------------------|--------------------------------------------------------------|-----------------|--------------|
|93525   |93526    |10023    |1696895087|1      |1                |-1              |             |0            |0             |0       |NORMAL|                       |-1          |1                  |1           |0        |-1629718700787670681|/opt/apache-doris/be/storage|http://10.136.219.209:8040/api/meta/header/93525|http://10.136.219.209:8040/api/compaction/show?tablet_id=93525|93526            |              |
|93527   |93528    |10023    |1696895087|1      |1                |-1              |             |0            |0             |0       |NORMAL|                       |-1          |1                  |1           |0        |-1629718700787670681|/opt/apache-doris/be/storage|http://10.136.219.209:8040/api/meta/header/93527|http://10.136.219.209:8040/api/compaction/show?tablet_id=93527|93528            |              |
|93529   |93530    |10023    |1696895087|1      |1                |-1              |             |0            |0             |0       |NORMAL|                       |-1          |1                  |1           |0        |-1629718700787670681|/opt/apache-doris/be/storage|http://10.136.219.209:8040/api/meta/header/93529|http://10.136.219.209:8040/api/compaction/show?tablet_id=93529|93530            |              |
|93531   |93532    |10023    |1696895087|1      |1                |-1              |             |0            |0             |0       |NORMAL|                       |-1          |1                  |1           |0        |-1629718700787670681|/opt/apache-doris/be/storage|http://10.136.219.209:8040/api/meta/header/93531|http://10.136.219.209:8040/api/compaction/show?tablet_id=93531|93532            |              |
|93533   |93534    |10023    |1696895087|1      |1                |-1              |             |0            |0             |0       |NORMAL|                       |-1          |1                  |1           |0        |-1629718700787670681|/opt/apache-doris/be/storage|http://10.136.219.209:8040/api/meta/header/93533|http://10.136.219.209:8040/api/compaction/show?tablet_id=93533|93534            |              |
|93535   |93536    |10023    |1696895087|2      |2                |-1              |             |6375623      |0             |47458   |NORMAL|                       |-1          |2                  |2           |0        |-1629718700787670681|/opt/apache-doris/be/storage|http://10.136.219.209:8040/api/meta/header/93535|http://10.136.219.209:8040/api/compaction/show?tablet_id=93535|93536            |              |
|93537   |93538    |10023    |1696895087|2      |2                |-1              |             |6395226      |0             |47487   |NORMAL|                       |-1          |2                  |2           |0        |-1629718700787670681|/opt/apache-doris/be/storage|http://10.136.219.209:8040/api/meta/header/93537|http://10.136.219.209:8040/api/compaction/show?tablet_id=93537|93538            |              |
|93539   |93540    |10023    |1696895087|2      |2                |-1              |             |6431337      |0             |47835   |NORMAL|                       |-1          |2                  |2           |0        |-1629718700787670681|/opt/apache-doris/be/storage|http://10.136.219.209:8040/api/meta/header/93539|http://10.136.219.209:8040/api/compaction/show?tablet_id=93539|93540            |              |
|93541   |93542    |10023    |1696895087|2      |2                |-1              |             |6358991      |0             |47310   |NORMAL|                       |-1          |2                  |2           |0        |-1629718700787670681|/opt/apache-doris/be/storage|http://10.136.219.209:8040/api/meta/header/93541|http://10.136.219.209:8040/api/compaction/show?tablet_id=93541|93542            |              |
|93543   |93544    |10023    |1696895087|2      |2                |-1              |             |6401750      |0             |47609   |NORMAL|                       |-1          |2                  |2           |0        |-1629718700787670681|/opt/apache-doris/be/storage|http://10.136.219.209:8040/api/meta/header/93543|http://10.136.219.209:8040/api/compaction/show?tablet_id=93543|93544            |              |
```



# VARIANT

## 欄位拆分與查詢
* 使用 Apache Doris 的 `VARIANT` 功能進行
在處理結構化數據時，有時一個欄位的內容以嵌套 JSON 的形式存儲，這種情況下，分析數據需要拆解欄位內部的結構。  
Apache Doris 提供了 `VARIANT` 資料類型及相關函數，方便對這類結構化數據進行處理。



### 步驟
1. 建表語句
在 Apache Doris 中，首先建立一個包含 VARIANT 類型欄位的表。此例中，表名為 CFX_WorkCompleted_autobkt，包含一個名為 MessageBody 的欄位，使用 VARIANT 類型來存儲 JSON 格式的數據。
```sql
CREATE TABLE `CFX_WorkCompleted_autobkt` (
  `TimeStamp` DATETIME NULL,
  `UniqueID` VARCHAR(255) NULL COMMENT 'UniqueID',
  `LineName` TEXT NULL,
  `MessageName` TEXT NULL,
  `Source` TEXT NULL,
  `Target` TEXT NULL,
  `RequestID` TEXT NULL,
  `MessageBody` VARIANT NOT NULL COMMENT 'MessageBody'
) ENGINE=OLAP
DUPLICATE KEY(`TimeStamp`, `UniqueID`)
PARTITION BY RANGE(`TimeStamp`)
(PARTITION p202410 VALUES [('2024-10-01 00:00:00'), ('2024-11-01 00:00:00')),
PARTITION p202411 VALUES [('2024-11-01 00:00:00'), ('2024-12-01 00:00:00')),
PARTITION p202412 VALUES [('2024-12-01 00:00:00'), ('2025-01-01 00:00:00'))
DISTRIBUTED BY HASH(`TimeStamp`) BUCKETS AUTO
PROPERTIES (
"replication_allocation" = "tag.location.default: 1",
"min_load_replica_num" = "-1",
"is_being_synced" = "false"
);
```
>  說明：
> TimeStamp 和 UniqueID 作為主鍵，並且表格根據 TimeStamp 欄位分區。
> MessageBody 欄位使用 VARIANT 類型來存儲 JSON 數據，這可以動態解析和存儲結構化的資料。
> PARTITION BY RANGE 用來將數據按時間範圍分區，有助於提高查詢效率。
> DISTRIBUTED BY HASH 表示根據 TimeStamp 欄位將數據分散到不同的節點，以平衡負載。


2. 利用streamload 將資料輸入
Apache Doris 支持多種數據載入方式，Streamload 是其中一種。這個步驟是將結構化或半結構化數據載入到 Doris 表中。可以使用 Streamload 將 JSON 數據寫入剛剛創建的表格中。
```
streamload -u http://<doris_host>:<doris_port>\
 -p <password> -d <database> -t CFX_WorkCompleted_autobkt -f <data_file_path>
```


3. 設定variant 條件
在處理 VARIANT 類型的數據時，為了正確處理並拆解 JSON 結構，需設置一些條件，特別是啟用展開嵌套結構的功能。使用 variant_enable_flatten_nested 參數來展開嵌套的陣列，並將陣列元素存儲為列。

```sql
set describe_extend_variant_column = true;  
```
使用 DESC 命令將展示如下的擴展列，是從MessageBody展開
`mysql> desc test_variant.CFX_WorkCompleted_autobkt;`
|Field|Type|Null|Key|Default|Extra|
|-----|----|----|---|-------|-----|
|TimeStamp|DATETIME|Yes|true|||
|UniqueID|VARCHAR(255)|Yes|true|||
|LineName|TEXT|Yes|false||NONE|
|MessageName|TEXT|Yes|false||NONE|
|Source|TEXT|Yes|false||NONE|
|Target|TEXT|Yes|false||NONE|
|RequestID|TEXT|Yes|false||NONE|
|MessageBody|VARIANT|No|false||NONE|
|messagebody.$type|TEXT|Yes|false||NONE|
|messagebody.HermesIdentifier|TEXT|Yes|false||NONE|
|messagebody.PrimaryIdentifier|TEXT|Yes|false||NONE|
|messagebody.Result|TEXT|Yes|false||NONE|
|messagebody.TransactionID|TEXT|Yes|false||NONE|
|messagebody.UnitCount|TINYINT|Yes|false||NONE|

> * 說明：
> 設置 describe_extend_variant_column 為 true，可讓 Doris 展示擴展後的欄位，這些欄位來自於 MessageBody 欄位中的 JSON 數據。
> 當嵌套的 JSON 數據寫入 VARIANT 類型欄位時，若設置為 true，Doris 會將 JSON 中的鍵值對展開為列，查詢時可以直接訪問每個鍵對應的值。
> 
4. 進行查詢
成功載入數據並展開 VARIANT 欄位後，可以執行 SQL 查詢來提取 MessageBody 欄位中的特定值。例如，提取 TransactionID 並與其他欄位（如 RequestID）一起查詢
```sql
select MessageBody['TransactionID']
as TransactionID, RequestID  from test_variant.CFX_WorkCompleted_autobkt; 
```

MessageBody['TransactionID'] 使用 JSON 路徑語法來提取 MessageBody 欄位中 TransactionID 的值。這是 VARIANT 類型的一個優勢，能夠輕鬆提取嵌套結構中的元素。
> 查詢結果將返回每條記錄的 TransactionID 和對應的 RequestID，這些值根據 MessageBody 中的結構來提取。

5. 查詢結果
執行查詢後，將獲得如下格式的查詢結果：

|element_at(MessageBody, 'TransactionID')|RequestID|
|----------------------------------------|---------|
|5349946a-08e2-4e4b-a2b6-eb45eb5a2144|9fd3c667-7203-4f11-a76f-b357477de28c|
|2cb5069c-c432-4d83-9dc7-04473bca2baa|2da488d2-b912-426d-9cd4-4f739dbfb997|
|3f977d66-9327-4524-993a-70720eee0162|9e7330fb-e2fc-4d8e-bcf2-2e835a4bf712|
|63b9d544-35cf-40c2-8704-40a75ce9a994|c5e917e4-02e6-44e2-bdbc-f7a3ec99190c|
|fc33785c-d451-4a66-a318-ed5ee61e7bf0|adbbccef-ea7f-4d6b-93c1-2d0d59bb96b1|

> 說明：
TransactionID 來自 MessageBody 中的嵌套 JSON 結構。
每條記錄的 TransactionID 和 RequestID 會顯示為提取出來的具體值。