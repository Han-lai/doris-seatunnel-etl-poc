# seatunnel kafka 問題描述

## Topic: wj_adp__poc__r_sn_cnf_t
- 這個 topic 只有 `op = U`（更新操作）訊息，並且包含 `columnsAfter` 和 `columnsBefore` 欄位內容。


## Topic: wj_ia__poc__r_sn_cnf_t
- 這個 topic 既有 `op = I`（插入操作）訊息，也有 `op = U`（更新操作）訊息。
- 當 `op = I` 時，欄位資料位於 `columnInfo` 中。
- 當 `op = U` 時，欄位資料分別位於 `columnsBefore` 和 `columnsAfter` 中。

存入doris，部分欄位缺失
![](/uploads/upload_5fe83ba76f65043a124eca8e8865f48c.png)

之前用clickhouse去接收kafka，也是部分欄位缺失。
![](/uploads/upload_ffbd931a775954beb4458d8c238413a0.png)

## 消息範例
在同一個topic 當中，具有兩種不同的json結構
1. **`op = I` 訊息範例（插入）**:
```json
{
 "OWNER": "WJ_IA",
 "TABLE": "R_SN_CNF_T",
 "OP": "I",
 "scn": "881095128632",
 "train_id": "881095128632",
 "train_seq": "310151170",
 "rowid": "AAA6y2ADZAALKIUAA8",
 "load_seq": "8729546578",
 "DBNAME": "WJIAMES",
 "columnInfo": {
   "SERIAL_NUMBER": "5BV2P5N0W24500016",
   "MO_NUMBER": "36124044767",
   "MODEL_NAME": "25B-V2P5N104",
   "LINE_NAME": "D-ASSY-03"
 }
}
```

2. **`op = U` 訊息範例（更新）**:
 ```json
{
  "OWNER": "WJ_IA",
  "TABLE": "R_SN_CNF_T",
  "OP": "U",
  "scn": "881093575378",
  "train_id": "881093575378",
  "train_seq": "310124756",
  "rowid": "AAA6y2ADYAAJA9NAAy",
  "load_seq": null,
  "DBNAME": "WJIAMES",
  "columnsAfter": {
    "SERIAL_NUMBER": "015EL43WW24500737",
    "MO_NUMBER": "36124041842",
    "MODEL_NAME": "VFD015EL43W",
    "LINE_NAME": "D-FINISH-PACK3"
  },
  "columnsBefore": {
    "SERIAL_NUMBER": "015EL43WW24500737",
    "MO_NUMBER": "36124041842",
    "MODEL_NAME": "VFD015EL43W",
    "LINE_NAME": "D-FINISH-PACK3"
  }
}
```
## 目前問題
* Topic: wj_ia__poc__r_sn_cnf_t
    * 在處理資料時，我們發現部分欄位的資料未成功進入 Doris，但 Kafka source 中已有該欄位的值，並且先前從 ClickHouse 抓取資料時也發現欄位值缺失。

* 具體情況如下： 
    * 當 op = I（插入操作）時，欄位資料會位於 columnInfo 中。

| kafka souce| doris db| clickhouse |
| -------- | -------- | -------- |
| ![](/uploads/upload_ba917f2123c09eeb73706a7339b0af5a.png)     | -  | ![](/uploads/upload_41a91adfb47bb1b157b467679a7766b7.png)|



## 解決方案
Topic: wj_ia__poc__r_sn_cnf_t
各設置不同的CONFIG，設定不同的Pipeline去跑
1. 提取op =I 
*     確認欄位格式，提取columnInfo
2. 提取OP= U
*     提取columnsAfter

    



