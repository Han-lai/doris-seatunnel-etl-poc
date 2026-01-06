# seatunnel & kafka _1118

## 1. 概述
### 1.1 SeaTunnel 與 Kafka 的整合
SeaTunnel 是一個開源的數據集成框架，支援多種數據來源與目的地之間的數據傳輸。Kafka 是一個分佈式的消息系統，常用於實時數據流傳輸場景。在本配置中，SeaTunnel 作為 Kafka 的消費者來接收消息，進行數據轉換後，再通過 SeaTunnel 的 Doris connector 將數據輸送至 Doris，實現從消息系統到分析型數據庫的無縫整合。

透過 SeaTunnel 與 Kafka 的整合，我們可以：

從 Kafka 消費數據進行批量或實時處理。
將處理後的數據存儲到 Doris 中，實現資料的持久化存儲和快速查詢。
### 1.2 SeaTunnel + Kafka + Doris 架構
本架構通過 SeaTunnel 作為數據流處理層，在 Kafka 與 Doris 之間構建數據管道。Kafka 存儲並傳輸消息，SeaTunnel 從中消費數據進行轉換並傳輸到 Doris，Doris 用於分析和查詢。


## 2.配置
### 2.1 Seatunnel cfg.
以下是使用的 SeaTunnel 配置文件（seatunnel.conf），包含 Kafka 作為數據源、SQL 作為轉換引擎、以及 Doris 作為目標數據庫的相關配置
```
env {
  parallelism = 1
  job.mode = "BATCH"
  checkpoint.interval = 600000
}

source {
  Kafka {
    result_table_name = "fake"
    schema = {
      fields {
        Timestamp = timestamp
        Topic = string
        Partition = int
        Offset = long
        SchemaId = string
        SchemaType = string
        Key = string
        OWNER = string
        TABLE = string
        OP = string
        scn = string
        train_id = string
        train_seq = string
        rowid = string
        load_seq = string
        DBNAME = string
        columnsBefore = string
        columnsAfter = string
      }
    }
    format = json
    topic = "MES-IT__WJADPMES__WJ_ADP__POC__R_SN_CNF_T"
    bootstrap.servers = "10.146.192.81:9092,10.146.192.82:9092,10.146.192.83:9092"
    kafka.config = {
      client.id = client_1
      max.poll.records = 1000
      poll.timeout =100000 --輪巡時間
      auto.offset.reset = "earliest"
      security.protocol=SASL_PLAINTEXT
      sasl.mechanism=PLAIN
      sasl.jaas.config="org.apache.kafka.common.security.scram.ScramLoginModule required username=\"MFG_DC\" password=\"MFG$DC0924\";"
    }
  }  
}

transform {
  Sql {
    source_table_name = "fake"  # Ensure this is the correct source table from the Kafka plugin
    result_table_name = "fake1" # Result table after SQL transformation
    query = """
      select 
        current_timestamp as ts,
        scn,
        train_id,
        train_seq,
        OWNER as owner,
        `TABLE` as `table`,
        OP as op,
        rowid,
        load_seq,
        DBNAME as dbname,
        columnsBefore,
        columnsAfter
      from fake
    """
  }
}

sink {
  Console {
  source_table_name = "fake1"
  }
}


sink {
  Doris {
    source_table_name = "fake1"  # This should match the transformed result table
    doris.batch.size = 1024
    fenodes = "10.136.147.130:8030"
    username = "root"
    password = ""
    database = "test_variant"
    table = "wj_c11_wjadpmes__wj_adp__poc__r_sn_cnf_t"
    sink.label-prefix = "wj-test"
    sink.enable-delete = "true"
    schema_save_mode = "CREATE_SCHEMA_WHEN_NOT_EXIST"
    save_mode_create_template = """
    CREATE TABLE IF NOT EXISTS `${database}`.`${table_name}` (
    ${rowtype_fields}
    ) ENGINE=OLAP
    UNIQUE KEY (ts)
    DISTRIBUTED BY HASH (ts)
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



## SeaTunnel Logs
SeaTunnel logs indicating successful data loads into Doris:

```
2024-11-08 03:02:49,635 INFO  [o.a.s.c.d.s.w.DorisStreamLoad ] [st-multi-table-sink-writer-2] - load Result {
    "TxnId": 17089,
    "Label": "wj-test_test_variant_wj_c11_wjadpmes__wj_adp__poc__r_sn_cnf_t_907102740142882817_0_1731034959788",
    "Comment": "",
    "TwoPhaseCommit": "false",
    "Status": "Success",
    "Message": "OK",
    "NumberTotalRows": 2,
    "NumberLoadedRows": 2,
    "NumberFilteredRows": 0,
    "NumberUnselectedRows": 0,
    "LoadBytes": 580,
    "LoadTimeMs": 9565,
    "BeginTxnTimeMs": 9,
    "StreamLoadPutTimeMs": 3,
    "ReadDataTimeMs": 0,
    "WriteDataTimeMs": 9519,
    "CommitAndPublishTimeMs": 32
}

