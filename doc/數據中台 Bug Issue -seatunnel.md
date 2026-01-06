
# 數據中台 Bug Issue -seatunnel
[TOC]

![](/uploads/upload_ecc5a2cbe96e0ba5c339ad9c8cc1bbd0.png)


## seatunnel 接收kafka topic 問題
無法從 Kafka Topic 讀取資料，由於 Topic 名稱解析問題

### 描述
在嘗試從 Kafka Topic `EAP.WJ3.CDP.D-ASSY-02.DEVICE_CFX.CFX.Production.WorkCompleted` 透過 EATunnel 系統獲取資料時，源初始化過程發生錯誤。錯誤訊息顯示系統無法將 Kafka Topic 分割為有效的資料庫名稱和表格名稱，原因是 Topic 名稱中包含多個句點 (.)。 

當使用測試 Kafka Topic 如 `TEST.SEA.SEATUNNEL` 時，系統能夠正確解析，但複雜的 Kafka Topic `TEST.SEA.SEATUNNEL.TT` 卻導致相同的錯誤，顯示系統無法處理包含多個句點的 Topic 名稱。

### 錯誤詳細資訊
- **錯誤代碼：** [API-06]
- **錯誤描述：** [Factory initialize failed] - Unable to create a source for identifier 'Kafka'。
- **異常：** `java.lang.IllegalArgumentException: Cannot get split 'TEST.SEA.SEATUNNEL.TT' to get databaseName and tableName`
![](/uploads/upload_79234b003d170d3bcefae7fd8e62ce68.png)

### 重現步驟
1. 嘗試在 EATunnel 配置 Kafka source，並使用 Topic `EAP.WJ3.CDP.D-ASSY-02.DEVICE_CFX.CFX.Production.WorkCompleted`。
2. 觀察到錯誤，顯示系統無法將 Topic 分割為資料庫名稱和表格名稱。
3. 測試 Topic `TEST.SEA.SEATUNNEL`，並確認系統能正確解析。
 ![](/uploads/upload_ca7b94dc6a56a2983c4bdb79ea62073a.png)

5. 測試 `TEST.SEA.SEATUNNEL.TT`，並觀察到相同的錯誤。
6. ![](/uploads/upload_4fde1b751cc78f86dcf5009f982e0d58.png)


### 預期行為
系統應該能夠處理包含多個句點的 Kafka Topic，並正確將 Topic 名稱分割為資料庫名稱和表格名稱，避免出現錯誤。

### 實際行為
系統無法初始化 Kafka source，當 Topic 名稱包含多個句點時，解析過程失敗並顯示錯誤。