---
```
頂層字段資料型別檢查結果:
  - Key: OWNER, Value: WJ_IA, Type: str
  - Key: TABLE, Value: R_SN_CNF_T, Type: str
  - Key: OP, Value: U, Type: str
  - Key: scn, Value: 881404913304, Type: str
  - Key: train_id, Value: 881404913304, Type: str
  - Key: train_seq, Value: 314072567, Type: str
  - Key: rowid, Value: AAA6y2ADaAALTzjAAH, Type: str
  - Key: load_seq, Value: None, Type: NoneType #--------------------這個無值
  - Key: DBNAME, Value: WJIAMES, Type: str
  - Key: columnsAfter, Type: dict (進一步檢查內容...)
      - Key: SERIAL_NUMBER, Value: E30421E0W24500165, Type: str
      - Key: MO_NUMBER, Value: 36124045991, Type: str
      - Key: MODEL_NAME, Value: ASD-E3-0421-E, Type: str
      - Key: LINE_NAME, Value: D-FINISH-PACK4, Type: str
  - Key: columnsBefore, Type: dict (進一步檢查內容...)
      - Key: SERIAL_NUMBER, Value: E30421E0W24500165, Type: str
      - Key: MO_NUMBER, Value: 36124045991, Type: str
      - Key: MODEL_NAME, Value: ASD-E3-0421-E, Type: str
      - Key: LINE_NAME, Value: D-ASSY-02, Type: str```

```
```
頂層字段資料型別檢查結果:
  - Key: OWNER, Value: WJ_IA, Type: str
  - Key: TABLE, Value: R_SN_CNF_T, Type: str
  - Key: OP, Value: I, Type: str
  - Key: scn, Value: 881404944286, Type: str
  - Key: train_id, Value: 881404944286, Type: str
  - Key: train_seq, Value: 314073350, Type: str
  - Key: rowid, Value: AAA6y2ADZAALKKpAAX, Type: str
  - Key: load_seq, Value: 8733468758, Type: str
  - Key: DBNAME, Value: WJIAMES, Type: str
  - Key: columnInfo, Type: dict (進一步檢查內容...)
      - Key: SERIAL_NUMBER, Value: SPXT7X058190, Type: str
      - Key: MO_NUMBER, Value: 19724529780, Type: str
      - Key: MODEL_NAME, Value: 5503229202, Type: str
      - Key: LINE_NAME, Value: D-HI-L02A, Type: str
```


##

解決方案

![](/uploads/upload_ed77fdb818c1d615ecb3a00e97794e47.png)
## Topic: wj_adp__poc__r_sn_cnf_t
- 這個 topic 只有 `op = U`（更新操作）訊息，並且包含 `columnsAfter` 和 `columnsBefore` 欄位內容。


## Topic: wj_ia__poc__r_sn_cnf_t
- 這個 topic 有 `op = U`（更新操作）訊息及`op = U`(插入操作)，並且包含`columnsINFO `columnsAfter` 和 `columnsBefore` 欄位內容。





-- 1. KAFKA DORIS LOAD(DORIS原生)
-- 2. ORACLE的資料接收(JDBC 的CREATE)
-- 3. ORACLE 接到DORIS (STREAMING有空在測)

-- APACHE RANGER DATA MASKING


# eap kafka 
# Kafka、ClickHouse、SeaTunnel 和 Doris 資料處理流程

## 整體流程概述
1. **資料來源與整合**：
   - 將 EAP Kafka 資料利用 ClickHouse 搬移至 AIT Kafka。
   - 整合四個不同的 Topic 到 ClickHouse 的同一張表：`eap_cfx_cfx_production_workcompleted_mergetree`。
   - 利用 Materialized View 將資料傳輸至 AIT Kafka 的 Topic：`CFX_CFX_WORKCOMPLETE`。

2. **SeaTunnel 資料處理與傳輸**：
   - SeaTunnel 接收 AIT Kafka 的 `CFX_CFX_WORKCOMPLETE` Topic。
   - 處理 JSON 資料，解決嵌套 JSON 的問題（目前分兩次 JSONPath 處理，尚在尋找最佳解）。

3. **Doris 資料存儲**：
   - SeaTunnel 將處理後的內容傳送到 Doris 中的表 `ods_eap_workcomplete`。

---

## SeaTunnel  資料處理與傳輸

