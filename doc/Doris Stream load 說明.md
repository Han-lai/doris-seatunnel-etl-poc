# Doris Stream load 說明
[TOC]

會議結論 : 
seatunel streamload 的方式要測10g資料量 (看有沒有接csv的)
kafka -> seatunnel -> doris
clickhouse的pkmessage(cfx data 轉為用seatunnel接)

## Stream Load 
### 10G資料量測試
#### 建立用於存儲數據的資料表
```
DUPLICATE KEY(id)：根據 id 欄位進行去重。
DISTRIBUTED BY HASH(id)：使用 id 欄位作為分桶鍵。
BUCKETS 2：設置資料分佈為 2 個分桶。
storage_format = V2：啟用新的存儲格式，提升性能。
```
```
CREATE TABLE large_table (
    id INT NOT NULL,
    name VARCHAR(8),
    age INT,
    city VARCHAR(6),
    country VARCHAR(6),
    email VARCHAR(255),
    phone VARCHAR(15),
    salary DECIMAL(10, 2)
) 
ENGINE=OLAP
DUPLICATE KEY(id)
COMMENT 'Large table for storing generated data'
DISTRIBUTED BY HASH(id) BUCKETS 2
PROPERTIES (
    "replication_allocation" = "tag.location.default: 1",
    "storage_format" = "V2"
);

```

#### Stream Load 操作
使用 curl 命令將 CSV 格式的資料上傳至 Doris
```
-u root:：使用 root 使用者無密碼登入 Doris。
-T ./large_data.csv：上傳的資料檔案為 large_data.csv。
-H "group_commit: async_mode"：啟用非同步模式以提高寫入性能。
-H "column_separator: ,"：指定資料列分隔符為逗號（,）。
-H "timeout: 3000"：設定超時時間為 3000 秒。
-X PUT：使用 PUT 請求上傳資料。

```
```
curl --location-trusted -u root: \
    -T ./large_data.csv \
    -H "Expect: 100-continue" \
    -H "group_commit: async_mode" \
    -H "column_separator: ," \
    -H "timeout: 3000" \
    -X PUT http://10.136.219.209:8040/api/test_variant/large_table/_stream_load

```

確認 Stream Load 狀態
```
show stream load from test_variant;
```


