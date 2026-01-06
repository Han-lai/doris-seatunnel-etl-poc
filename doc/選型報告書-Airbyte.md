# 選型報告書-Airbyte
## 3.1 數據匯流(Data Ingestion)

目前，我們選擇了開源數據匯流工具 SeaTunnel 和 Airbyte，以評估和測試其 Extract 與 Load 功能。評估範圍將涵蓋以下幾個方面：

1. 數據處理的基本特性與類型
2. 效能表現
3. 支援的資料來源與目標
4. 維護性

### 3.1.2 Airbyte 評估
#### 3.1.2.1 Airbyte 簡介
Airbyte 是一款開源的資料整合工具，用於輕鬆地將資料從多種來源同步到多個目的地。無論是結構化資料（如 MySQL、Oracle）還是非結構化資料（如 MongoDB），Airbyte 都能夠處理。其支援實時和非實時的資料傳輸，並提供多種資料增量模式以適應不同的需求

Airbyte具備Connector連接器將資料從 Source端導入Destination 端

Airbyte 主要組件介紹
       
* Connector連接器
    * 定義：
    Connector 是一個組件，用於在 Source 和 Destination 之間移動數據。 Airbyte 連接器的版本，有社區版和市場版可供選擇。Community 版本通常包括開源連接器，而 Market 版本則提供額外的高級連接器和增強的支援。

    * 特性：
        * 模塊化設計：分為 Source Connector 和 Destination Connector，分別負責數據提取和寫入。
        * 可擴展性：支持 Custom Connector自定義連接器開發，開發者可以使用 Airbyte SDK 或修改現有 Docker 映像來滿足特殊需求。
        * 開源框架：基於開源架構，易於集成和二次開發。
        * 高效數據同步：支持增量同步和全量同步兩種模式，提高同步效率。

* Source 
    * 定義：
       數據來源的組件，負責從外部系統（例如 API、文件、數據庫或數據倉庫）中提取數據。
    * 特性：
        * 支持多種來源：支持的來源範圍廣泛，包括常見的雲服務（如 Salesforce、Google Sheets）和資料庫（如 MySQL、PostgreSQL）。
        * 配置靈活：
        用戶可設置認證信息（如 API 金鑰、用戶名和密碼）以及過濾參數（例如開始同步的日期）。
        * 數據結構檢測：
        提供來源目錄（Source Catalog），以確保提取的數據結構清晰且可用。
* Destination
    * 定義：
        數據目標的組件，負責將提取的數據載入到目標系統（如數據倉庫、數據湖、資料庫或分析工具）。
    * 特性：
        * 多樣化目標支持：支持的目標包括 BigQuery、Snowflake、Redshift 等熱門平台。
        * 數據格式轉換：
        在載入過程中進行必要的數據規範化或轉換。
        目標目錄管理：提供目標目錄（Destination Catalog），確保數據流映射到正確的名稱空間和表結構。
 

#### 3.1.2.2 安裝與使用方式
* 安裝內容請參閱附錄-Airbyte 安裝手冊
#### 3.1.2.3 測試案例說明

#### 目標
為了確認 Airbyte 是否能穩定執行數據提取（Extract）與載入（Load）功能，我們設計測試場景，模擬實際環境下的數據流處理需求。

#### 測試方法
通過連接不同的數據來源（如 RabbitMQ、Kafka），並將數據載入到目標數據庫（如 Doris、S3），檢查 Airbyte 的功能是否符合預期。
#### 驗證標準
處理的數據量、正確性、錯誤處理機制等是否達到預期目標。

#### 測試環境-待更改
**硬體環境-Delta Local VM**：
- CPU: 8 核
- 記憶體: 16GB
- 磁碟空間: 100GB HDD

**軟體環境**：
- 作業系統: Ubuntu 20.04
- Apache Seatunnel 版本: 2.3.7
- Clickhouse 版本: 23.8.14
- 部署方式: Docker

----
#### 案例一
測試案例一以 `Kafka → Doris`  為目標，並測試部分 Transform 功能。
實際測試流程請參閱附錄 — **Airbyte 測試案例**。

#### Connector 階段說明
1. Source Connector ： 使用 Marketplace版本 kafka v0.2.5

2. Destination Connector ： 使用 Custom版本 Apache-doris v0.2.5

#### Source 測試階段說明：
支援 Kafka 作為源連接器，設置一個管道用於從 Kafka 中提取資料並將其發送到各個目的地。設置包括將 Kafka 定義為源、指定 Kafka 代理 URL、身份驗證憑證和要從中提取數據的主題
1. 確保 Source Connector 可用：
    * 目前 僅 Community 版本

2. 確保 Airbyte 正確連接到 Kafka 集群：
    ![](/uploads/upload_959499700a3aaeb83a65822e774c6a3f.png)