### 環境設定
```plaintext
env {
  parallelism = 1
  job.mode = "STREAMING"
  checkpoint.interval = 6000
}
```
## source 配置
從AIT KAFKA 收取資訊
```
source {
  Kafka {
    result_table_name = "kafka_source"
    schema = {
      fields {
       receiveat= String,
       MessageID= String,
       MessageType= String,
       MessageVersion= String,
       MessageTime= String,
       Sender= String,
       Data= String
      } 
    }
    format = json
    topic = "CFX_CFX_Production_WorkCompleted"
    bootstrap.servers = "10.136.218.207:9092"
    kafka.config = {
      max.poll.records = 1000
      auto.offset.reset = "earliest"
      security.protocol = PLAINTEXT
      sasl.mechanism = PLAIN
    }
  }  
}
```

## 進行第一次JSON PATH
資訊大多於Data當中，因為json path 二次嵌套會造成error
第一次以meta 、rawdata欄位資料為主
```
JsonPath {
  source_table_name= "kafka_source"
  result_table_name = "trans_json"
  row_error_handle_way = SKIP
  columns = [
    { "src_field" = "Data", "path" = "$.ProcessedTime", "dest_field" = "ProcessedTime" },
    { "src_field" = "Data", "path" = "$.Meta.DeviceID", "dest_field" = "Meta_DeviceID" },
    { "src_field" = "Data", "path" = "$.Meta.LineID", "dest_field" = "Meta_LineID" },
    ...
  ]
}
```
## 第二次json path
將第一次jsonpath後的資訊，再進行parsing
將MessageBody的內容解析出來
```
JsonPath {
  source_table_name= "trans_json_sql"
  result_table_name = "trans_msg"
  row_error_handle_way = SKIP
  columns = [
    { "src_field" = "RawData_MessageBody", "path" = "$.TransactionID", "dest_field" = "TransactionID" },
    ...
  ]
}
```

## 取得所有欄位資訊
```
Sql {
  source_table_name= "trans_msg"
  result_table_name = "trans_msg_sql"
  query = """
    SELECT
      RawData_UniqueID,
      RawData_RequestID,
      ProcessedTime,
      Type,
      TransactionID,
      ...
    FROM trans_msg
  """
}
```

## Doris 資料存儲
```

sink {
  Doris {
    source_table_name= "trans_msg_sql"
    result_table_name = "sink_doris"
    doris.batch.size = 1024
    fenodes = "10.136.147.130:8030"
    username = "root"
    password = ""
    database = "dataplatform"
    table = "ods_eap_workcomplete"
    sink.label-prefix = "ods_eap_dp"
    sink.enable-delete = "true"
    schema_save_mode = "CREATE_SCHEMA_WHEN_NOT_EXIST"
    data_save_mode = "APPEND_DATA"
    save_mode_create_template = """
    CREATE TABLE IF NOT EXISTS `dataplatform`.`ods_eap_workcomplete` (
      RawData_UniqueID VARCHAR(255) NULL,
      RawData_RequestID VARCHAR(255) NULL,
      ProcessedTime DATETIME NULL,
      ...
    )
    ENGINE=OLAP
    UNIQUE KEY(`RawData_UniqueID`, `RawData_RequestID`, `ProcessedTime`)
    PARTITION BY RANGE(`ProcessedTime`) (
      PARTITION p202410 VALUES [('2024-10-01 00:00:00'), ('2024-11-01 00:00:00')],
      ...
    )
    DISTRIBUTED BY HASH(`RawData_UniqueID`) BUCKETS AUTO
    PROPERTIES (
      "replication_allocation" = "tag.location.default: 1",
      ...
    )
    """
  }
}
```