```



## Error Messages and Debugging

An error occurs with the Kafka consumer’s connection:
```
2024-11-08 03:02:50,207 ERROR [KafkaConsumer] - Failed to close coordinator
org.apache.kafka.common.errors.InterruptException: java.lang.InterruptedException
	at org.apache.kafka.clients.consumer.internals.ConsumerNetworkClient.maybeThrowInterruptException(ConsumerNetworkClient.java:520)
...
Caused by: java.lang.InterruptedException
```

![](/uploads/upload_67a2e361198be962cc68754f0316edeb.png)
![](/uploads/upload_23fbd1130fc19a98c94a51b9e3e942c2.png)



| Label                                                                 | Db          | Table                                                             | ClientIp        | Status  | Message | Url | TotalRows | LoadedRows | FilteredRows | UnselectedRows | LoadBytes | StartTime               | FinishTime              | User  | Comment |
|-----------------------------------------------------------------------|-------------|-------------------------------------------------------------------|-----------------|---------|---------|-----|-----------|------------|--------------|----------------|-----------|-------------------------|-------------------------|-------|---------|
| wj-test_test_variant_wj_c11_wjadpmes__wj_adp__poc__r_sn_cnf_t_907102740142882817_0_1731034959788 | test_variant | wj_c11_wjadpmes__wj_adp__poc__r_sn_cnf_t                         | 10.136.147.129  | Success | OK      | N/A | 2         | 2          | 0            | 0              | 580       | 2024-11-08 03:02:40.068 | 2024-11-08 03:02:49.633 | root  |         |
| wj-test_test_variant_wj_c11_wjadpmes__wj_adp__poc__r_sn_cnf_t_907102740142882817_0_1731034949543 | test_variant | wj_c11_wjadpmes__wj_adp__poc__r_sn_cnf_t                         | 10.136.147.129  | Success | OK      | N/A | 502       | 502        | 0            | 0              | 183098    | 2024-11-08 03:02:32.717 | 2024-11-08 03:02:39.702 | root  |         |


# 待做
## 多測messagebody的jsonpath
## kafka streaming 的模式



## bug

1. java.lang.NullPointerException
* [java.lang.NullPointerException](https://github.com/apache/seatunnel/issues/6325)
* [NullPointerException](https://github.com/apache/seatunnel/issues/8053)
2. metadata 無解，無法拉取 [issue :  Support read message metadata](https://github.com/apache/seatunnel/pull/3570)



----
## 1125
### kafka streaming 的模式
* 資料會一直收，後續確認dophinschedule 設定
```
env {
  parallelism = 1
  job.mode = "BATCH" #STREAMING
  checkpoint.interval = 6000
}
```
----


## 多測messagebody的jsonpath
![](/uploads/upload_d8e38eb8b5ba392b3d4b881f0cd8e047.png)

![](/uploads/upload_33bede8d87de6e2576cbbc8fc2840357.png)

```
transform {

  JsonPath {
    source_table_name = "CFX_Production_UnitsArrived"
    result_table_name = "jsonpath"  # 替換為轉換後的表名稱
    row_error_handle_way = SKIP  # 跳過錯誤行
    columns = [
      {
        "src_field" = "MessageBody"  # 源表中的字段名
        "path" = "$.$type"  # 提取 PrimaryIdentifier
        "dest_field" = "type"  # 轉換後的欄位名稱
      },
      {
        "src_field" = "MessageBody"  # 源表中的字段名
        "path" = "$.PrimaryIdentifier"  # 提取 PrimaryIdentifier
        "dest_field" = "primary_identifier"  # 轉換後的欄位名稱
      },
      {
        "src_field" = "MessageBody"  # 源表中的字段名
        "path" = "$.HermesIdentifier"  # 提取 HermesIdentifier
        "dest_field" = "hermes_identifier"  # 轉換後的欄位名稱
      },
      {
        "src_field" = "MessageBody"  # 源表中的字段名
        "path" = "$.UnitCount"  # 提取 UnitCount
        "dest_field" = "unit_count"  # 轉換後的欄位名稱
        "dest_type" = "int"
      }
    ]
  }
  Filter {
    source_table_name = "jsonpath"
    result_table_name = "Filter_jsonpath"
    exclude_fields = [MessageBody]
  }
  Sql {
    source_table_name = "Filter_jsonpath"
    result_table_name = "Filter_jsonpath_sql"
    query = "select * from Filter_jsonpath"
  }
}

