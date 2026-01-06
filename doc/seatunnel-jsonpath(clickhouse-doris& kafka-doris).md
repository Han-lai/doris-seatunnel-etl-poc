# seatunnel-jsonpath(clickhouse-doris& kafka-doris)
[toc]

## jsonpath
SeaTunnel 的 JSONPath 是用於處理 JSON 結構化數據的功能。它能夠從 JSON 數據中提取特定的字段或子結構，適合在數據管道中對嵌套結構數據進行解析和轉換。

1. 功能與特性
* 字段提取
JSONPath 允許從 JSON 結構中提取特定字段，支持嵌套字段的選擇。

* 數據過濾
可以透過過濾條件選擇符合規範的 JSON 數據。

* 支援複雜路徑
支持使用 $（根節點）和 .（子節點）語法來遍歷 JSON 結構。

* 靈活範圍選擇
支援使用通配符 * 選擇所有子節點，或使用索引 [n] 選擇特定的數據項目。

2. 使用方式
* 基本配置
要使用 JSONPath，需要在 config 文件中加入以下配置項目：

```
transform {
  json_path {
    fields {
      field1 = "$.path.to.field1"
      field2 = "$.path.to.field2"
    }
  }
}
```

* 示例
假設有以下 JSON 數據：
```
{
  "user": {
    "name": "Alice",
    "details": {
      "age": 25,
      "location": "NY"
    }
  },
  "preferences": ["reading", "traveling", "coding"]
}
```


提取 user 中的 name: >> 結果: "Alice"
```field1 = "$.user.name"```
提取 details 中的 age:
```field2 = "$.user.details.age"```
提取 preferences 中的第一個項目:
```field3 = "$.preferences[0]"```
3. 使用情境
* 數據清理與標準化
處理含有嵌套結構的數據（如來自 Kafka、RabbitMQ 的消息）時，提取需要的字段並轉換為結構化表格數據。
* 數據整合
在多源數據中，提取不同數據源的字段以統一格式進行整合。
* 特定字段過濾
對大規模 JSON 數據進行過濾，只保留與業務相關的部分。

4. 功能面分析

| **優點**               | **說明**                                                  |
|------------------------|-----------------------------------------------------------|
| **靈活性高**           | 支持複雜的 JSON 結構提取，可以處理多層嵌套和動態變化的數據。     |
| **性能好**             | 適合流式處理場景，能快速解析大量 JSON 數據，適應高吞吐量環境。 |
| **語法簡單**           | 類似 XPath，語法直觀，學習曲線較低，易於上手。                 |

| **局限性**             | **說明**                                                  |
|------------------------|-----------------------------------------------------------|
| **嵌套深度的限制**     | 如果 JSON 結構過於複雜，提取配置可能難以維護和理解。           |
| **處理非標準 JSON 的挑戰** | 必須確保 JSON 數據是合法格式，否則解析會失敗。               |

5. 注意事項

| **注意事項**           | **說明**                                                  |
|------------------------|-----------------------------------------------------------|
| **JSON 格式驗證**       | 輸入數據必須是合法的 JSON 格式，否則會引發解析錯誤。         |
| **配置錯誤防範**       | 確保 JSONPath 路徑的準確性，錯誤的路徑會導致提取結果為 null。  |
| **性能問題**           | 高吞吐量環境下，頻繁的 JSONPath 操作可能增加 CPU 開銷，建議結合過濾或分片優化性能。 |
| **不支持 JSON 扁平化** | 如果需要將嵌套結構完全展開成多層表格格式，需額外工具或處理步驟。 |
| **處理特定格式的注意** | 當數據中包含陣列或非結構化部分時，需特別注意索引的使用方式。   |

----

## clickhouse-doris實作
如何使用 JSONPath 進行數據提取與轉換，並將結果寫入 Doris 資料庫。過程包括數據過濾、字段轉換、欄位篩選及資料儲存，特別針對 JSONPath 的格式要求和 Doris 資料表結構設計。

### 流程概述
1. 數據來源設定：從 ClickHouse 擷取符合條件的資料。
2.  JSONPath 轉換：從 MessageBody 提取所需的欄位並新增為表中的新欄位。
3. 欄位篩選與清理：刪除不必要的欄位，僅保留需要的數據。
4. 數據儲存：透過 Doris Sink 將處理後的數據存入 Doris 資料庫。