## 遇到的問題
嵌套 JSON 的處理：
JSONPath 嵌套部分需分兩次處理，尚未找到最佳解。
![](/uploads/upload_8ffe50ce80573c1d767e620f2b6b1473.png)
```2024-12-20 02:51:33,307 WARN  [o.a.s.e.s.TaskExecutionService] [BlockingWorker-TaskGroupLocation{jobId=922320221459447809, pipelineId=1, taskGroupId=30000}] - [seatunnel]:5801 [seatunnel] [5.1] Exception in org.apache.seatunnel.engine.server.task.SourceSeaTunnelTask@3530ff42
org.apache.seatunnel.connectors.seatunnel.kafka.exception.KafkaConnectorException: ErrorCode:[KAFKA-06], ErrorDescription:[Kafka failed to consume data]
	at org.apache.seatunnel.connectors.seatunnel.kafka.source.KafkaSourceReader.lambda$pollNext$4(KafkaSourceReader.java:216) ~[?:?]
	at java.lang.Iterable.forEach(Iterable.java:75) ~[?:1.8.0_342]
	at org.apache.seatunnel.connectors.seatunnel.kafka.source.KafkaSourceReader.pollNext(KafkaSourceReader.java:125) ~[?:?]
	at org.apache.seatunnel.engine.server.task.flow.SourceFlowLifeCycle.collect(SourceFlowLifeCycle.java:156) ~[seatunnel-starter.jar:2.3.7]
	at org.apache.seatunnel.engine.server.task.SourceSeaTunnelTask.collect(SourceSeaTunnelTask.java:127) ~[seatunnel-starter.jar:2.3.7]
	at org.apache.seatunnel.engine.server.task.SeaTunnelTask.stateProcess(SeaTunnelTask.java:168) ~[seatunnel-starter.jar:2.3.7]
	at org.apache.seatunnel.engine.server.task.SourceSeaTunnelTask.call(SourceSeaTunnelTask.java:132) ~[seatunnel-starter.jar:2.3.7]
	at org.apache.seatunnel.engine.server.TaskExecutionService$BlockingWorker.run(TaskExecutionService.java:717) ~[seatunnel-starter.jar:2.3.7]
	at org.apache.seatunnel.engine.server.TaskExecutionService$NamedTaskWrapper.run(TaskExecutionService.java:1039) ~[seatunnel-starter.jar:2.3.7]
	at java.util.concurrent.Executors$RunnableAdapter.call(Executors.java:511) ~[?:1.8.0_342]
	at java.util.concurrent.FutureTask.run(FutureTask.java:266) ~[?:1.8.0_342]
	at java.util.concurrent.ThreadPoolExecutor.runWorker(ThreadPoolExecutor.java:1149) ~[?:1.8.0_342]
	at java.util.concurrent.ThreadPoolExecutor$Worker.run(ThreadPoolExecutor.java:624) ~[?:1.8.0_342]
	at java.lang.Thread.run(Thread.java:750) [?:1.8.0_342]
Caused by: java.util.concurrent.ExecutionException: org.apache.seatunnel.transform.exception.TransformException: ErrorCode:[JSONPATH_ERROR_CODE-05], ErrorDescription:[JsonPathTransform path is invalid] - No results for path: $['RawData']['MessageBody']['$type']
	at java.util.concurrent.CompletableFuture.reportGet(CompletableFuture.java:357) ~[?:1.8.0_342]
	at java.util.concurrent.CompletableFuture.get(CompletableFuture.java:1908) ~[?:1.8.0_342]
	at org.apache.seatunnel.connectors.seatunnel.kafka.source.KafkaSourceReader.lambda$pollNext$4(KafkaSourceReader.java:212) ~[?:?]
	... 13 more
Caused by: org.apache.seatunnel.transform.exception.TransformException: ErrorCode:[JSONPATH_ERROR_CODE-05], ErrorDescription:[JsonPathTransform path is invalid] - No results for path: $['RawData']['MessageBody']['$type']
	at org.apache.seatunnel.transform.jsonpath.JsonPathTransform.doTransform(JsonPathTransform.java:171) ~[?:?]
	at org.apache.seatunnel.transform.jsonpath.JsonPathTransform.getOutputFieldValues(JsonPathTransform.java:126) ~[?:?]
	at org.apache.seatunnel.transform.common.MultipleFieldOutputTransform.transformRow(MultipleFieldOutputTransform.java:50) ~[?:?]
	at org.apache.seatunnel.transform.common.AbstractCatalogSupportTransform.map(AbstractCatalogSupportTransform.java:39) ~[?:?]
	at org.apache.seatunnel.transform.common.AbstractCatalogSupportTransform.map(AbstractCatalogSupportTransform.java:28) ~[?:?]
	at org.apache.seatunnel.engine.server.task.flow.TransformFlowLifeCycle.received(TransformFlowLifeCycle.java:94) ~[seatunnel-starter.jar:2.3.7]
	at org.apache.seatunnel.engine.server.task.flow.TransformFlowLifeCycle.received(TransformFlowLifeCycle.java:37) ~[seatunnel-starter.jar:2.3.7]
	at org.apache.seatunnel.engine.server.task.SeaTunnelSourceCollector.sendRecordToNext(SeaTunnelSourceCollector.java:233) ~[seatunnel-starter.jar:2.3.7]
	at org.apache.seatunnel.engine.server.task.SeaTunnelSourceCollector.collect(SeaTunnelSourceCollector.java:148) ~[seatunnel-starter.jar:2.3.7]
	at org.apache.seatunnel.api.serialization.DeserializationSchema.deserialize(DeserializationSchema.java:40) ~[seatunnel-starter.jar:2.3.7]
	at org.apache.seatunnel.connectors.seatunnel.kafka.source.KafkaSourceReader.lambda$pollNext$3(KafkaSourceReader.java:170) ~[?:?]
	at org.apache.seatunnel.connectors.seatunnel.kafka.source.KafkaConsumerThread.run(KafkaConsumerThread.java:58) ~[?:?]
	... 5 more
```

