# Doris_seatunnel

## be 設定
```
enable_stream_load_record = true
streaming_load_max_mb = 102400  --預設是10240mb(10G)  -- 調漲load進去的大小調整成100g 已成功拋了30g
string_type_length_soft_limit_bytes = 2147483643  --預設是104857 --欄位超過預設schema長度所以更改
```


## 問題1_oom
```
2024-10-21 07:11:34,335 ERROR [a.s.m.MultiTableWriterRunnable] [st-multi-table-sink-writer-1] - MultiTableWriterRunnable error
java.lang.OutOfMemoryError: Java heap space
```
### 解決辦法
 > Seatunnel 有更改jvm 防止heap oom 更改成6G

```
services:
  seatunnel:
    image: sgmsaacr.azurecr.io/seatunnel:2.3.7
    environment:
      - JAVA_OPTS=-Xms6G -Xmx6G
      - SEATUNNEL_HOME=/opt/seatunnel
      - SEATUNNEL_VERSION=2.3.5 
    ports:
      - "9801:5801"
    volumes:
      - ./server/config:/opt/seatunnel/config
      - ./logs:/opt/seatunnel/logs
    command: ["/bin/sh", "-c", "/opt/seatunnel/bin/seatunnel-cluster.sh -DJvmOption=-Xms6G -Xmx6G"]
    deploy:
      resources:
        limits:
          cpus: "4"          # 限制容器最多使用 4 核 CPU
          memory: "8g"        # 限制容器最多使用 8GB 記憶體
        reservations:
          cpus: "2"           # 預留至少 2 核 CPU
          memory: "2g"        # 預留至少 4GB 記憶體
    networks:
      - seatunnel-networkservices:

  job_submitter:
    image: sgmsaacr.azurecr.io/seatunnel:2.3.7
    environment:
      - JAVA_OPTS=-Xms6G -Xmx6G
      - SEATUNNEL_HOME=/opt/seatunnel
      - SEATUNNEL_VERSION=2.3.5   
    volumes:
      - ./server/config:/opt/seatunnel/config/
    ##entrypoint: ["sh", "-c", "/opt/seatunnel/bin/seatunnel.sh --config /opt/seatunnel/config/v2.batch.config.template"]
    # entrypoint: ["sh", "-c", "/opt/seatunnel/bin/seatunnel.sh --config /opt/seatunnel/config/wj3.config"]
    entrypoint: ["sh", "-c", "/opt/seatunnel/bin/seatunnel.sh --config /opt/seatunnel/config/large_data.config"]
    depends_on:
      - seatunnel
    networks:
      - seatunnel-network
```

BE 調整成100G

## 問題2
```
ERROR [o.a.s.e.s.d.p.PhysicalVertex  ] [hz.main.seaTunnel.task.thread-74] - Job SeaTunnel_Job (901361377703100417), Pipeline: [(1/1)], task: [pipeline-1 [Source[0]-Clickhouse]-SourceTask (1/1)] end with state FAILED and Exception: java.lang.RuntimeException: java.lang.RuntimeException: org.apache.seatunnel.connectors.doris.exception.DorisConnectorException: ErrorCode:[Doris-01], ErrorDescription:[stream load error] - java.util.concurrent.ExecutionException: org.apache.http.client.ClientProtocolException

```
>造成BROKE PIPE


