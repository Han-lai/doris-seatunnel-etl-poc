# DORIS　踩坑紀錄
![](/uploads/upload_e6e4815c0bd550349f1a6acdcd27af0d.png)
[TOC]
## 資料量測試紀錄
### 測試背景與目標
在進行資料量測試時，我們的目的是評估系統處理不同資料集的效能，並確認是否會發生記憶體不足（OOM，Out of Memory）錯誤。測試包含了來自不同來源（wjc02、wjc03、wjc11）的資料，並觀察不同情況下的系統反應。
測試步驟與結果

1. 測試整個資料集（包含 wjc02、wjc03、wjc11）

    * 測試操作：將來自 wjc02、wjc03、wjc11 的資料匯總並進行處理。
    * 結果：發現系統出現 OOM 錯誤，無法成功處理這些資料。
2. 將資料分開處理，分別測試 wjc02、wjc03、wjc11

    * 測試操作：將資料分開，單獨執行每個資料集的查詢（wjc02、wjc03、wjc11）。
    * 結果：進一步測試後，發現僅 wjc02 的資料在處理時出現 OOM 錯誤。
3. 測試單獨查詢 wjc02 資料中的特定欄位

    *  測試操作：針對 wjc02 資料進行進一步篩選，選擇欄位 MessageName，該欄位包含的值有 CFX.Heartbeat、CFX.ResourcePerformance.StationStateChanged、CFX.Production.UnitsArrived 等。
    *  結果：發現只有 CFX.Production.UnitsArrived 的資料會導致 OOM 錯誤，其他 MessageName 的資料未出現 OOM。
4. 單獨處理 UnitsArrived 資料

    * 測試操作：針對 CFX.Production.UnitsArrived 的資料進行測試，發現該資料中可能包含過長的資料長度。
    * 結果：經過進一步分析，發現資料長度過長可能是導致 OOM 的主要原因。這些資料可能包含大量未經處理的文本或過多的記錄，導致記憶體不足。
### 結論與建議
OOM 錯誤的根本原因：CFX.Production.UnitsArrived 的資料在處理時出現 OOM，初步判斷是由於資料長度過長，造成記憶體占用過多。

## 測試表數據量
| Name                                       | 資料量（bytes）        | 資料量（GB）        | 傳送時間 (秒) |
| ------------------------------------------------- | ---------------------- | ------------------- | ------------ |
| CFX.ResourcePerformance.StationParametersModified | 20,851,750,523         | 19.42 GB            | -            |
| CFX.Heartbeat                                     | 5,641,669,042          | 5.26 GB             | -            |
| CFX.ResourcePerformance.StationStateChanged       | 4,261,577,770          | 3.97 GB             | -            |
| CFX.Production.UnitsArrived                       | -                      | OOM                 | -            |
| pkmsg_autobkt_c11_variant                         | 11,490,695,265 | 11.49 GB            | 233.19       |
| pkmsg_autobkt_c03_test_variant                    | 3,889,806,884  |  3.89 GB           | 172.61       |

## issue
### issue 1：內存不足（Out of Memory - OOM）

* 問題描述：

1. Seatunnel 在處理大量資料時出現「OutOfMemoryError: Java heap space」錯誤。
2. Doris 的 Backend (BE) 也出現了內存不足問題，特別是某些表和查詢過大時導致「MEM_LIMIT_EXCEEDED」。
* 解決方法：

    **Seatunnel OOM**：提高 JVM 的堆內存配置。將 JAVA_OPTS 調整為 -Xms6G -Xmx6G，並限制 Seatunnel 容器的 CPU 和內存資源（最多 8GB 記憶體，預留至少 2 核 CPU）。
    **Doris BE OOM**：增加 streaming_load_max_mb 的限制，並將 string_type_length_soft_limit_bytes 設定更大以允許更長的字符串處理。另外可以檢查 BE 設定和系統內存使用情況，確保內存資源不被過度使用。
```
2024-10-28 08:48:48,547 ERROR [o.a.s.c.s.SeaTunnel] [main] - Fatal Error 2024-10-28 08:48:48,547 ERROR [o.a.s.c.s.SeaTunnel] [main] - Please submit bug report in https://github.com/apache/seatunnel/issues 2024-10-28 08:48:48,547 ERROR [o.a.s.c.s.SeaTunnel] [main] - Reason: SeaTunnel job executed failed Exception StackTrace: org.apache.seatunnel.core.starter.exception.CommandExecuteException: SeaTunnel job executed failed at org.apache.seatunnel.core.starter.seatunnel.command.ClientExecuteCommand.execute(ClientExecuteCommand.java:211) Caused by: java.lang.OutOfMemoryError: Java heap space at org.apache.seatunnel.api.sink.multitablesink.MultiTableSinkWriter.subSinkErrorCheck(MultiTableSinkWriter.java:121) at java.lang.Thread.run(Thread.java:750)
```
### issue 2：網路中斷（Broken Pipe）
* 問題描述：

    * 資料加載時，Seatunnel 連接 Doris 出現「Broken Pipe」錯誤，這通常是因為過多的資料傳輸或網路連線中斷所導致。
  
```
Caused by: java.net.SocketException: Broken pipe (Write failed)
at java.net.SocketOutputStream.socketWrite0(Native Method)
at java.net.SocketOutputStream.socketWrite(SocketOutputStream.java:111)
at java.net.SocketOutputStream.write(SocketOutputStream.java:155)
```
    
* 解決方法：

    * 嘗試分批次傳輸大數據或減少單次請求的數據量，以降低單次數據加載對連線的壓力。
    * 增加網路超時設定的時間或確認網路環境穩定性，避免連線因超時而中斷。

