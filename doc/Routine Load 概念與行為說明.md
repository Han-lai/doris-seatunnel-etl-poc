# Routine Load 概念與行為說明

## 1. Routine Load 的概念
Routine Load 是 Doris 中的一種實時數據導入方式，主要用於從外部數據源（如 Kafka）將流式數據持續導入 Doris 表。通過 Routine Load，Doris 可以實現低延遲、高效能的數據導入操作，非常適合處理高頻更新或實時數據分析場景。
![](/uploads/upload_83e161a5810dd66ed0602efae3a5184a.png)

主要特點：
* 自動化：Routine Load 能夠持續自動地從指定的數據源導入數據到 Doris 表。
* 高效能：採用分布式導入機制，能夠處理大量數據並保證高吞吐量。 
* 錯誤容忍：支持錯誤數據的處理和監控，確保數據導入過程穩定可靠。 
* 靈活性：支持多種數據格式（如 JSON、CSV 等），並能通過 JSONPath 提取結構化數據。



## 2. 使用 Routine Load
![](/uploads/upload_c58fa0efbd5068a213cb5450e6f59f46.png)

2.1 建立表格

在使用 Routine Load 將數據導入 Doris 前，需先建立目標表格。這些表格需要與數據源中的字段結構相匹配。

示例： 創建一個表來存儲設備數據：
```sql=
CREATE TABLE cfx_work_completed (
    MessageID varchar(255),
    receiveat DATETIME,

    MessageType varchar(255),
    MessageVersion INT,
    MessageTime DATETIME,
    Sender varchar(255),
    
    `Data` String, -- 存储整个 Data JSON 作为备份
    
    processed_time String,
    device_id varchar(255),
    line_id varchar(255),
    mfg_plant_code varchar(255),
    factory varchar(255),
    message_name varchar(255),
    source varchar(255),

    rawdata String, -- 存储 RawData JSON 作为备份
    
    RawData_message_name varchar(255),
    RawData_version varchar(255),
    RawData_timestamp String,
    RawData_UniqueID varchar(255),
    RawData_source varchar(255),
    RawData_target varchar(255),
    RawData_RequestID varchar(255),

    RawData_MessageBody_type varchar(255),
    RawData_MessageBody_TransactionID varchar(255),
    RawData_MessageBody_Result varchar(255),
    RawData_MessageBody_PrimaryIdentifier varchar(255),
    
    RawData_MessageBody_HermesIdentifier varchar(255),
    RawData_MessageBody_UnitCount INT
)
DUPLICATE KEY (MessageID)
DISTRIBUTED BY HASH(MessageID) BUCKETS 4
PROPERTIES (
    "replication_num" = "1"
);

```


2.2 創建 Routine Load 任務

建立好表格後，可以創建 Routine Load 任務以持續導入數據。

創建一個 Routine Load 任務來導入 Kafka 數據：
```sql
Create  ROUTINE LOAD cfx_routine_load
ON cfx_work_completed
COLUMNS TERMINATED BY ",",
COLUMNS (
    MessageID ,                   -- This should match Kafka's key "MessageID"
    receiveat ,                    -- This should match Kafka's key "receiveat"
    MessageType ,                -- This should match Kafka's key "MessageType"
    MessageVersion ,          -- This should match Kafka's key "MessageVersion"
    MessageTime ,                -- This should match Kafka's key "MessageTime"
    Sender ,
    `Data`,  -- Store `Data` as a backup
    processed_time = JSON_EXTRACT(`Data`, '$.ProcessedTime'),
    device_id = JSON_EXTRACT(`Data`, '$.Meta.DeviceID'),
    line_id = JSON_EXTRACT(`Data`, '$.Meta.LineID'),
    mfg_plant_code = JSON_EXTRACT(`Data`, '$.Meta.MfgPlantCode'),
    factory = JSON_EXTRACT(`Data`, '$.Meta.Factory'),
    message_name = JSON_EXTRACT(`Data`, '$.Meta.MessageName'),
    source = JSON_EXTRACT(`Data`, '$.Meta.Source'),
    rawdata,
    RawData_message_name = JSON_EXTRACT(`Data`, '$.RawData.MessageName'),
    RawData_version = JSON_EXTRACT(`Data`, '$.RawData.Version'),
    RawData_timestamp = JSON_EXTRACT(`Data`, '$.RawData.TimeStamp'),
    RawData_UniqueID = JSON_EXTRACT(`Data`, '$.RawData.UniqueID'),
    RawData_source = JSON_EXTRACT(`Data`, '$.RawData.Source'),
    RawData_target = JSON_EXTRACT(`Data`, '$.RawData.Target'),
    RawData_RequestID = JSON_EXTRACT(`Data`, '$.RawData.RequestID'),
    RawData_MessageBody_type = JSON_EXTRACT(`Data`, '$.RawData.MessageBody.$type'),
    RawData_MessageBody_TransactionID = JSON_EXTRACT(`Data`, '$.RawData.MessageBody.TransactionID'),
    RawData_MessageBody_Result = JSON_EXTRACT(`Data`, '$.RawData.MessageBody.Result'),
    RawData_MessageBody_PrimaryIdentifier = JSON_EXTRACT(`Data`, '$.RawData.MessageBody.PrimaryIdentifier'),
    RawData_MessageBody_HermesIdentifier = JSON_EXTRACT(`Data`, '$.RawData.MessageBody.HermesIdentifier'),
    RawData_MessageBody_UnitCount = JSON_EXTRACT(`Data`, '$.RawData.MessageBody.UnitCount')
)
PROPERTIES(
    "format"="json"
)
FROM KAFKA(
    "kafka_broker_list" = "10.136.218.207:9092",
    "kafka_topic" = "CFX_CFX_Production_WorkCompleted",
    "property.kafka_default_offsets" = "OFFSET_BEGINNING"
);
```