* ### JSONPath 欄位格式要求
在 JSONPath 的轉換過程中，每個欄位需指定來源欄位 (src_field)、提取的路徑 (path)、目標欄位名稱 (dest_field)，並滿足以下格式要求：
    * STRING: 字符串類型資料。
    * BYTES: 二進制類型資料。
    * ARRAY: 陣列類型資料。
    * MAP: 鍵值對資料。
    * ROW: 結構化數據類型。
    
* ### 原始json數據
```json
{
  "$type": "CFX.Production.UnitsArrived, CFX",
  "PrimaryIdentifier": "string",
  "HermesIdentifier": "string",
  "UnitCount": 20,
  "Units": [
    {
      "UnitIdentifier": "56",
      "PositionNumber": 1,
      "PositionName": "string",
      "X": 0.0,
      "Y": 0.0,
      "Rotation": 0.0,
      "FlipX": false,
      "FlipY": false,
      "Status": "Pass"
    },
    {
      "UnitIdentifier": "56",
      "PositionNumber": 2,
      "PositionName": "string",
      "X": 0.0,
      "Y": 0.0,
      "Rotation": 0.0,
      "FlipX": false,
      "FlipY": false,
      "Status": "Pass"
    }
  ]
}
```
* ### JSONPath 配置
以下配置專門用於提取 UnitCount 欄位：
```
transform {
  JsonPath {
    source_table_name = "CFX_Production_UnitsArrived"
    result_table_name = "jsonpath"
    row_error_handle_way = SKIP
    columns = [
      {
        "src_field" = "MessageBody"
        "path" = "$.UnitCount"
        "dest_field" = "unit_count"
        "dest_type" = "int"
      }
    ]
  }
}
```
> src_field: 指定數據來源字段，這裡是 MessageBody。
path: 使用 JSONPath 提取所需數據，$.UnitCount 表示直接取得 UnitCount 的值。
dest_field: 提取的數據存入的目標字段名稱，這裡是 unit_count。
dest_type: 定義數據類型為整數 (int)。


----
### ClickHouse 到 Doris 數據處理流程

1. 數據來源設定
從 ClickHouse 擷取符合條件的資料。以下是範例配置：

```yaml=
source {
  Clickhouse {
    host = "10.136.218.207:8123"
    database = "EAP"
    sql = """
      SELECT 
        UniqueID, 
        toString(`TimeStamp`) as `TimeStamp`, 
        LineName, 
        MessageName, 
        `Source`, 
        Target, 
        RequestID, 
        MessageBody 
      FROM PK_MessageBody_data 
      WHERE LineName = 'wj_c02' 
        AND MessageName = 'CFX.Production.UnitsArrived' 
        AND toString(`TimeStamp`) > '2024-10-13 00:00:00.000 +0000' 
        AND toString(`TimeStamp`) < '2024-10-14 00:00:00.000 +0000' 
        AND length(MessageBody) >= 5000000 
        AND UniqueID IN (
          '52b69743-1e37-4e7e-8ddc-41aa7df87114', 
          'ddbd8b55-8759-4db9-8827-c9fc27bb5b40', 
          '75d9b134-4134-413a-9e78-f672c8c198c6', 
          '308ece8b-f6f0-4bdc-a704-302e29846291'
        )
    """
    username = "default"
    password = "default"
    server_time_zone = "UTC"
    result_table_name = "CFX_Production_UnitsArrived"
    clickhouse.config = {
      "socket_timeout" = "3000000"
    }
  }
}
```
2. JSONPath 轉換與新增欄位
提取 MessageBody 的數據並新增新欄位，以下是 JSONPath 的轉換配置：
```yaml=
transform {
  JsonPath {
    source_table_name = "CFX_Production_UnitsArrived"
    result_table_name = "jsonpath"
    row_error_handle_way = SKIP
    columns = [
      {
        "src_field" = "MessageBody"
        "path" = "$.$type"
        "dest_field" = "type"
      },
      {
        "src_field" = "MessageBody"
        "path" = "$.PrimaryIdentifier"
        "dest_field" = "primary_identifier"
      },
      {
        "src_field" = "MessageBody"
        "path" = "$.HermesIdentifier"
        "dest_field" = "hermes_identifier"
      },
      {
        "src_field" = "MessageBody"
        "path" = "$.UnitCount"
        "dest_field" = "unit_count"
        "dest_type" = "int"
      },
      {
        "src_field" = "TimeStamp"
        "path" = "$"
        "dest_field" = "timestamp"
        "dest_type" = "string"
      }
    ]
  }
}
```