### 潛在原因
問題可能出現在 Kafka Topic 的解析過程中。系統可能無法正確處理包含多個句點 (`.`) 的 Topic 名稱。這是因為系統預期 Topic 名稱的結構較簡單，句點數量較少，無法適應更複雜的 Topic 命名規範。
* [GITHUB SOURCE CODE](https://github.com/apache/seatunnel/blob/dev/seatunnel-api/src/main/java/org/apache/seatunnel/api/table/factory/FactoryUtil.java#L170)
* source : [kafka ref.](https://seatunnel.apache.org/zh-CN/docs/2.3.7/connector-v2/source/kafka)
    * topic 限制 : seatunnel 會依據「.」將topic分成dbname、schema、table，故topic名稱勿涵蓋3個「.」


### 詳細解析：
- **Kafka 解析失敗**：`Seatunnel` 無法正確將包含多個句點的 Topic 名稱分割為資料庫名稱和表格名稱。該錯誤與 `FactoryUtil` 類中的 `createAndPrepareSource` 方法有關，該方法在初始化時無法從 Kafka Topic 中獲取正確的資料庫名稱和表格名稱。
- **`CatalogTable` 解析失敗**：在將 Kafka Topic 名稱解析為 `CatalogTable` 時，系統期望的結構可能與 Topic 名稱中的實際結構不匹配。

### 可能的解決方案
1. **Topic 命名變更**：要求工廠團隊修改 Kafka Topic 命名規範，減少 Topic 名稱中的句點數量，這樣可以避免解析錯誤。將 Topic 名稱簡化為更符合系統預期的結構。
   
2. **系統修改**：修改 `Seatunnel` 系統，改進 Topic 名稱解析邏輯，讓系統能夠正確處理包含多個句點的 Kafka Topic，並能夠將 Topic 名稱正確分割為資料庫名稱和表格名稱。這可能涉及：
   - 調整 Topic 名稱解析的邏輯，支持多層次的命名結構。
   - 在 `FactoryUtil` 類中的 `createAndPrepareSource` 方法中加入對多句點 Topic 名稱的處理邏輯。

### 其他備註
- 該問題已在 EAP 相關的 Kafka Topic 獲取過程中被發現，但也可能出現在其他 Kafka Topic 名稱較複雜的情況下。
- 解決此問題的途徑包括：
  - 調整 Kafka Topic 的命名規範。
  - 改進系統的 Topic 解析邏輯，使其能夠支持更多樣化的 Topic 命名規則。

----


## Kafka 到 ClickHouse 資料接收

由於 `Seatunnel` 的 Kafka source 無法正確處理某些複雜的 Kafka Topic 結構，我們選擇了 ClickHouse 作為中介，並通過其 Kafka 引擎來處理 Kafka 資料。
1. **從 Kafka 到 ClickHouse**：將資料從 Kafka 接收並寫入到 ClickHouse。
2. **從 ClickHouse 到 Doris**：使用 `Seatunnel` 將從 ClickHouse 中獲取的資料搬遷到 Doris。

### 注意事項

1. **Kafka 消費者設置**：使用 ClickHouse 的 Kafka 引擎時，需要確保 Kafka 配置正確，並且能夠穩定地接收到來自 Kafka 的資料流。
2. **資料格式問題**：當從 Kafka 接收資料並將其存儲到 ClickHouse 時，我們發現資料並非全部符合 JSON 格式。這造成 ClickHouse 無法正確解析和存儲這些資料，導致資料無法成功接收。請確保 Kafka 中的資料是有效的 JSON 格式。

### JSON 格式問題

- **問題描述**：當資料不是有效的 JSON 格式時，ClickHouse 無法解析這些資料，會導致資料丟失或無法插入表格。
- **解決方案**：在資料寫入 Kafka 時，必須確保資料符合正確的 JSON 格式。這可以通過以下方式解決：
  - 檢查資料生產端的輸出格式，確保資料被格式化為 JSON 格式。
  - 在資料進入 Kafka 之前，使用工具（如 `Kafka Connect` 或自定義的處理程序）來驗證並轉換資料格式為有效的 JSON。
kafka 資料

```json!
{
	"MessageID": "47e61929-0617-4024-87ac-d4d4dfab8a43",
	"TransactionID": null,
	"MessageType": "DEVICE_CFX",
	"MessageVersion": 1.0,
	"MessageTime": "2024-11-12T12:05:45.639719+00:00",
	"Sender": "FactoryEAP",
	"Data": {
		"ProcessedTime": "2024-11-12T12:05:45.638156+00:00",
		"Meta": {
			"DeviceID": "ST00460029",
			"LineID": "D-ASSY-02",
			"MfgPlantCode": "CDP",
			"Factory": "WJ3",
			"MessageName": "CFX.Production.WorkCompleted",
			"Source": "CFX.A00.ST00460029"
		},
		"RawData": {
			"MessageName": "CFX.Production.WorkCompleted",
			"Version": "1.7",
			"TimeStamp": "2024-11-12T12:05:45.6368889+00:00",
			"UniqueID": "5d2b30fc-e41c-4183-aa11-01678c9afafd",
			"Source": "CFX.A00.ST00460029",
			"Target": "inline-control",
			"RequestID": "2c51c960-a69b-4d18-a239-baea81e2db2c",
			"MessageBody": {
				"$type": "CFX.Production.WorkCompleted, CFX",
				"TransactionID": "1ecbc6d7-c28b-4d7d-b881-2c42757bf638",
				"Result": "Completed",
				"PrimaryIdentifier": "2411121511",
				"HermesIdentifier": "string",
				"UnitCount": 1,
				"Units": [
					{
						"UnitIdentifier": "2411121511",
						"PositionNumber": 1,
						"PositionName": "string",
						"X": 0.0,
						"Y": 0.0,
						"Rotation": 0.0,
						"FlipX": false,
						"FlipY": false,
						"Status": "Pass"
					}
				],
				"PerformanceImpacts": []
			}
		}
	},
	"Transmission": [
		{
			"Node": "WJ3-CDP-C02",
			"SendTime": "2024-11-12T12:05:45.638220+00:00"
		},
		{
			"Node": "FactoryEAP",
			"SendTime": "2024-11-12T12:05:45.639686+00:00"
		}
	]
}
```

*  transmission 的格式非json，clickhouse 無法解析
![](/uploads/upload_23932abc6678e987c2e49600c473c898.png)



```
2024.11.25 02:39:21.676997 [ 195 ] {} <Error> StorageKafka (eap_wj3_cdp_d_assy_02_device_cfx_cfx_production_workcompleted): void DB::StorageKafka::threadFunc(size_t) Code: 26. DB::Exception: Cannot parse JSON string: expected opening quote: (while reading the value of key Transmission): while parsing Kafka message (topic: EAP.WJ3.CDP.D-ASSY-02.DEVICE_CFX.CFX.Production.WorkCompleted, partition: 0, offset: 518422)': While executing Kafka. (CANNOT_PARSE_QUOTED_STRING), Stack trace (when copying this message, always include the lines below):
11. DB::KafkaSource::generateImpl() @ 0x0000000010c68658 in /usr/bin/clickhouse
12. DB::KafkaSource::generate() @ 0x0000000010c6c06f in /usr/bin/clickhouse
19. DB::StorageKafka::threadFunc(unsigned long) @ 0x0000000010c55223 in /usr/bin/clickhouse
```

* 先前rabbit MQ接收的資料 也僅接收到	"PerformanceImpacts": []
![](/uploads/upload_91a045e0a161c562cc9b069ef74dbc18.png)




----



## ClickHouse 到 Doris 資料搬遷

當資料成功從 Kafka 被 ClickHouse 接收並儲存後，我們使用 `Seatunnel` 將資料從 ClickHouse 搬遷至 Doris。此過程會依照定期或增量的方式將資料同步至 Doris。

### 注意事項

1. **ClickHouse 配置**：在設置 `Seatunnel` 時，需確保 ClickHouse 的連接參數正確配置，並且能夠正常訪問 ClickHouse 中的資料。
2. **資料格式轉換**：ClickHouse 與 Doris 之間的資料格式有時可能有所不同，請確保資料格式能夠無縫轉換或進行相應的處理。

## 其他建議

1. **Kafka 資料驗證**：強烈建議在資料從 Kafka 進行處理之前，進行資料驗證，確保所有資料符合 JSON 格式，以避免在 ClickHouse 中的解析問題。
2. **監控與日誌**：設置有效的監控和日誌機制，以便能夠及時發現資料格式或處理過程中的問題。

## 結論

通過這個架構，使用 ClickHouse 作為中介來處理 Kafka 資料，並利用 `Seatunnel` 將資料轉移至 Doris，解決了 `Seatunnel` 直接從 Kafka 接收資料的問題。然而，為了確保資料能夠正確流轉，必須解決 Kafka 資料的格式問題，尤其是 JSON 格式的正確性。


----


* clickhouse 因為kafka的資訊裡面有bug 所以收不下來 >> 解決資料裡的問題

# clickhouse kafka engine 設定

```sql=

# Kafka Table
'''
CREATE TABLE EAP.eap_wj3_cdp_d_assy_02_device_cfx_cfx_production_workcompleted
(
    `Timestamp` DateTime,          -- 存储时间戳
    `Topic` String,               -- 存储 Kafka 主题
    `Partition` UInt32,           -- Kafka 分区
    `Offset` UInt64,              -- Kafka 偏移量
    `SchemaId` Nullable(String),  -- 可为空的 SchemaId
    `SchemaType` Nullable(String),-- 可为空的 SchemaType
    `Key` Nullable(String),       -- 消息的键值
    `MessageID` String,           -- 存储 Kafka 消息 ID
    `TransactionID` Nullable(String), -- 可为空的 TransactionID
    `MessageType` String,         -- 消息类型
    `MessageVersion` Nullable(Float64), -- MessageVersion 字段
    `MessageTime` Nullable(String),  -- 消息时间
    `Sender` Nullable(String),    -- 发送者
    `Data` String,                -- 存储 Kafka 消息中的 'Data' 字段
      -- `Transmission` String         -- 存储 Kafka 消息中的 'Transmission' 字段
) ENGINE = Kafka
SETTINGS kafka_broker_list = '10.146.212.114:9092',
         kafka_topic_list = 'EAP.WJ3.CDP.D-ASSY-02.DEVICE_CFX.CFX.Production.WorkCompleted',
         kafka_group_name = 'clickhouse_group',
         kafka_format = 'JSONEachRow',
         kafka_num_consumers = 1;
'''

```

```sql= '''
CREATE TABLE IF NOT EXISTS EAP.eap_wj3_cdp_d_assy_02_device_cfx_cfx_production_workcompleted_mergetree (
    receiveat DateTime,
    `Timestamp` DateTime,
    `Topic` String,
    `Partition` UInt32,
    `Offset` UInt64,
    `SchemaId` Nullable(String),
    `SchemaType` Nullable(String),
    `Key` Nullable(String),
    `MessageID` String,
    `TransactionID` Nullable(String),
    `MessageType` String,
    `MessageVersion` Nullable(Float64),
    `MessageTime` Nullable(String),
    `Sender` Nullable(String),
    `Data` String,
   -- `Transmission` String
) ENGINE = MergeTree()
ORDER BY receiveat;
'''


```


```sql=
'''
CREATE MATERIALIZED VIEW IF NOT EXISTS EAP.mview_eap_wj3_cdp_d_assy_02_device_cfx_cfx_production_workcompleted
TO EAP.eap_wj3_cdp_d_assy_02_device_cfx_cfx_production_workcompleted_mergetree AS
SELECT
    now() as receiveat,
    `Timestamp`,
    `Topic`,
    `Partition`,
    `Offset`,
    `SchemaId`,
    `SchemaType`,
    `Key`,
    `MessageID`,
    `TransactionID`,
    `MessageType`,
    toFloat64(MessageVersion) AS MessageVersion,
    `MessageTime`,
    `Sender`,
    `Data`,
     --  `Transmission`
FROM EAP.eap_wj3_cdp_d_assy_02_device_cfx_cfx_production_workcompleted;
'''

```