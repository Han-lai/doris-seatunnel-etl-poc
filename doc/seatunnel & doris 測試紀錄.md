# seatunnel & doris 測試紀錄![](/uploads/upload_b376f9bbece00e8d84bfdb9d8dcd5bdd.png)




## 系統設定與優化調整紀錄 

| **順序** | **調整日期** | **調整項目** | **原始值** | **修改原因** | **SQL語法** | **Doris Table** | **實際結果** | **doris效能** | **seatunnel效能** |
|----------|--------------|--------------|------------|--------------|-------------|-----------------|--------------|----------------|--------------------|
| 1        | 2024-10-28 08:48:48 | `JVM 堆內存 (-Xmx) 2G` <br> `streaming_load_max_mb = 1024` <br> `string_type_length_soft_limit_bytes = 1048576` <br> `doris.batch.size = 100000` | | `seatunnel` `OutOfMemoryError: Java heap space` | ```sql SELECT TimeStamp, UniqueID, LineName, MessageName, Source, Target, RequestID, MessageBody FROM PK_MessageBody_data WHERE LineName='wj_c02' AND MessageName='CFX.Production.UnitsArrived'``` | pkmsg_autobkt_c02_UnitsArrived ||![](/uploads/upload_230657ca4cf39b0128e87af14a99e896.png)| ![](/uploads/upload_02bfe8edac492d43eaa7eabb9d67a1f4.png)|
| 2        | 2024-10-29 02:12:37 | `JVM 堆內存 (-Xmx) 4G` | | `OutOfMemoryError: Java heap space` | ```sql SELECT TimeStamp, UniqueID, LineName, MessageName, Source, Target, RequestID, MessageBody FROM PK_MessageBody_data WHERE LineName='wj_c02' AND MessageName='CFX.Production.UnitsArrived'``` | pkmsg_autobkt_c02_UnitsArrived |![](/uploads/upload_4d5942beacfcde39d1faf7f6cd002531.png) | ![](/uploads/upload_8e7bd72113c4b00086148bcb27b55844.png) |
| 3        | 2024-10-29 03:21:05 | `JVM 堆內存 (-Xmx) 6G` | | `OutOfMemoryError: Java heap space` | ```sql SELECT TimeStamp, UniqueID, LineName, MessageName, Source, Target, RequestID, MessageBody FROM PK_MessageBody_data WHERE LineName='wj_c02' AND MessageName='CFX.Production.UnitsArrived'``` | pkmsg_autobkt_c02_UnitsArrived | `SeaTunnel job executed failed`/ `Doris encountered unqualified data` | ![](/uploads/upload_f4fae50dec984915128101ada622ff12.png)| ![](/uploads/upload_4239a853b8a72575dfde6188997b6982.png) |
| 4        | 2024-10-29 03:36:03 | `JVM 堆內存 (-Xmx) 6G` <br> `streaming_load_max_mb = 10240` <br> `string_type_length_soft_limit_bytes = 2147483643` | | `java.io.UncheckedIOException: Failed to read column #8 of 8: MessageBody String` | ```sql SELECT TimeStamp, UniqueID, LineName, MessageName, Source, Target, RequestID, MessageBody FROM PK_MessageBody_data WHERE LineName='wj_c02' AND MessageName='CFX.Production.UnitsArrived'``` | pkmsg_autobkt_c02_UnitsArrived |![](/uploads/upload_8c0f2df29170bbae403e2355d2374cf2.png)| ![](/uploads/upload_6e7b37b5c3eea47719626d0da8c411f2.png)|
| 5        | 2024-10-29 09:11:31 | `JVM 堆內存 (-Xmx) 7G` <br> `streaming_load_max_mb = 10240` <br> `string_type_length_soft_limit_bytes = 2147483643` | | `java.io.UncheckedIOException: Failed to read column #8 of 8: MessageBody String` | ```sql "SELECT `TimeStamp`, UniqueID, LineName, MessageName, `Source`, Target, RequestID, MessageBody FROM PK_MessageBody_data where LineName='wj_c02' AND MessageName='CFX.Production.UnitsArrived' and toString(`TimeStamp`) > '2024-10-13 00:00:00.000 +0000' and toString(`TimeStamp`) < '2024-10-14 00:00:00.000 +0000'``` | pkmsg_autobkt_c02_UnitsArrived | `SeaTunnel  java.lang.OutOfMemoryError: Java heap space` <br> `Doris org.apache.seatunnel.connectors.doris.exception.DorisConnectorException: ErrorCode:[Doris-01], ErrorDescription:[stream load error] - stream load error: [DATA_QUALITY_ERROR]too many filtered rows, see more in http://10.136.219.209:8040/api/_load_error_log?file=__shard_15/error_log_insert_stmt_fd48820d6264c483-369f86ce2e39dcbb_fd48820d6264c483_369f86ce2e39dcbb`![](/uploads/upload_5e020900eeb99953218fff3f9c53ac90.png)| [Reason: Parse json data for JsonDoc failed. code: 14, error info: A string is opened, but never closed.](http://10.136.219.209:8040/api/_load_error_log?file=__shard_15/error_log_insert_stmt_fd48820d6264c483-369f86ce2e39dcbb_fd48820d6264c483_369f86ce2e39dcbb) |
| 6        | 2024-10-30 07:28:14 | `JVM 堆內存 (-Xmx) 7G` <br> `streaming_load_max_mb = 10240` <br> `string_type_length_soft_limit_bytes = 2147483643` | | `java.io.UncheckedIOException: Failed to read column #8 of 8: MessageBody String` | ```sql "SELECT `TimeStamp`, UniqueID, LineName, MessageName, `Source`, Target, RequestID, MessageBody FROM PK_MessageBody_data where LineName='wj_c02' AND MessageName='CFX.Production.UnitsArrived' and toString(`TimeStamp`) > '2024-10-13 00:00:00.000 +0000' and toString(`TimeStamp`) < '2024-10-14 00:00:00.000 +0000' and length(MessageBody) >=5000000 LIMIT 300'``` | pkmsg_autobkt_c02_UnitsArrived_LIMIT | 可以寫入250筆及300筆到doris中 |![](/uploads/upload_1a94568aec3653db6163a1ae80cdaccd.png) |![](/uploads/upload_904885141f2deeac4bd09cf4cc233162.png)
 |
| 7        | 2024-10-30 08:24:44 | `JVM 堆內存 (-Xmx) 7G` <br> `streaming_load_max_mb = 10240` <br> `string_type_length_soft_limit_bytes = 2147483643` | | `java.io.UncheckedIOException: Failed to read column #8 of 8: MessageBody String` | ```sql "SELECT `TimeStamp`, UniqueID, LineName, MessageName, `Source`, Target, RequestID, MessageBody FROM PK_MessageBody_data where LineName='wj_c02' AND MessageName='CFX.Production.UnitsArrived' and toString(`TimeStamp`) > '2024-10-13 00:00:00.000 +0000' and toString(`TimeStamp`) < '2024-10-14 00:00:00.000 +0000' and length(MessageBody) >=5000000 LIMIT 400'``` | pkmsg_autobkt_c02_UnitsArrived_LIMIT | `ErrorCode:[Doris-01], ErrorDescription:[stream load error] - stream load error: [CANCELLED][INTERNAL_ERROR][MEM_LIMIT_EXCEEDED]PreCatch error code:11, [E11] Allocator sys memory check failed: Cannot alloc:4294967296` | ![image](https://hackmd.io/_uploads/rJiQ9_k-1e.png) | ![image](https://hackmd.io/_uploads/Hy_Wc_JZJe.png) |
|8       |  2024-11-01 05:40:19| `JVM 堆內存 (-Xmx) 7G` <br> `streaming_load_max_mb = 10240` <br> `string_type_length_soft_limit_bytes = 2147483643`  <br> `doris.batch.size = 1024`| | | ```sql "SELECT `TimeStamp`, UniqueID, LineName, MessageName, `Source`, Target, RequestID, MessageBody FROM PK_MessageBody_data where LineName='wj_c02' AND MessageName='CFX.Production.UnitsArrived' and toString(`TimeStamp`) > '2024-10-13 00:00:00.000 +0000' and toString(`TimeStamp`) < '2024-10-14 00:00:00.000 +0000' and length(MessageBody) >=5000000 LIMIT 400'``` | pkmsg_autobkt_c02_UnitsArrived_LIMIT |成功  |  | ![image](https://hackmd.io/_uploads/HyE8OzG-kx.png) |
|9       |  2024-11-01 08:38:31| be.conf裡面將15000改成5000`dirty_decay_ms:5000`| | | ```sql "SELECT `TimeStamp`, UniqueID, LineName, MessageName, `Source`, Target, RequestID, MessageBody FROM PK_MessageBody_data where LineName='wj_c02' AND MessageName='CFX.Production.UnitsArrived' and toString(`TimeStamp`) > '2024-10-13 00:00:00.000 +0000' and toString(`TimeStamp`) < '2024-10-14 00:00:00.000 +0000' and length(MessageBody) >=5000000 LIMIT 400'``` | pkmsg_autobkt_c02_UnitsArrived_LIMIT |  |![](/uploads/upload_31d5fa5d7f56761c899430713d12438a.png)|![](/uploads/upload_5e12485b98dc08d68b6b5fa948634ab8.png) |
|10      |  2024-11-01 05:40:19| `ALTER WORKLOAD GROUP normal PROPERTIES("enable_memory_overcommit" = "false")`<br> `ALTER WORKLOAD GROUP normal PROPERTIES("memory_limit" = "70%")`| | | ```sql "SELECT `TimeStamp`, UniqueID, LineName, MessageName, `Source`, Target, RequestID, MessageBody FROM PK_MessageBody_data where LineName='wj_c02' AND MessageName='CFX.Production.UnitsArrived' and toString(`TimeStamp`) > '2024-10-13 00:00:00.000 +0000' and toString(`TimeStamp`) < '2024-10-14 00:00:00.000 +0000' and length(MessageBody) >=5000000 LIMIT 400'``` | pkmsg_autobkt_c02_UnitsArrived_LIMIT | `Caused by: org.apache.seatunnel.engine.common.exception.SeaTunnelEngineException: java.lang.RuntimeException: java.lang.RuntimeException: java.util.concurrent.ExecutionException: org.apache.seatunnel.connectors.doris.exception.DorisConnectorException: ErrorCode:[Doris-01], ErrorDescription:[stream load error] - stream load error: [CANCELLED]GC wg for hard limit, wg id:1, name:normal, used:8.00 GB, limit:7.56 GB, backend:10.136.219.209. cancel top memory used tracker <Load#Id=6c4423150a0475be-b705cd052d5d8bb2> consumption 8.00 GB. details:process memory used 4.12 GB exceed soft limit 9.72 GB or sys available memory 8.09 GB less than warning water mark 1.20 GB., Execute again after enough memory, details see be.INFO., see more in null` |![](/uploads/upload_34153bf7dce70af673206f03a1e1e3ee.png)|![](/uploads/upload_1252d6af32d4e9562ee644435a9a4c76.png) |




| 步驟 | 調整內容 | 目標 |
|------|----------|------|
| 1    | memory_limit 調整 | 將 memory_limit 設定為 50% 或更低 | 減少系統記憶體壓力 |
| 2    | 關閉記憶體超額配置 | enable_memory_overcommit 設為 false | 防止過度分配記憶體 |
| 3    | 降低批次大小 | 調小 doris.batch.size 值 | 減少單次載入的記憶體需求 |
| 4    | 減少載入容量限制 | 調整 streaming_load_max_mb 或 string_type_length_soft_limit_bytes | 避免一次載入過大數據 |



問題 :

* doris 已經拋出gc error ，但seatunnel 持續未暫停job
Doris 在02:35 已經拋出cancel的資訊
![](/uploads/upload_9fe3da46693166279e0869613870bc05.png)
seatunnel 在0332 才shutdown
![](/uploads/upload_4dfdc3741ba3c0d3e8c1441535ec1780.png)
![](/uploads/upload_209a971677c386f09ae7e360db1ee000.png)

> 設定值
* JVM:7G,memory_limit:25%
* doris.batch.size:1024
* enable_memory_overcommit=false 
* streaming_load_max_mb = 10240
* string_type_length_soft_limit_bytes =2147483643

![](/uploads/upload_0d8a097fe798fb1f67f8304358ae0045.png)



## **SEATUNNEL備註/日誌**

| **欄位**         | **內容**                                                                                   |
|------------------|---------------------------------------------------------------------------------------------|
| **日期時間**     | 2024-10-28 08:48:48                                                                         |
| **錯誤描述**     | `SeaTunnel job executed failed`                                                              |
| **可能原因**     | `OutOfMemoryError: Java heap space`                                                          |
| **建議解決方案** | - 增加 JVM Heap Size: `-Xmx4g -Xms4g` <br> - 減少每批數據處理量 <br> - 檢查數據源與 Sink 配置 |
| **完整錯誤日誌** | ``` 2024-10-28 08:48:48,547 ERROR [o.a.s.c.s.SeaTunnel] [main] - Fatal Error 2024-10-28 08:48:48,547 ERROR [o.a.s.c.s.SeaTunnel] [main] - Please submit bug report in https://github.com/apache/seatunnel/issues 2024-10-28 08:48:48,547 ERROR [o.a.s.c.s.SeaTunnel] [main] - Reason: SeaTunnel job executed failed Exception StackTrace: org.apache.seatunnel.core.starter.exception.CommandExecuteException: SeaTunnel job executed failed at org.apache.seatunnel.core.starter.seatunnel.command.ClientExecuteCommand.execute(ClientExecuteCommand.java:211) Caused by: java.lang.OutOfMemoryError: Java heap space at org.apache.seatunnel.api.sink.multitablesink.MultiTableSinkWriter.subSinkErrorCheck(MultiTableSinkWriter.java:121) at java.lang.Thread.run(Thread.java:750) ``` | 
|------------------|---------------------------------------------------------------------------------------------------------|
| **日期時間**     | 2024-10-29 02:12:37                                                                     |
| **錯誤描述**     | `SeaTunnel job executed failed`                                                              |
| **可能原因**     | `OutOfMemoryError: Java heap space`                                                          |
| **建議解決方案** | - 增加 JVM Heap Size: `-Xmx6g -Xms6g` <br> - 減少每批數據處理量 <br> - 檢查數據源與 Sink 配置 |
| **完整錯誤日誌** | ``` 2024-10-28 08:48:48,547 ERROR [o.a.s.c.s.SeaTunnel] [main] - Fatal Error 2024-10-28 08:48:48,547 ERROR [o.a.s.c.s.SeaTunnel] [main] - Please submit bug report in https://github.com/apache/seatunnel/issues 2024-10-28 08:48:48,547 ERROR [o.a.s.c.s.SeaTunnel] [main] - Reason: SeaTunnel job executed failed Exception StackTrace: org.apache.seatunnel.core.starter.exception.CommandExecuteException: SeaTunnel job executed failed at org.apache.seatunnel.core.starter.seatunnel.command.ClientExecuteCommand.execute(ClientExecuteCommand.java:211) Caused by: java.lang.OutOfMemoryError: Java heap space at org.apache.seatunnel.api.sink.multitablesink.MultiTableSinkWriter.subSinkErrorCheck(MultiTableSinkWriter.java:121) at java.lang.Thread.run(Thread.java:750) ``` |
|------------------|---------------------------------------------------------c

## DORIS 日誌錯誤解析

| **欄位**         | **內容**                                                                                               |
|------------------|---------------------------------------------------------------------------------------------------------|
| **日期時間**     | 2024-10-29 03:37:13                                                                                   |
| **錯誤描述**     | [DATA_QUALITY_ERROR] Encountered unqualified data, stop processing                                     |
| **可能原因**     | 1. 輸入數據質量不合格 (可能包含 NULL 值或不符合要求的格式) <br> 2. 數據完整性問題                     |
| **建議解決方案** | - 檢查數據來源，確保數據質量 <br> - 設置 DORIS 數據質量檢查條件 <br> - 檢查是否有未處理的 NULL 值或格式不正確的數據 |
| **完整錯誤日誌** | `RuntimeLogger W20241029 03:37:13.987582 962 vtablet_writer.cpp:587] cancel node channel VNodeChannel[207036-10023], load_id=804542c44b0c1fa3-4e86fa4d12e60c86, txn_id=15914, node=10.136.219.209:8060, error message: [DATA_QUALITY_ERROR]Encountered unqualified data, stop processing` |


7. 官方解決辦法
[Memory Tracker Limit Exceeded](https://doris.apache.org/zh-CN/docs/admin-manual/memory-management/memory-analysis/query-cancelled-after-query-memory-exceeded)
![](/uploads/upload_b0c94641416c1256cff9d8775bc257d3.png)


![](/uploads/upload_40a0fa65c0627f1f26d3aa3dcd880103.png)


> Allocator sys memory 
```
RuntimeLogger W20241030 10:18:49.061264  2071 stream_load.cpp:112] handle streaming load failed, id=f34f6fef2cbed079-7ad722a0169e03ae, errmsg=[CANCELLED][INTERNAL_ERROR][INTERNAL_ERROR]close wait failed coz rpc error. VNodeChannel[214561-10023], load_id=f34f6fef2cbed079-7ad722a0169e03ae, txn_id=17025, node=10.136.219.209:8060, add batch req success but status isn't ok, err: [MEM_LIMIT_EXCEEDED]PStatus: (10.136.219.209)[MEM_LIMIT_EXCEEDED]PreCatch error code:11, [E11] Allocator sys memory check failed: Cannot alloc:4294967296, consuming tracker:<Load#Id=f34f6fef2cbed079-7ad722a0169e03ae>, peak used 8590507136, current used 4295443584, exec node:<>, process memory used 7.11 GB exceed limit 10.80 GB or sys available memory 3.99 GB less than low water mark 614.40 MB.
```



> Process Memory Summary
```
2024-10-30T10:18:40.678673751Z Process Memory Summary: process memory used 2.98 GB(= 3.62 GB[vm/rss] - 648.72 MB[tc/jemalloc_cache] + 0[reserved] + 0B[waiting_refresh]), sys available memory 8.59 GB(= 8.59 GB[proc/available] - 0[reserved] - 0B[waiting_refresh]), all quries mem: 3.62 GB
```

## Large virtual memory usage
![](/uploads/upload_2ed3690083b79414cc48489ebef2ffe1.png)
![](/uploads/upload_6393e5bb3278935f1affe009e9f6aba7.png)



## wj_c11欄位string 問題
[ERRORFILE](http://10.136.219.209:8040/api/_load_error_log?file=__shard_35/error_log_insert_stmt_b24f0afa515aa148-f9f1660936fc2cab_b24f0afa515aa148_f9f1660936fc2cab)
這兩筆UNIQUEID的MESSAGEBODY太長，可是過去有寫入到doris
|UniqueID                            |length(MessageBody)|
|------------------------------------|-------------------|
|28d20cfb-9460-4d94-a32d-6bca26b10be1|1,806,171          |
|7c802cff-cb83-4086-bead-61d354297d86|3,301,709          |

```
Reason: column_name[MessageBody], the length of input string is too long than vec schema. first 32 bytes of input str: [{"$type":"CFX.Production.UnitsDe] schema length: 2147483643; limit length: 1048576; actual length: 1806171; . src line []; 
Reason: column_name[MessageBody], the length of input string is too long than vec schema. first 32 bytes of input str: [{"$type":"CFX.Production.UnitsAr] schema length: 2147483643; limit length: 1048576; actual length: 3285134; . src line []; 
Reason: column_name[MessageBody], the length of input string is too long than vec schema. first 32 bytes of input str: [{"$type":"CFX.Production.UnitsDe] schema length: 2147483643; limit length: 1048576; actual length: 3301709; . src line []; 
```

調整BE.conf，將string增為2G > be oom啟動不了，還是要改回
```
string_type_length_soft_limit_bytes = 2147483643 

```
![image](https://hackmd.io/_uploads/SJ_SRnVeJx.png)


## oom問題
```
2024-10-21 07:11:34,335 ERROR [a.s.m.MultiTableWriterRunnable] [st-multi-table-sink-writer-1] - MultiTableWriterRunnable error
java.lang.OutOfMemoryError: Java heap space
```
更改jvm的heap size 
```
  seatunnel:
    image: sgmsaacr.azurecr.io/seatunnel:2.3.7
    environment:
      - JAVA_OPTS=-Xms4G -Xmx4G
      - SEATUNNEL_HOME=/opt/seatunnel
      - SEATUNNEL_VERSION=2.3.5 
    ports:
      - "9801:5801"
    volumes:
      - ./server/config:/opt/seatunnel/config
      - ./logs:/opt/seatunnel/logs
    command: ["/bin/sh", "-c", "/opt/seatunnel/bin/seatunnel-cluster.sh -DJvmOption=-Xms4G -Xmx4G"]
    deploy:
      resources:
        limits:
          cpus: "4"          # 限制容器最多使用 4 核 CPU
          memory: "8g"        # 限制容器最多使用 8GB 記憶體
        reservations:
          cpus: "2"           # 預留至少 2 核 CPU
          memory: "4g"        # 預留至少 4GB 記憶體
    networks:
      - seatunnel-network
```