3. 欄位篩選與清理
移除不必要的欄位，例如 MessageBody，僅保留處理後的數據。

```
Filter {
  source_table_name = "jsonpath"
  result_table_name = "Filter_jsonpath"
  exclude_fields = [MessageBody]
}
```
4. 數據儲存至 Doris
將清理後的數據寫入 Doris 資料庫，並確保欄位符合 JSONPath 的轉換結果。表結構設計如下：
```yaml=
sink {
  Doris {
    source_table_name = "Filter_jsonpath_sql"
    doris.batch.size = 1024
    fenodes = "10.136.147.130:8030"
    username = "root"
    password = ""
    database = "test_variant"
    table = "jsonpath_CFX_Production_UnitsArrived_unit"
    sink.label-prefix = "jsonpath"
    sink.enable-delete = "true"
    schema_save_mode = "CREATE_SCHEMA_WHEN_NOT_EXIST"
    save_mode_create_template = """
    CREATE TABLE IF NOT EXISTS `${database}`.`${table}` (
      UniqueID varchar(255) NULL,
      `TimeStamp` Datetime  NOT NULL,
      LineName string NULL, 
      MessageName string NOT NULL, 
      Source string NULL,
      Target string NULL,
      RequestID string NULL,
      `type` string NOT NULL, 
      primary_identifier string NULL,
      hermes_identifier string NULL,
      unit_count int NULL
    ) ENGINE=OLAP
    UNIQUE KEY (UniqueID)
    DISTRIBUTED BY HASH (UniqueID)
    PROPERTIES (
      "replication_allocation" = "tag.location.default: 1",
      "in_memory" = "false",
      "storage_format" = "V2",
      "disable_auto_compaction" = "false"
    )
    """
    doris.config {
      format = "json"
      read_json_by_line = "true"
    }
  }
}
```
* ### 資料EL完成

```log
2024-11-18 06:40:57,105 INFO  [o.a.s.c.d.s.w.DorisStreamLoad ] [st-multi-table-sink-writer-2] - load Result {
    "TxnId": 17243,
    "Label": "jsonpath_test_variant_jsonpath_CFX_Production_UnitsArrived_unit_1118_910781399009591297_0_1731912037904",
    "Comment": "",
    "TwoPhaseCommit": "false",
    "Status": "Success",
    "Message": "OK",
    "NumberTotalRows": 4,
    "NumberLoadedRows": 4,
    "NumberFilteredRows": 0,
    "NumberUnselectedRows": 0,
    "LoadBytes": 1659,
    "LoadTimeMs": 6725,
    "BeginTxnTimeMs": 9,
    "StreamLoadPutTimeMs": 6,
    "ReadDataTimeMs": 0,
    "WriteDataTimeMs": 6674,
    "CommitAndPublishTimeMs": 34
}
```

```
| **欄位名稱**         | **定義**                              | **用途/取值**                                                                 |
|----------------------|-------------------------------------|-------------------------------------------------------------------------------|
| **TxnId**            | 本次加載任務的事務 ID                 | 唯一標識 Stream Load 任務。                                                   |
| **Label**            | 本次加載任務的標籤                    | 區分任務，可自動生成或由用戶指定。                                            |
| **Comment**          | 任務的附加說明                       | 通常為空。                                                                   |
| **TwoPhaseCommit**   | 是否使用兩階段提交                    | `true`: 使用兩階段提交。<br>`false`: 單階段提交。                             |
| **Status**           | 加載任務的執行狀態                    | `Success`: 加載成功。<br>`Fail`: 加載失敗。                                   |
| **Message**          | 任務結果訊息                         | 描述執行結果，例如 "OK" 表示成功。                                            |
| **NumberTotalRows**  | 本次加載的總行數                      | 包含所有嘗試加載的行數。                                                      |
| **NumberLoadedRows** | 成功加載的行數                        | 表示實際成功寫入的行數。                                                      |
| **NumberFilteredRows** | 被過濾的行數                         | 未成功加載的行數（例如資料格式錯誤）。                                        |
| **NumberUnselectedRows** | 未被選中的行數                     | 加載過程中未選中的行數（例如不符合條件）。                                     |
| **LoadBytes**        | 加載的數據量（字節）                   | 本次加載的總數據量，以字節為單位。                                            |
| **LoadTimeMs**       | 總加載時間（毫秒）                    | 包括整個加載過程所花費的時間。                                                |
| **BeginTxnTimeMs**   | 開始事務所花時間（毫秒）               | 初始化事務的耗時。                                                            |
| **StreamLoadPutTimeMs** | 傳輸數據所花時間（毫秒）             | 數據傳輸至 Doris 的耗時。                                                     |
| **ReadDataTimeMs**   | 讀取數據所花時間（毫秒）               | Doris 讀取輸入數據的耗時。                                                    |
| **WriteDataTimeMs**  | 寫入數據所花時間（毫秒）               | 數據寫入 Doris 的耗時。                                                       |
| **CommitAndPublishTimeMs** | 提交並發佈數據所花時間（毫秒）     | 提交事務及數據生效的耗時。                                                    |
```