| Label                                    | Db          | Table       | ClientIp        | Status  | Message | Url                                                                                                               | TotalRows | LoadedRows | FilteredRows | UnselectedRows | LoadBytes   | StartTime                    | FinishTime                   | User | Comment |
|------------------------------------------|-------------|-------------|-----------------|---------|---------|-------------------------------------------------------------------------------------------------------------------|-----------|------------|--------------|----------------|-------------|------------------------------|------------------------------|------|---------|
| group_commit_1740d7c82273eac9_6ca0ea5a2f6810ac | test_variant | large_table | 10.136.48.178   | Success | OK      | [Load Error Log](http://10.136.219.209:8040/api/_load_error_log?file=__shard_3/error_log_insert_stmt_fa45764357760d96-8b8995033114b99_fa45764357760d96_8b8995033114b99) | 20000001  | 20000000   | 1            | 0              | 1486888611  | 2024-10-08 03:08:48.514    | 2024-10-08 03:09:22.278    | root |         |
| group_commit_8840f6209bff80ff_71ec3d05b5b70fb5 | test_variant | large_table | 10.136.48.178   | Success | OK      | [Load Error Log](http://10.136.219.209:8040/api/_load_error_log?file=__shard_4/error_log_insert_stmt_a24777e34a1f13e0-36311174e309c095_a24777e34a1f13e0_36311174e309c095) | 40000001  | 40000000   | 1            | 0              | 2984886991  | 2024-10-08 06:05:36.955    | 2024-10-08 06:06:43.793    | root |         |
| group_commit_1d40d5e61d666aaf_60264454482b02ab | test_variant | large_table | 10.136.48.178   | Success | OK      | [Load Error Log](http://10.136.219.209:8040/api/_load_error_log?file=__shard_5/error_log_insert_stmt_5948f68d67e7858f-591bdf85fa9a6bba_5948f68d67e7858f_591bdf85fa9a6bba) | 40000001  | 40000000   | 1            | 0              | 2984886991  | 2024-10-08 06:46:33.301    | 2024-10-08 06:47:40.320    | root |         |

```
1. 資料格式：請確認 CSV 檔案的列數和順序與資料表的 schema 一致，否則導入會失敗。
2. 權限配置：使用 Stream Load 時，需要有相應的資料表寫入權限。
3. 性能優化：建議在大規模資料載入前啟用異步模式（async_mode）及合理配置 BUCKETS 數量。
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
![image](https://hackmd.io/_uploads/BJhCWrc1kg.png)


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

* 

---
* 不同partition可以掛不同的policy，需要另外設定
```
ALTER TABLE my_table MODIFY PARTITION p1 SET ("storage_policy" = "POLICY_TEST1")
ALTER TABLE my_table MODIFY PARTITION p2 SET ("storage_policy" = "POLICY_TEST2")
```

---

```
 
# Set the basic configuration of the task to be performed
env {
  parallelism = 1
  job.mode = "BATCH"
}
source {
  Clickhouse {
    host = "10.136.218.207:8123"
    database = "EAP"
    sql = "SELECT * FROM PK_MessageBody_data WHERE MessageName = 'CFX.Production.WorkCompleted' and LineName ='wj_c03'"
    username = "default"
    password = "default"
    server_time_zone = "UTC"
    clickhouse.config = {
      "socket_timeout" = "300000"
    }
  }
}
sink {
    Doris {
        fenodes = "10.136.147.130:8030"
        username = "root"
        password = ""
        database = "test_variant"
        schema_save_mode = "CREATE_SCHEMA_WHEN_NOT_EXIST"
        table = "CFX_WorkCompleted_autobkt"
        data_save_mode = "APPEND_DATA"
        sink.enable-2pc = "true"
        sink.label-prefix = "CFX_autobkt"
        save_mode_create_template = """
        CREATE TABLE IF NOT EXISTS `${database}`.`${table}`
        (
            `TimeStamp` Datetime,
            `UniqueID` VARCHAR(255) COMMENT "UniqueID",
            ${rowtype_fields},
            MessageBody VARIANT NOT NULL COMMENT "MessageBody"
        ) ENGINE=OLAP
        DUPLICATE KEY(`TimeStamp`, `UniqueID`)
        PARTITION BY RANGE(`TimeStamp`)
        (
            PARTITION p202408 VALUES LESS THAN ('2024-09-01'),
            PARTITION p202409 VALUES LESS THAN ('2024-10-01'),
            PARTITION p202410 VALUES LESS THAN ('2024-11-01')
        )
        DISTRIBUTED BY HASH(`TimeStamp`) BUCKETS AUTO
        PROPERTIES (
            "dynamic_partition.enable" = "true",
            "dynamic_partition.time_unit" = "MONTH",
            "dynamic_partition.start" = "-2",
            "dynamic_partition.end" = "2",
            "dynamic_partition.prefix" = "p",
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
        doris.config = {
            format = "json"
            read_json_by_line = "true"
        }
    }
}
```

```
# Set the basic configuration of the task to be performed
env {
  parallelism = 1
  job.mode = "BATCH"
}
source {
  Clickhouse {
    host = "10.136.218.207:8123"
    database = "EAP"
    sql = "SELECT * FROM PK_MessageBody_data WHERE MessageName = 'CFX.Production.WorkCompleted' and LineName ='wj_c02'"
    username = "default"
    password = "default"
    server_time_zone = "UTC"
    clickhouse.config = {
      "socket_timeout" = "300000"
    }
  }
}
sink {
    Doris {
        fenodes = "10.136.147.130:8030"
        username = "root"
        password = ""
        database = "test_variant"
        schema_save_mode = "CREATE_SCHEMA_WHEN_NOT_EXIST"
        table = "CFX_WorkCompleted_autobkt"
        data_save_mode = "APPEND_DATA"
        sink.enable-2pc = "true"
        sink.label-prefix = "ttl_test"
 
        doris.config = {
            format = "json"
            read_json_by_line = "true"
        }
    }
}
```




---
* 測試單一partation單一policy
* 動態分區不先寫好partition
--
不先寫好partition的話，資料會進不去
![image](https://hackmd.io/_uploads/H1HFLIqkJe.png)

seatunnel
(load資料有問題，但建立表格沒問題)






## 20241016

將不同line 分開傳送
c03的資料傳遞成功

![image](https://hackmd.io/_uploads/ryTgCA3J1x.png)

在BE CONF裡新增調整
增加LOAD進去的資料量限制
```
streaming_load_max_mb = 30000
```
![image](https://hackmd.io/_uploads/SJqz0C31yl.png)


| Label                                                      | Db           | Table        | ClientIp        | Status  | Message | Url | TotalRows | LoadedRows | FilteredRows | UnselectedRows | LoadBytes | StartTime               | FinishTime              | User | Comment |
|------------------------------------------------------------|--------------|--------------|----------------|---------|---------|-----|-----------|------------|--------------|----------------|-----------|------------------------|------------------------|------|---------|
| pkmsg_autobkt_c11_variant_pkmsg_autobkt_898809467796193281_0_1 | test_variant | pkmsg_autobkt | 10.136.147.129 | Success | OK      | N/A | 9742329   | 9742329    | 0            | 0              | 11490695265( 11.49 GB) | 2024-10-16 05:47:59.353 | 2024-10-16 05:52:41.541 | root |         |
| pkmsg_autobkt_c03_test_variant_pkmsg_autobkt_898827827095273473_0_1 | test_variant | pkmsg_autobkt | 10.136.147.129 | Success | OK      | N/A | 4182745   | 4182745    | 0            | 0              | 3889806884(約 3.89 GB)  | 2024-10-16 07:01:09.393 | 2024-10-16 07:04:24.907 | root |         |