```


----

### NullPointerException 解決

* 僅篩選message 內容，不拉取metadata
* source : 
    * 僅篩選message 內容，不拉取metadata
    * 僅篩到第一階columnInfo 
* transform : 
    * jsonpath 將columnInfo 其中欄位parse出來(SERIAL_NUMBER、MO_NUMBER..等
    * sql 將null欄位轉成空格* 利用transform 將null欄位轉成空格
* sink : 
    將parse轉出來的欄位依序寫入
    

![](/uploads/upload_9a68b142499a6841cada3fae1b90ad5d.png)    
![](/uploads/upload_ba26bba13d960ca00c61831dedf0037e.png)


```
env {
  parallelism = 1
  job.mode = "BATCH" #STREAMING
  checkpoint.interval = 6000
}

source {
  Kafka {
    result_table_name = "fake"   # Add this line
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
        columnInfo = string
      }
    } 
    format = json
    topic = "MES-IT__WJIAMES__WJ_IA__POC__R_SN_CNF_T"
    bootstrap.servers = "10.146.192.81:9092,10.146.192.82:9092,10.146.192.83:9092"
    kafka.config = {
      max.poll.records = 1000
      auto.offset.reset = "earliest"
      security.protocol = SASL_PLAINTEXT
      sasl.mechanism = PLAIN
      sasl.jaas.config = "org.apache.kafka.common.security.scram.ScramLoginModule required username=\"MFG_DC\" password=\"MFG$DC0924\";"
    }
  }  
}


transform {
  JsonPath {
  
    source_table_name= "fake"
    result_table_name = "fake_trans"   # Add this line
    row_error_handle_way = SKIP  # 跳過錯誤行
    columns = [
      {
        "src_field" = "columnInfo"
        "path" = "$.SERIAL_NUMBER"
        "dest_field" = "columnInfo_serial_number"
      },
      {
        "src_field" = "columnInfo"
        "path" = "$.MO_NUMBER"
        "dest_field" = "columnInfo_mo_number"
      },
      {
        "src_field" = "columnInfo"
        "path" = "$.MODEL_NAME"
        "dest_field" = "columnInfo_model_name"
      },
      {
        "src_field" = "columnInfo"
        "path" = "$.LINE_NAME"
        "dest_field" = "columnInfo_line_name"
      }
    ]
  }

  Sql {
  
    source_table_name= "fake_trans"
    result_table_name = "fake_trans_sql"   # Add this line
    query = """
      select
        IFNULL(scn, '') as scn,
        IFNULL(train_id, '') as train_id,
        IFNULL(train_seq, '') as train_seq,
        IFNULL(OWNER, '') as `owner`,
        IFNULL(`TABLE`, '') as table_name,  -- 避免與關鍵字衝突
        IFNULL(OP, '') as op,
        IFNULL(rowid, '') as rowid,
        IFNULL(load_seq, '') as load_seq,
        IFNULL(DBNAME, '') as dbname,
        IFNULL(columnInfo_serial_number, '') as columnInfo_serial_number,
        IFNULL(columnInfo_mo_number, '') as columnInfo_mo_number,
        IFNULL(columnInfo_model_name, '') as columnInfo_model_name,
        IFNULL(columnInfo_line_name, '') as columnInfo_line_name,
        NOW() as `Input_time` 
     
      from fake_trans
    """
  }
}




#------------------------------dk--------------------------
sink {
  Doris {
    source_table_name= "fake_trans_sql"
    result_table_name = "fake_doris"   # Add this line
    doris.batch.size = 1024
    fenodes = "10.136.147.130:8030"
    username = "root"
    password = ""
    database = "test_variant"
    table = "jsonpath_wj_c11_wjadpmes__wj_ia__poc__r_sn_cnf_t"
    sink.label-prefix = "wj-json"
    sink.enable-delete = "true"
    schema_save_mode = "CREATE_SCHEMA_WHEN_NOT_EXIST"
    data_save_mode = "APPEND_DATA"
    save_mode_create_template = """
    CREATE TABLE IF NOT EXISTS `test_variant`.`jsonpath_wj_c11_wjadpmes__wj_ia__poc__r_sn_cnf_t` (
      scn VARCHAR(255) NOT NULL,
      train_id VARCHAR(255)   NULL,
      train_seq VARCHAR(255)   NULL,
      `owner` VARCHAR(255) NOT  NULL,
      table_name VARCHAR(255)  NOT NULL,  -- renamed to avoid keyword conflict
      op VARCHAR(255) NOT NULL,
      rowid VARCHAR(255) NOT   NULL,
      load_seq VARCHAR(255)  NOT  NULL,
      dbname VARCHAR(255) NOT  NULL,
      columnInfo_serial_number VARCHAR(255)  NOT NULL,
      columnInfo_mo_number VARCHAR(255)  NOT NULL,
      columnInfo_model_name VARCHAR(255) NOT NULL,
      columnInfo_line_name VARCHAR(255) NOT  NULL,
      Input_time Datetime NOT NULL
    ) ENGINE=OLAP
    DUPLICATE KEY (`scn`, `train_id`, `train_seq`)  -- 修改為 DUPLICATE KEY，並指定需要的分布鍵
    DISTRIBUTED BY HASH (`scn`)  -- 分布鍵可以根據需求修改
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