----


## Json path error
### seatunnel transform設定
```
transform {

  JsonPath {
    source_table_name = "kafka_source"
    result_table_name = "trans_json"  # JsonPath 的输出表
    row_error_handle_way = "SKIP"  # 跳过错误行
    columns_error_handle_way = "SKIP"  # 跳过错误行    
    columns = [
        {
          "src_field" = "company_name"        # Adjusted to match the root field in your JSON
          "path" = "$.level2.level3.level4.$level5"  # Path inside the "company_name" object
          "dest_field" = "company_name"       # Output field name
        }
      ]
    }

}
```

### kafka msg 成功
msg有5層，且欄位名稱一致
```
{
    "company_name": {
        "level2": {
            "level3": {
                "level4": {
                    "$level5": "Adkins-Wright"
                }
            }
        }
    },
    "current_time": "2024-12-30T11:30:56.212029"
}
```
![](/uploads/upload_71fdfdaf5c5ddbd9598839ffb40cb394.png)


### kafka msg 失敗
msg有5層，且欄位名稱不一致

```
{
    "company_name": {
        "level2": {
            "level3": {
                "level4": {
                    "level5": "James-Casey"
                }
            }
        }
    },
    "current_time": "2024-12-30T11:33:14.268132"
}
```
![](/uploads/upload_abfd6b9c597259a8e7bd5832a602a1d4.png)




### job不會出錯，會持續跑但資料不會進來

msg有4層，少了最後一個欄位
```
{
    "company_name": {
        "level2": {
            "level3": {
                "level4": "Williams Inc"
            }
        }
    },
    "current_time": "2024-12-30T13:07:05.120233"
}
```


### job不會出錯，會持續跑但資料不會進來

msg有5層，value為空
資料未進入doris，job也不會出錯

```
{
    "company_name": {
        "level2": {
            "level3": {
                "level4": {
                    "$level5": null
                }
            }
        }
    },
    "current_time": "2024-12-30T13:29:03.288415"
}
```


## 20240106

cfx 12/26始Data欄位異動
![](/uploads/upload_7bfd86d64b86d5bebe9ff48aef474664.png)
![](/uploads/upload_19c09119bc2d2febc06ddb6a339c71bd.png)
![](/uploads/upload_03150e3b199e323823941c58891ac4ef.png)