2.3 啟動與監控任務

Routine Load 任務創建後會自動啟動。可以通過以下 SQL 的執行情況：
```查看任務 :SHOW ROUTINE LOAD;```
|Id|Name|CreateTime|PauseTime|EndTime|DbName|TableName|IsMultiTable|State|DataSourceType|CurrentTaskNum|JobProperties|DataSourceProperties|CustomProperties|Statistic|Progress|Lag|ReasonOfStateChanged|ErrorLogUrls|OtherMsg|User|Comment|
|--|----|----------|---------|-------|------|---------|------------|-----|--------------|--------------|-------------|--------------------|----------------|---------|--------|---|--------------------|------------|--------|----|-------|
|863476|cfx_routine_load|2024-12-24 08:18:39|||routineloaddb|cfx_work_completed|false|RUNNING|KAFKA|1|{"max_batch_rows":"20000000","timezone":"Etc/UTC","send_batch_parallelism":"1","load_to_single_tablet":"false","current_concurrent_number":"1","delete":"*","partial_columns":"false","merge_type":"APPEND","exec_mem_limit":"2147483648","strict_mode":"false","jsonpaths":"","max_batch_interval":"10","max_batch_size":"1073741824","fuzzy_parse":"false","partitions":"*","columnToColumnExpr":"MessageID,receiveat,MessageType,MessageVersion,MessageTime,Sender,Data,processed_time=json_extract(`Data`, '$.ProcessedTime'),device_id=json_extract(`Data`, '$.Meta.DeviceID'),line_id=json_extract(`Data`, '$.Meta.LineID'),mfg_plant_code=json_extract(`Data`, '$.Meta.MfgPlantCode'),factory=json_extract(`Data`, '$.Meta.Factory'),message_name=json_extract(`Data`, '$.Meta.MessageName'),source=json_extract(`Data`, '$.Meta.Source'),rawdata,RawData_message_name=json_extract(`Data`, '$.RawData.MessageName'),RawData_version=json_extract(`Data`, '$.RawData.Version'),RawData_timestamp=json_extract(`Data`, '$.RawData.TimeStamp'),RawData_UniqueID=json_extract(`Data`, '$.RawData.UniqueID'),RawData_source=json_extract(`Data`, '$.RawData.Source'),RawData_target=json_extract(`Data`, '$.RawData.Target'),RawData_RequestID=json_extract(`Data`, '$.RawData.RequestID'),RawData_MessageBody_type=json_extract(`Data`, '$.RawData.MessageBody.$type'),RawData_MessageBody_TransactionID=json_extract(`Data`, '$.RawData.MessageBody.TransactionID'),RawData_MessageBody_Result=json_extract(`Data`, '$.RawData.MessageBody.Result'),RawData_MessageBody_PrimaryIdentifier=json_extract(`Data`, '$.RawData.MessageBody.PrimaryIdentifier'),RawData_MessageBody_HermesIdentifier=json_extract(`Data`, '$.RawData.MessageBody.HermesIdentifier'),RawData_MessageBody_UnitCount=json_extract(`Data`, '$.RawData.MessageBody.UnitCount')","whereExpr":"*","desired_concurrent_number":"256","precedingFilter":"*","format":"json","max_error_number":"0","max_filter_ratio":"1.0","json_root":"","strip_outer_array":"false","num_as_string":"false"}|{"topic":"CFX_CFX_Production_WorkCompleted","currentKafkaPartitions":"0","brokerList":"10.136.218.207:9092"}|{"kafka_default_offsets":"OFFSET_BEGINNING","group.id":"cfx_routine_load_deba07e0-10a2-4e8e-bdb5-12f635349b2a"}|{"receivedBytes":78227768,"runningTxns":[],"errorRows":0,"committedTaskNum":2,"loadedRows":60843,"loadRowsRate":2858,"abortedTaskNum":0,"errorRowsAfterResumed":0,"totalRows":60843,"unselectedRows":0,"receivedBytesRate":3675598,"taskExecuteTimeMs":21283}|{"0":"60842"}|{"0":0}||||root||