### doris 呈現結果

![](/uploads/upload_7e13e30a489ac915ebec691e12fac499.png)


----



## kafka-doris實作
SeaTunnel 是一個高效能的數據傳輸引擎，支持批處理模式，允許用戶在不同的數據源和目標之間進行數據處理和轉換。在
數據從 Kafka 讀取，經過轉換後，寫入到 Doris 數據庫。

### 流程概述
1. 配置概述
Source：Kafka，從 Kafka 主題中讀取數據。
Transform：進行數據轉換，使用 JSONPath 和 SQL 進行數據處理。
Sink：Doris，將處理後的數據存儲到 Doris。

### Kafka 到 Doris 數據處理流程
1. 環境配置 (env)
這是配置文件的起始部分，定義了並行度、作業模式、檢查點間隔等參數：
1. 數據來源設定 (從 Kafka 擷取資料)
```
env {
  parallelism = 1
  job.mode = "BATCH"
  checkpoint.interval = 600000
}
```


2. 資料源配置 (source)
這是 Kafka 資料源的配置，包括指定 Kafka topic、伺服器、以及使用的 JSON 格式和表結構
```yaml=
source {
  Kafka {
    result_table_name = "fake"  # 存儲 Kafka 資料的臨時表名
    schema = {
      fields {
        OWNER = string
        TABLE = string
        OP = string
        scn = string
        train_id = string
        train_seq = string
        rowid = string
        load_seq = string
        DBNAME = string
        columnInfo = string # 其中具有其他欄位資訊後續用jsonpath解析
      }
    } 
    format = json  # 資料格式為 JSON
    topic = "MES-IT__WJIAMES__WJ_IA__POC__R_SN_CNF_T"  # Kafka topic
    bootstrap.servers = "10.146.192.81:9092,10.146.192.82:9092,10.146.192.83:9092"  # Kafka 伺服器地址
    kafka.config = {
      max.poll.records = 1000
      auto.offset.reset = "earliest"
      security.protocol = SASL_PLAINTEXT
      sasl.mechanism = PLAIN
      sasl.jaas.config = "org.apache.kafka.common.security.scram.ScramLoginModule required username=\"MFG_DC\" password=\"MFG$DC0924\";"
    }
  }
}

```


3. 資料轉換配置 (transform)
在資料轉換階段， JsonPath 和 Sql 兩種轉換方法：

* JsonPath 轉換
    JsonPath 轉換用於解析 JSON 格式的資料，並從中提取特定的欄位。這通常用於處理結構化的 JSON 資料，從而將它轉換為關聯式資料庫表格中可以使用的格式。

    * 主要功能：
        * 資料解析：從 JSON 格式的資料中提取指定的字段，並將它們轉換為對應的表結構欄位。
        * 靈活的欄位映射：從原始 JSON 資料中提取哪些字段，以及將這些字段轉換成的目標欄位名稱。

```yaml=
transform {
  JsonPath {
    source_table_name= "fake"  # 指定來源表格名稱，即 Kafka 資料
    result_table_name = "fake_trans"  # 指定轉換後的結果表格名稱
    row_error_handle_way = SKIP  # 設定錯誤行的處理方式，這裡選擇跳過錯誤行
    columns = [
      {
        "src_field" = "columnInfo"
        "path" = "$.SERIAL_NUMBER"  # 使用 JSONPath 來提取 SERIAL_NUMBER 欄位
        "dest_field" = "columnInfo_serial_number"  # 將提取的資料放到新的欄位中
      },
      {
        "src_field" = "columnInfo"
        "path" = "$.MO_NUMBER"  # 提取 MO_NUMBER 欄位
        "dest_field" = "columnInfo_mo_number"
      },
      {
        "src_field" = "columnInfo"
        "path" = "$.MODEL_NAME"  # 提取 MODEL_NAME 欄位
        "dest_field" = "columnInfo_model_name"
      },
      {
        "src_field" = "columnInfo"
        "path" = "$.LINE_NAME"  # 提取 LINE_NAME 欄位
        "dest_field" = "columnInfo_line_name"
      }
    ]
  }
}
```