驗證 SeaTunnel 配置中 Kafka 的連接參數（如 Kafka 代理 URL、身份驗證信息）是否正確。
3. 確保 Airbyte 訂閱並消費指定 Topic：
    檢查 Airbyte 配置的 Kafka Topic，並確保它能成功接收來自該 Topic 的消息。


#### Destination 階段說
本次案例Destination 選擇為Apache Doris，
1. 確保 Destination Connector 可用：
    * 官方目前將doris的connector為ARCHIVED，故airbyte UI介面上並無可用的Doris connector
    * 自行拉取image 建立connector，參考[Airbyte GITHUB](https://github.com/airbytehq/connector-archive/tree/main/airbyte-integrations/connectors/destination-doris)connector-archive區建立
![](/uploads/upload_786fdda58b031b69f8c9bec32910b240.png)

2. 確保 Airbyte 正確連接到 Doris 集群：
- 設置 doris 目的地連接參數，包括主機、端口和資料庫名稱。
    * HttpPort (8030) 用於管理和維護層面的操作，例如元數據的管理或執行一些不涉及大數據量的操作。
    * QueryPort (9030) 則是實際進行數據處理的端口，負責處理所有的SQL查詢請求，這些請求通常與數據的讀寫操作有關。

    |連線資訊 | 
    | -------- | 
    | ![](/uploads/upload_d49527efe051c285b603badd8b0d2d15.png)   | 

3. 連線資訊

| Column 1 | SOURCE 連線設定                                                | DEST.連線設定 |
| -------- | --------------------------------------------------------- | -------- |
| SASL PLAINTEXT     | ![](/uploads/upload_c8c95cf1a94051dbd2ac54590fa6e727.png)  |![](/uploads/upload_cab121488dc23b2bc544535f93c7bb1e.png)
| PLAINTEXT     |  ![](/uploads/upload_2614de36cd2b28a5094235a5b0eb5e58.png)|![](/uploads/upload_59be4e2e015957f08593721a0daae42a.png)|
#### 同步策略
   - 選擇全量同步或增量同步。
   - 配置同步排程（如每小時、每日同步）
    
    
#### 測試結果
* 連線成功，但資料未導入


----

#### 測試案例
測試案例一以 `postgresdb → Doris`  為目標，並測試部分 Transform 功能。
實際測試流程請參閱附錄 — **Airbyte 測試案例**。
#### Connector 階段說明
1. Source Connector ： 使用 community版本 PostgreSQL v3.6.10
3. Destination Connector ： 使用 Custom版本 Apache-doris latest
#### Source 測試階段說明：
   - 設置 PostgreSQL 資料源連接參數，包括主機、端口、用戶名、密碼和資料庫名稱。
   - 選擇需要同步的表格。
1. 確保 Source Connector 可用：
    * 目前 僅 Community 版本


#### Destination 階段說明
本次案例Destination 選擇為Apache Doris，
1. 確保 Destination Connector 可用：
    * 官方目前將doris的connector為ARCHIVED，故airbyte UI介面上並無可用的Doris connector
    * 自行拉取image 建立connector，參考[Airbyte GITHUB](https://github.com/airbytehq/connector-archive/tree/main/airbyte-integrations/connectors/destination-doris)connector-archive區建立
![](/uploads/upload_786fdda58b031b69f8c9bec32910b240.png)

2. 確保 Airbyte 正確連接到 Doris 集群：
當配置Airbyte連接Doris時，需要確保這些端口在Doris伺服器上開放，並且在Airbyte中設定正確的端口號碼，以便順利完成數據同步工作。
    * HttpPort (8030) 用於管理和維護層面的操作，例如元數據的管理或執行一些不涉及大數據量的操作。
    * QueryPort (9030) 則是實際進行數據處理的端口，負責處理所有的SQL查詢請求，這些請求通常與數據的讀寫操作有關。

    |連線資訊 | 
    | -------- | 
    | ![](/uploads/upload_d49527efe051c285b603badd8b0d2d15.png)   | 

3. 連線資訊

| Column 1 | SOURCE 連線設定                                                | DEST.連線設定 |
| -------- | --------------------------------------------------------- | -------- |
| SASL PLAINTEXT     | ![](/uploads/upload_c8c95cf1a94051dbd2ac54590fa6e727.png)  |![](/uploads/upload_cab121488dc23b2bc544535f93c7bb1e.png)
| PLAINTEXT     |  ![](/uploads/upload_2614de36cd2b28a5094235a5b0eb5e58.png)|![](/uploads/upload_59be4e2e015957f08593721a0daae42a.png)|
#### 同步策略
   - 選擇全量同步或增量同步。
   - 配置同步排程（如每小時、每日同步）

    
#### 測試結果
* 連線成功，但資料未導入