## 問題3_欄位問題
[ERRORFILE](http://10.136.219.209:8040/api/_load_error_log?file=__shard_35/error_log_insert_stmt_b24f0afa515aa148-f9f1660936fc2cab_b24f0afa515aa148_f9f1660936fc2cab)

```
Reason: column_name[MessageBody], the length of input string is too long than vec schema. first 32 bytes of input str: [{"$type":"CFX.Production.UnitsDe] schema length: 2147483643; limit length: 1048576; actual length: 1806171; . src line []; 
Reason: column_name[MessageBody], the length of input string is too long than vec schema. first 32 bytes of input str: [{"$type":"CFX.Production.UnitsAr] schema length: 2147483643; limit length: 1048576; actual length: 3285134; . src line []; 
Reason: column_name[MessageBody], the length of input string is too long than vec schema. first 32 bytes of input str: [{"$type":"CFX.Production.UnitsDe] schema length: 2147483643; limit length: 1048576; actual length: 3301709; . src line []; 
```

> 但是過去有寫過這幾筆資料存放在DORIS
這兩筆UNIQUEID的MESSAGEBODY太長，可是過去有寫入到doris

|UniqueID                            |length(MessageBody)|
|------------------------------------|-------------------|
|28d20cfb-9460-4d94-a32d-6bca26b10be1|1,806,171          |
|7c802cff-cb83-4086-bead-61d354297d86|3,301,709          |

### 解決辦法
調整be.conf後重啟
```
string_type_length_soft_limit_bytes = 2147483643 

```
![image](https://hackmd.io/_uploads/SJ_SRnVeJx.png)


## 測試表

|MessageName|count()| 測試 |資料量|
|-----------|-------|-------|-------|
 |CFX.ResourcePerformance.StationParametersModified|17311099|V|20851750523
|CFX.Heartbeat|13338133|V|5641669042
|CFX.ResourcePerformance.StationStateChanged|9363228|V|4261577770
|CFX.Production.UnitsArrived|2231649| oom |
|CFX.Production.UnitsDeparted|2191927|v|

> 測試傳入非oom的欄位(測試去除UnitsArrived以及UnitsDeparted) 
> be string有更改成2G
> Seatunnel 有更改jvm 防止heap oom 更改成6G

| Job Name                                        | Variant      | Category       | IP Address      | Status  | Result | Error | Read Count | Write Count | Read Errors | Write Errors | Data Size (Bytes) | Start Time            | End Time              | User |
|------------------------------------------------|--------------|----------------|----------------|---------|--------|-------|------------|-------------|-------------|--------------|-------------------|-----------------------|----------------------|------|
| pkmsg_autobkt_c02_test_variant_pkmsg_autobkt_901040181874786305_0_1 | test_variant | pkmsg_autobkt | 10.136.147.129 | Success | OK     | N/A   | 33,206,750 | 33,206,750  | 0           | 0            | 36,159,762,398    | 2024-10-22 09:32:01.874 | 2024-10-22 09:38:10.765 | root |


## 未解決 持續oom
   sql = "SELECT * FROM PK_MessageBody_data where LineName = 'wj_c02' AND MessageName = 'CFX.Production.UnitsArrived'"    >>>OOM

```SQL
SELECT max(LENGTH(MessageBody))
FROM PK_MessageBody_data 
where LineName = 'wj_c02' and MessageName ='CFX.Production.UnitsArrived'

--853148 wj_c02
--5396752(LEN(MSGBODY)

SELECT  max(LENGTH(MessageBody))
FROM PK_MessageBody_data 
where LineName = 'wj_c03' and MessageName ='CFX.Production.UnitsArrived'
--- 370851 wj_c03
--- 1430 (LEN(MSGBODY)

SELECT max(LENGTH(MessageBody))
FROM PK_MessageBody_data 
where LineName = 'wj_c11' and MessageName ='CFX.Production.UnitsArrived'
--- 1052525 wj_c11 (COUNT)
--- 3285134 (LEN(MSGBODY)
```


---

* 僅有wjc02 messagename為UnitsArrived的 造成oom

```
{"$type": "CFX.Production.UnitsArrived, CFX", "PrimaryIdentifier": "string", "HermesIdentifier": "string", "UnitCount": 32774
```
|LineName|UniqueID|MessageBody|length(MessageBody)|
|--------|--------|-----------|-------------------|
|wj_c02|813badb5-682c-4b27-8307-884276725c51|{"$type": "CFX.Production.UnitsArrived, CFX", "PrimaryIdentifier": "string", "HermesIdentifier": "string", "UnitCount": 32774....|53967525396752|

* C03

|LineName|UniqueID|MessageBody|length(MessageBody)|
|--------|--------|-----------|-------------------|
|wj_c03|bb3dcf84-a7b5-4fbb-b4a7-53320c9ee5c0|{"$type":"CFX.Production.UnitsArrived, CFX","PrimaryIdentifier":"string","HermesIdentifier":"string","UnitCount":9,"Units":],"Lane":1} | 1430 |


* C11

|LineName|UniqueID|MessageBody|length(MessageBody)|
|--------|--------|-----------|-------------------|
|wj_c11|104cc5eb-1d26-46c3-b6ee-7efe9855f517|{"$type":"CFX.Production.UnitsArrived, CFX","PrimaryIdentifier":"string","HermesIdentifier":"string","UnitCount":22346...|32851343285134|





---
![image](https://hackmd.io/_uploads/ByqH_8Px1e.png)
* be oom 
```
RuntimeLogger W20241024 03:34:45.292932  1275 compaction.cpp:381] fail to do cumulative compaction. res=[MEM_LIMIT_EXCEEDED]PreCatch error code:11, [E11] Allocator sys memory check failed: Cannot alloc:2147483648, consuming tracker:<CumulativeCompaction:154086>, peak used 1632478291, current used 1626906645, exec node:<>, process memory used 1.92 GB exceed limit 7.20 GB or sys available memory 1.85 GB less than low water mark 409.60 MB.

	0#  doris::Exception::Exception(int, std::basic_string_view<char, std::char_traits<char> > const&) at /var/local/ldb-toolchain/bin/../lib/gcc/x86_64-linux-gnu/11/../../../../include/c++/11/bits/unique_ptr.h:173

	1#  Allocator<false, false, false>::sys_memory_check(unsigned long) const at /home/zcp/repo_center/doris_release/doris/be/src/vec/common/allocator.cpp:126

	2#  Allocator<false, false, false>::realloc_impl(void*, unsigned long, unsigned long, unsigned long) at /home/zcp/repo_center/doris_release/doris/be/src/vec/common/allocator.cpp:175

	3#  doris::vectorized::ColumnStr<unsigned int>::insert_many_continuous_binary_data(char const*, unsigned int const*, unsigned long) at /home/zcp/repo_center/doris_release/doris/be/src/vec/common/pod_array.h:171

	4#  doris::segment_v2::BinaryPlainPageDecoder<(doris::FieldType)5>::next_batch(unsigned long*, COW<doris::vectorized::IColumn>::mutable_ptr<doris::vectorized::IColumn>&) at /home/zcp/repo_center/doris_release/doris/be/src/olap/rowset/segment_v2/binary_plain_page.h:250

	5#  doris::segment_v2::BinaryDictPageDecoder::next_batch(unsigned long*, COW<doris::vectorized::IColumn>::mutable_ptr<doris::vectorized::IColumn>&) at /home/zcp/repo_center/doris_release/doris/be/src/olap/rowset/segment_v2/binary_dict_page.cpp:0

	6#  doris::segment_v2::FileColumnIterator::next_batch(unsigned long*, COW<doris::vectorized::IColumn>::mutable_ptr<doris::vectorized::IColumn>&, bool*) at /home/zcp/repo_center/doris_release/doris/be/src/common/status.h:481

	7#  doris::segment_v2::SegmentIterator::_read_columns_by_index(unsigned int, unsigned int&, bool) at /home/zcp/repo_center/doris_release/doris/be/src/common/status.h:481

	8#  doris::segment_v2::SegmentIterator::_next_batch_internal(doris::vectorized::Block*) at /home/zcp/repo_center/doris_release/doris/be/src/common/status.h:481

	9#  doris::segment_v2::SegmentIterator::next_batch(doris::vectorized::Block*) at /home/zcp/repo_center/doris_release/doris/be/src/common/status.h:481

	10# doris::vectorized::VerticalMergeIteratorContext::_load_next_block() at /home/zcp/repo_center/doris_release/doris/be/src/common/status.h:481

	11# doris::vectorized::VerticalMaskMergeIterator::next_batch(doris::vectorized::Block*) at /home/zcp/repo_center/doris_release/doris/be/src/common/status.h:481

	12# doris::vectorized::VerticalBlockReader::_direct_next_block(doris::vectorized::Block*, bool*) at /home/zcp/repo_center/doris_release/doris/be/src/common/status.h:481

	13# doris::vectorized::VerticalBlockReader::next_block_with_aggregation(doris::vectorized::Block*, bool*) at /home/zcp/repo_center/doris_release/doris/be/src/common/status.h:481
```



## 2pc setting

| Job Name                                        | Variant      | Category       | IP Address      | Status  | Result | Error | Read Count | Write Count | Read Errors | Write Errors | Data Size (Bytes) | Start Time            | End Time              | User |
|------------------------------------------------|--------------|----------------|----------------|---------|--------|-------|------------|-------------|-------------|--------------|-------------------|-----------------------|----------------------|------|
| pkmsg_autobkt_c02_test_variant_pkmsg_autobkt_c02_901769368096997377_0_1 | test_variant | pkmsg_autobkt_c02 | 10.136.147.129 | Success | OK     | N/A   | 867,061     | 867,061      | 0           | 0            | 115,748,397       | 2024-10-24 09:49:39.212 | 2024-10-24 09:50:58.350 | root |

開啟2PC(資料會一次打進去DORIS)
```
sink {
    Doris {
        fenodes = "10.136.147.130:8030"
        username = "root"
        password = ""
        database = "test_variant"
        schema_save_mode = "CREATE_SCHEMA_WHEN_NOT_EXIST"
        table = "pkmsg_autobkt_c02"
        data_save_mode = "APPEND_DATA"
        sink.enable-2pc = "true" -- TRUE 資料一次打，FALSE 分1024ROW去打
```

關閉2pc 資料會按照seatunnel 預設的load進doris
https://seatunnel.apache.org/docs/connector-v2/sink/Doris/#sink-options
![image](https://hackmd.io/_uploads/HJNojT_xkg.png)

可更改doris.batch.size 調整輸入的row數