*  SQL 轉換
SQL 轉換方法用於對資料進行更多的處理和過濾，例如根據 SQL 查詢來轉換資料，選擇性地提取、過濾、重命名欄位，或進行一些數據的聚合、過濾等操作。這通常在資料處理流程中對資料做更高級的處理後，進行最終的轉換和整理。

    * 主要功能：
        * SQL 查詢處理：透過 SQL 查詢來選擇資料、轉換欄位，甚至做數據的聚合或過濾。
        * 避免資料遺失：使用 IFNULL 等函數來處理缺失的資料，保證資料的一致性

```yaml=
transform {
  Sql {
    source_table_name= "fake_trans"  # 指定來源表格名稱，即從 JsonPath 轉換來的表格
    result_table_name = "fake_trans_sql"  # 轉換後的結果表格名稱
    query = """
      select 
        IFNULL(scn, '') as scn,
        IFNULL(train_id, '') as train_id,
        IFNULL(train_seq, '') as train_seq,
        IFNULL(OWNER, '') as owner,
        IFNULL(TABLE, '') as table_name,  -- 避免與關鍵字衝突
        IFNULL(OP, '') as op,
        IFNULL(rowid, '') as rowid,
        IFNULL(load_seq, '') as load_seq,
        IFNULL(DBNAME, '') as dbname,
        IFNULL(columnInfo_serial_number, '') as columnInfo_serial_number,
        IFNULL(columnInfo_mo_number, '') as columnInfo_mo_number,
        IFNULL(columnInfo_model_name, '') as columnInfo_model_name,
        IFNULL(columnInfo_line_name, '') as columnInfo_line_name
      from fake_transformed  # 從轉換後的表格中提取資料
    """
  }
}
```

4. 資料目標配置 (sink)
最後，資料將存儲到 Doris 中，配置中包括了資料表名稱、Doris 連接資訊、批量大小等參數：

```yaml=
sink {
  Doris {
    source_table_name= "fake_trans_sql"  # 來源表
    result_table_name = "fake_doris"  # 目標 Doris 表名
    doris.batch.size = 1024
    fenodes = "10.136.147.130:8030"  # Doris FE 節點
    username = "root"
    password = ""
    database = "test_variant"
    table = "jsonpath_wj_c11_wjadpmes__wj_ia__poc__r_sn_cnf_t"
    sink.label-prefix = "wj-json"
    sink.enable-delete = "true"
    schema_save_mode = "CREATE_SCHEMA_WHEN_NOT_EXIST"
    save_mode_create_template = """
    CREATE TABLE IF NOT EXISTS test_variant.jsonpath_wj_c11_wjadpmes__wj_ia__poc__r_sn_cnf_t (
    scn VARCHAR(255) NOT NULL,
    train_id VARCHAR(255)   NULL,
    train_seq VARCHAR(255)   NULL,
    owner VARCHAR(255) NOT  NULL,
    table_name VARCHAR(255)  NOT NULL,
    op VARCHAR(255) NOT NULL,
    rowid VARCHAR(255) NOT   NULL,
    load_seq VARCHAR(255)  NOT  NULL,
    dbname VARCHAR(255) NOT  NULL,
    columnInfo_serial_number VARCHAR(255)  NOT NULL,
    columnInfo_mo_number VARCHAR(255)  NOT NULL,
    columnInfo_model_name VARCHAR(255) NOT NULL,
    columnInfo_line_name VARCHAR(255) NOT  NULL
    ) ENGINE=OLAP
    UNIQUE KEY (scn)
    DISTRIBUTED BY HASH (scn)
    PROPERTIES (
    "replication_allocation" = "tag.location.default: 1",
    "in_memory" = "false",
    "storage_format" = "V2",
    "disable_auto_compaction" = "false"
    )"""
    doris.config {
      format = "json"
      read_json_by_line = "true"
    }
  }
}

```
### doris 呈現結果
![](/uploads/upload_8e6134944340be3efcb9b3f4f3ca2901.png)