暫停或重啟任務，可使用：
```
暫停任務：PAUSE ROUTINE LOAD my_routine_load;
重啟任務：RESUME ROUTINE LOAD my_routine_load;
```

2.4 查看表格內容

```sql!
SELECT MessageID, receiveat, MessageType, MessageVersion, MessageTime, Sender, `Data`, processed_time, device_id, line_id, mfg_plant_code, factory, message_name, source, rawdata, RawData_message_name, RawData_version, RawData_timestamp, RawData_UniqueID, RawData_source, RawData_target, RawData_RequestID, RawData_MessageBody_type, RawData_MessageBody_TransactionID, RawData_MessageBody_Result, RawData_MessageBody_PrimaryIdentifier, RawData_MessageBody_HermesIdentifier, RawData_MessageBody_UnitCount
FROM routineloaddb.cfx_work_completed;
```
![](/uploads/upload_5294142e6e45e1702cae388c7adb21dc.png)

## 3. JSONPath 定位問題與處理

在 Routine Load 中，如果數據格式是 JSON，可以通過 JSON_EXTRACT 或 JSONPath 精確提取所需字段。然而，當 JSON 結構複雜或不規範時，可能會導致定位錯誤。以下是常見問題與解決方案。
3.1 JSONPath 使用示例

假設 Kafka 消息的數據格式如下：
```{
  "ProcessedTime": "2024-12-25T10:30:00Z",
  "Meta": {
    "DeviceID": "D12345",
    "LineID": "L67890",
    "MfgPlantCode": "P001",
    "Factory": "FactoryA",
    "MessageName": "WorkCompleted",
    "Source": "SystemX"
  },
  "RawData": {
    "MessageName": "OperationComplete",
    "MessageBody": {
      "$type": "CFX.Type",
      "TransactionID": "T20241225",
      "UnitCount": 100
    }
  }
}
```
要將上述 JSON 數據導入 Doris，配置 Routine Load 時可以使用以下 JSONPath：
```sql
CREATE ROUTINE LOAD my_routine_load
ON my_table
COLUMNS (
    processed_time = JSON_EXTRACT(`Data`, '$.ProcessedTime'),
    device_id = JSON_EXTRACT(`Data`, '$.Meta.DeviceID'),
    line_id = JSON_EXTRACT(`Data`, '$.Meta.LineID'),
    rawdata_message_name = JSON_EXTRACT(`Data`, '$.RawData.MessageName'),
    message_body_type = JSON_EXTRACT(`Data`, '$.RawData.MessageBody.$type'),
    unit_count = JSON_EXTRACT(`Data`, '$.RawData.MessageBody.UnitCount')
)
PROPERTIES (
    "format" = "json"
)
FROM KAFKA (
    "kafka_broker_list" = "localhost:9092",
    "kafka_topic" = "my_topic"
);
```

## 3.2 常見定位問題

* 字段不存在
    * 問題：JSON 中某些字段可能在某些消息中缺失。
    * 解決：使用 SQL 函數 NULLIF 或 COALESCE 處理缺失字段。

    * 示例：
    ```
    COALESCE(JSON_EXTRACT(`Data`, '$.RawData.MessageName'), 'Unknown')
    ```

* 字段類型不匹配
    * 問題：JSON 中的數值可能被識別為字符串，導致類型錯誤。
    * 解決：使用 CAST 函數強制轉換類型。
    * 示例：

    ```
    CAST(JSON_EXTRACT(`Data`, '$.RawData.MessageBody.UnitCount') AS INT)
    ```
* JSON 結構不規範
    * 問題：不同消息的 JSON 結構可能不一致，導致部分字段無法提取。
    * 解決：在 JSONPath 中增加條件判斷，或者先對數據進行預處理。
* 深層嵌套結構
    * 問題：當 JSON 結構層次過深時，JSONPath 較長且易出錯。
    * 解決：優化數據格式，或分步提取關鍵字段後再處理。

3.3 排查與調試技巧
* 檢查樣例數據： 在 Kafka 中查看多條樣例消息，確保 JSON 結構一致。
* 驗證 JSONPath： 使用工具（如 Jayway JSONPath Evaluator）測試 JSONPath 是否正確。
* 日誌排查： 在 Doris 的 FE 日誌中查看 Routine Load 任務執行狀態和錯誤記錄。

