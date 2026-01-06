# Issue: Doris Destination 數據加載失敗 - SocketException: Broken pipe
[TOC]

## 問題描述
在使用 Airbyte 整合 Apache Doris 時，數據加載過程中發生了 `SocketException: Broken pipe` 錯誤，導致數據加載失敗。

## 重現步驟
1. 創建 Doris 表格：
 Airbyte整合doris 固定寫法
 [airbyte源碼](https://github.com/airbytehq/connector-archive/blob/main/airbyte-integrations/connectors/destination-doris/src/main/java/io/airbyte/integrations/destination/doris/DorisDestination.java)
 [Doris 建議bucket數量](![](/uploads/8b4d3b20328f4924735750317.png)
)
   ```sql
   CREATE TABLE IF NOT EXISTS `lineitem` ( 
      `_airbyte_ab_id` varchar(40),
      `_airbyte_emitted_at` BIGINT,
      `_airbyte_data` String
   ) DUPLICATE KEY(`_airbyte_ab_id`,`_airbyte_emitted_at`) 
   DISTRIBUTED BY HASH(`_airbyte_ab_id`) BUCKETS 16 
   PROPERTIES ( 
      "replication_allocation" = "tag.location.default: 1"
   );

2. 清空 Doris 表格：

```sql
TRUNCATE TABLE `lineitem`;
```

3. 初始化 Doris 消費者
4. 開始 Airbyte 消息消費者，成功初始化。
5. 執行數據加載過程，最終出現錯誤。

## 預期結果
- 數據應成功加載到 Doris 表格中，無任何錯誤發生。

## 實際結果
- 數據加載失敗，出現以下錯誤訊息：

```
I/O exception (java.net.SocketException) \\
caught when processing request to {}->http://10.136.159.47:8040: Broken pipe
failed to stream load data
```

- Airbyte web ui錯誤堆疊追蹤
```bash!
Stack Trace: org.apache.http.client.ClientProtocolException  at org.apache.http.impl.client.InternalHttpClient.doExecute(InternalHttpClient.java:187) at org.apache.http.impl.client.CloseableHttpClient.execute(CloseableHttpClient.java:83) at org.apache.http.impl.client.CloseableHttpClient.execute(CloseableHttpClient.java:108) at io.airbyte.integrations.destination.doris.DorisStreamLoad.firstCommit(DorisStreamLoad.java:110) at io.airbyte.integrations.destination.doris.DorisConsumer.close(DorisConsumer.java:84) at io.airbyte.integrations.base.FailureTrackingAirbyteMessageConsumer.close(FailureTrackingAirbyteMessageConsumer.java:64) at io.airbyte.integrations.base.IntegrationRunner.runInternal(IntegrationRunner.java:151) at io.airbyte.integrations.base.IntegrationRunner.run(IntegrationRunner.java:100) at io.airbyte.integrations.destination.doris.DorisDestination.main(DorisDestination.java:44)
        
Caused by: org.apache.http.client.NonRepeatableRequestException: Cannot retry request with a non-repeatable request entity at org.apache.http.impl.execchain.RetryExec.execute(RetryExec.java:108)  at org.apache.http.impl.execchain.RedirectExec.execute(RedirectExec.java:110) at org.apache.http.impl.client.InternalHttpClient.doExecute(InternalHttpClient.java:185)  ... 8 more
        
Caused by: java.net.SocketException: Broken pipe  at java.base/sun.nio.ch.NioSocketImpl.implWrite(NioSocketImpl.java:420)
        at java.base/sun.nio.ch.NioSocketImpl.write(NioSocketImpl.java:440)
        at java.base/sun.nio.ch.NioSocketImpl$2.write(NioSocketImpl.java:826)
        at java.base/java.net.Socket$SocketOutputStream.write(Socket.java:1035)  at org.apache.http.impl.io.SessionOutputBufferImpl.streamWrite(SessionOutputBufferImpl.java:124)  at org.apache.http.impl.io.SessionOutputBufferImpl.flushBuffer(SessionOutputBufferImpl.java:136) at org.apache.http.impl.io.SessionOutputBufferImpl.write(SessionOutputBufferImpl.java:167)  at org.apache.http.impl.io.ChunkedOutputStream.flushCacheWithAppend(ChunkedOutputStream.java:122)  at org.apache.http.impl.io.ChunkedOutputStream.write(ChunkedOutputStream.java:179)  at org.apache.http.entity.InputStreamEntity.writeTo(InputStreamEntity.java:134)

```

----
- Doris fe log
- ![](/uploads/8b4d3b20328f4924735750312.png)
![](/uploads/8b4d3b20328f4924735750313.png)

僅出現memory summary 
但未出現out of memory 的error log
![](/uploads/8b4d3b20328f4924735750315.png)

- Broken Pipe 官方建議作法
- [官方建議數據操作常見問題連結](https://doris.apache.org/zh-CN/docs/2.1/faq/data-faq?_highlight=broken#q7-%E9%80%9A%E8%BF%87-java-%E7%A8%8B%E5%BA%8F%E8%B0%83%E7%94%A8-stream-load-%E5%AF%BC%E5%85%A5%E6%95%B0%E6%8D%AE%E5%9C%A8%E4%B8%80%E6%89%B9%E6%AC%A1%E6%95%B0%E6%8D%AE%E9%87%8F%E8%BE%83%E5%A4%A7%E6%97%B6%E5%8F%AF%E8%83%BD%E4%BC%9A%E6%8A%A5%E9%94%99-broken-pipe)




## 環境資訊
* Apache Doris 版本：2.0.12
* Airbyte 版本：0.57.3
* Java 版本：jdk8
* 操作系統：ubuntu
* 連接 IP 地址：http://10.136.159.47:8040。

## 可能的解決方案
1. **Bucket 數量和數據量建議**
 [官方連結](https://doris.apache.org/zh-CN/docs/2.1/table-design/data-partition/)
   - **Tablet 總數**:
     - 一個表的 Tablet 總數量等於分區數 (Partition num) 與分桶數 (Bucket num) 的乘積。
    - **Tablet 數量建議**:
     不考慮擴容的情況下，建議 Tablet 總數略多於整個集群的磁盤數量。
   - **單個 Tablet 數據量**:
    建議保持在 1G - 10G 範圍內。過小會增加元數據管理壓力，過大不利於副本遷移和操作重試。
   - **優先考量**: 
     當數量原則和數據量原則衝突時，建議優先考慮數據量原則。
    - **Bucket 數量設置**:
    建表時每個分區的 Bucket 數量需統一，但在增加分區時（ADD PARTITION），可以單獨指定新分區的 Bucket 數量以應對數據的縮小或膨脹。
   - **優先考量**: 
    一旦指定，分區的 Bucket 數量不能更改，設置時需考慮集群擴容。

- **示例建議**:
  - 500MB 表：考慮 4-8 個分片。
  - 5GB 表：考慮 8-16 個分片。
  - 50GB 表：32 個分片。
  - 500GB 表：建議分區，每個分區約 50GB，16-32 個分片。
  - 5TB 表：建議分區，每個分區約 50GB，16-32 個分片。

2. **服務器建議配置**
   - **開發及測試環境**:
     - Frontend: 8 核 +, 8GB + 內存, SSD 或 SATA, 10GB +
     - Backend: 8 核 +, 16GB + 內存, SSD 或 SATA, 50GB +

   - **生產環境**:
     - Frontend: 16 核 +, 64GB + 內存, SSD 或 RAID, 100GB +
     - Backend: 16 核 +, 64GB + 內存, SSD 或 SATA, 100GB +
     - 建議至少 3 台機器部署 Backend 以提升查詢性能。

3. **硬盤空間計算**
   - **FE**: 建議不低於 100GB。
   - **BE**: 按總數據量 * 3（3 副本）計算磁盤空間，預留 40% 空間用於 compaction 和臨時數據存儲。

4. **Java 版本**
- [x]    - 2.1 版本前使用 Java 8，推薦 openjdk-8u352-b08-linux-x64。
   - 3.0 版本後使用 Java 17，推薦 jdk-17.0.10_linux-x64_bin.tar.gz。

5. **操作系統設置**
- [x]    - **關閉 swap 分區**: 
     - 暫時關閉：`swapoff -a`
     - 永久關閉：編輯 `/etc/fstab` 並註釋掉 swap 分區。

   - **配置 NTP 服務**:
     ```bash
     sudo systemctl start ntpd.service
     sudo systemctl enable ntpd.service
     ```

- [x]    - **設置系統最大打開文件句柄數**:
     編輯 `/etc/security/limits.conf` 並增加：
     ```
     * soft nofile 1000000
     * hard nofile 1000000
     ```

- [x]    - **修改虛擬內存區域數量**:
     ```bash
     sysctl -w vm.max_map_count=2000000
     ```

   - **關閉透明大頁**:
     ```bash
     echo never > /sys/kernel/mm/transparent_hugepage/enabled
     echo never > /sys/kernel/mm/transparent_hugepage/defrag
     ```
     
## 內存追蹤設定
- [BE OOM 分析](https://doris.apache.org/zh-CN/docs/2.1/admin-manual/memory-management/be-oom-analysis)

僅出現memory summary 
但未出現out of memory 的error log
![](/uploads/8b4d3b20328f4924735750315.png)

## 其他備註
- (7/30) VM 後續無法啟動 >>  請IT 重啟
- (7/30) VM 重啟後 >> 防火牆掛掉>> 請Networkteam 重設定防火牆
- (8/2) IT 重啟並確認防火牆正常啟動
- (8/2) VM 正常、防火牆正常、Docker 服務正常 >> 依然無法連線網頁
- (8/5) VM 無法登入(Network error)

## 附件
- 添加任何有助於描述或分析問題的文件、截圖、日誌等。
