# seatunnel 與doris配置紀錄

## 1. 工具名稱與版本資訊
* seatunnel 版本 : 2.3.7
* doris 版本 : 

## 2. seatunnel 配置
## 2.1 基本配置




| 參數                            | 值  | 說明                                   |
| ------------------------------- | --- | -------------------------------------- |
| -Xms                            | 7   | JVM 初始化堆內存大小，根據需求設置     |
| -Xmx                            | 7   | JVM 最大堆內存大小，調整為 8G 提升效能 |
| -XX:MetaspaceSize               | 2g  | Metaspace 初始大小                     |
| -XX:+UseG1GC                    |     | 使用 G1 GC 回收機制，適合大內存環境    |
| -XX:+HeapDumpOnOutOfMemoryError |     | 發生 OOM 時生成 Heap Dump              |


## 3. doris 配置
## 3.1 基本配置



* be.conf
 
|參數              |值            | 說明 |
| --------------------- | ------------------- | -------- |
| JEMALLOC_CONF         | dirty_decay_ms:5000 | 設定 jemalloc 內存分配器的「髒頁回收延遲」為 5000 毫秒。這可以控制未使用內存頁釋放的延遲時間，有助於提高內存回收效率並減少內存碎片 |
| streaming_load_max_mb | 10240               | 定義每次流式加載的最大資料量，單位為 MB。此設定影響批次載入的容量上限，根據需求可調整以提高流式處理的吞吐量。  |
| string_type_length_soft_limit_bytes |2147483643 | 設定字符串類型的長度「軟限制」，以位元組數為單位。當字串長度超過此值時，系統會有提示，但不會強制中斷。此設定可防止過長字符串造成記憶體壓力|

* workload 
```
SHOW WORKLOAD GROUPS

ALTER WORKLOAD GROUP normal PROPERTIES("memory_limit" = "2GB", "enable_memory_overcommit" = "false");
```