### issue 3：欄位長度超出限制（Column Length Exceeded）

* 問題描述：

    * 在將資料加載到 Doris 時，如果資料欄位的長度超過了表中定義的欄位長度限制，則可能會引發錯誤。這通常發生在處理長文本或大型字段（例如 `VARCHAR` 或 `TEXT` 類型）時。

* 解決方法：

    - 檢查資料庫表中的欄位定義，特別是對於變長數據類型（如 `VARCHAR` 或 `TEXT`）的限制。
    - 增加相應欄位的最大長度，或在資料處理過程中使用更合適的資料類型。
    - 可以使用 Doris 的 `string_type_length_soft_limit_bytes` 配置，根據需要調整可接受的欄位長度限制。

### Issue 4：寫入超時（Write Timeout）
* 問題描述：
在高負載或大批量資料加載過程中，可能會出現寫入超時的錯誤。這通常是因為單次操作所需的時間過長，或者資料處理過程中的延遲。


* 解決方法：

    - 增加寫入超時設置。可以調整 Doris 的 `load_default_timeout_second` 配置，設定更長的寫入超時時間。
    - 嘗試分批處理資料，減少每次操作的資料量，從而減少單次請求的執行時間。
    - 檢查系統資源，確保系統的 I/O 性能足夠支援大規模數據寫入。

### Issue 5：不一致的資料格式（Data Format Inconsistency）
* 問題描述：
在資料處理過程中，資料格式不一致會導致錯誤，特別是在轉換或映射資料時。例如，某些欄位的資料型態可能與預期格式不匹配，或資料中缺失必要的欄位。

```
RuntimeLogger W20241029 03:37:13.987582 962 vtablet_writer.cpp:587] cancel node channel VNodeChannel[207036-10023], load_id=804542c44b0c1fa3-4e86fa4d12e60c86, txn_id=15914, node=10.136.219.209:8060, error message: [DATA_QUALITY_ERROR]Encountered unqualified data, stop processing
```
* 解決方法：
    - 檢查資料源和目標資料庫的欄位對應關係，確保資料格式一致。
    - 在資料傳輸過程中，使用資料驗證機制檢查資料格式是否正確，並處理缺失或格式不正確的數據。
    - 可以使用 Seatunnel 提供的資料格式轉換工具（如 JSON、CSV 轉換），確保資料一致性。


## 持續 OOM 問題的潛在解決方案
* 優化查詢：針對大數據查詢的 SQL 語句進行優化，減少一次加載過多數據。
* 限制 MessageBody 長度：在查詢和載入過程中過濾或限制過長的 MessageBody 記錄，減少過大數據進入內存。
* 垂直擴展或水平擴展：增加 Doris BE 節點或擴展現有節點的內存，以支持更大規模的數據處理。


---

##  工具配置
- **Seatunnel 版本**: 2.3.7
### Seatunnel  基本配置

| 參數                            | 值  | 說明                                      |
| ------------------------------- | --- | ----------------------------------------- |
| `-Xms`                           | 7   | JVM 初始化堆內存大小，根據需求設置         |
| `-Xmx`                           | 7   | JVM 最大堆內存大小，調整為 8G 可提升效能 |
| `-XX:MetaspaceSize`              | 2g  | Metaspace 初始大小                        |
| `-XX:+UseG1GC`                   |     | 使用 G1 GC 回收機制，適合大內存環境       |
| `-XX:+HeapDumpOnOutOfMemoryError`|     | 發生 OOM 時生成 Heap Dump                |

**配置目標：**  
- 確保 Seatunnel 在處理大量數據時不會受到內存限制。
- 使用 G1 GC 以提升內存回收效率，避免長時間的垃圾回收延遲。

---

### Doris BE 配置 (`be.conf`)
- **Doris 版本**: 2.1.5

| 參數                              | 值                  | 說明                                                    |
| ----------------------------------- | ------------------- | ------------------------------------------------------- |
| `JEMALLOC_CONF`                     | `dirty_decay_ms:5000` | 設定 jemalloc 內存分配器的「髒頁回收延遲」為 5000 毫秒。此配置幫助減少內存碎片，並提高內存回收效率 |
| `streaming_load_max_mb`             | `10240`             | 設定每次流式加載的最大資料量（MB）。該設置影響流式加載的吞吐量，可根據需求調整以適應流量。 |
| `string_type_length_soft_limit_bytes`| `2147483643`        | 設定字符串類型的長度軟限制。長度超過此值會發出警告，但不會強制中斷。防止過長字符串造成內存壓力。 |

**配置目標：**
- 通過調整 `JEMALLOC_CONF` 來控制內存回收延遲，減少內存碎片。
- 通過調整 `streaming_load_max_mb` 和 `string_type_length_soft_limit_bytes` 限制流式加載數據的大小，避免單次加載數據過大導致內存壓力。

####  Doris Workload 配置

| 步驟 | 調整內容                  | 目標                                      |
|------|---------------------------|-------------------------------------------|
| 1    | `memory_limit` 調整        | 將 `memory_limit` 設為 50% 或更低，減少內存壓力 |
| 2    | 關閉內存超額配置 (`enable_memory_overcommit`) | 設為 `false`，防止過度分配內存 |
| 3    | 降低批次大小              | 減少 `doris.batch.size` 的值，減少單次載入內存需求 |
| 4    | 減少載入容量限制          | 調整 `streaming_load_max_mb` 或 `string_type_length_soft_limit_bytes`，防止一次載入過大數據 |

**配置目標：**
- 降低內存需求並減少系統的記憶體壓力。
- 防止內存過度分配和過大批次的流式加載，從而提高 Doris 的穩定性與性能。


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


