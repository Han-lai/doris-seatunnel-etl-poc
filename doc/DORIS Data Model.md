
[TOC]

![](/uploads/upload_170e4572c12e4189abc0c15950236a7f.png)


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
