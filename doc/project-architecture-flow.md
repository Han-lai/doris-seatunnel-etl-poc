# Doris-SeaTunnel ETL POC 專案架構與資料流

> 用途：作為簡報、架構圖與資料流示意圖的繪製 prompt。
> 專案定位：技術選型驗證與本地 Docker POC，不是生產環境架構。

## 0. 結案報告定義的專案目的

### 業務背景與痛點

```text
製造域存在多個獨立資料系統
  │
  ├─ 機聯 / IoT：設備狀態、設備產出量、停機時間
  ├─ MES：線別主檔、工單、生產資訊
  └─ PLM：產品主檔與產品維度
  │
  ▼
資料孤島、資料格式不一致、資料重複與重工
  │
  ▼
資料取得不易，資料工程重複開發，資料資產無法重用
```

### 期望解決方案

```text
機聯 / IoT + MES + PLM
      │
      ▼
製造域數據中台
      │
      ├─ 統一資料入口
      ├─ 標準化資料格式
      ├─ 資料匯流與轉換
      ├─ 數據治理與品質管理
      └─ API / Database / File 等資料接口
      │
      ▼
BI 報表、查詢分析、設備效率分析、生產效率分析
```

### POC1 使用者故事

```text
WJ3 C02 / C03、WJ2 C11 線別的製造資料
      │
      ├─ 機聯 CFX：設備狀態、產出量、停機時間
      ├─ MES：線別、工單與生產資訊
      └─ PLM：產品主檔與產品維度
      │
      ▼
整合時間、產品、廠區、線別與設備維度
      │
      ▼
產出 BI 分析：
• 生產線效率
• 設備生產效率
• 設備利用率與維護需求
• 生產問題與瓶頸識別
• 資源分配與產能利用率
```

### POC1 在整體中台建置中的位置

```text
POC1：0 → 1 可行性驗證
  • 各功能模組工具選型
  • 串接製造域資料來源
  • 驗證資料匯流、格式轉換與資料上架
  • 建立基礎架構與測試結果
    │
    ▼
後續建置：1 → N 場域擴散與客製功能開發
  • WJ 數據中台第一階段建置
  • 使用者測試與導入輔導
  • 更多製造場域與資料應用
```

### POC1 的功能模組分工

```text
資料擷取 / 匯流 / 格式轉換  → Apache SeaTunnel（本 repository 主要實作）
排程控制                   → Apache DolphinScheduler（結案報告選型）
數據湖泊 / OLAP 儲存         → Apache Doris（本 repository 主要實作）
數據接口 / Semantic Layer    → Cube.js（後續資料應用方向）
數據權限                   → Apache Ranger（規劃中的治理能力）
```

> 本 repository 主要聚焦於 SeaTunnel、Kafka、ClickHouse、PostgreSQL 與 Doris 的資料匯流和儲存驗證；排程、接口、權限、完整 BI 與生產級維運屬於結案報告的整體中台規劃，不應在簡報中誤畫成已完成的本次 ETL 實作。

### POC1 執行規模

```text
4 台 VM
  ↓
部署並運行 20+ 個數據平台相關服務
  ↓
保留安裝步驟、設定方式、測試結果與故障排除紀錄
```

> 結案報告中的「3+ 資料源」代表製造域整體使用情境（機聯 / MES / PLM）；本 repository 則以 Kafka、ClickHouse、PostgreSQL 建立可重現的資料匯流與儲存 POC。

## 1. 簡報敘事主軸

本專案不是把三種資料來源放在同一條流程中，而是用不同資料流驗證不同問題：

```text
問題定義
  ↓
建立不同測試資料源
  ↓
以 SeaTunnel 或 Doris Routine Load 處理
  ↓
寫入 Apache Doris
  ↓
驗證資料正確性、轉換能力、吞吐量與查詢能力
```

簡報建議依照以下順序說明：

```text
1. 為什麼需要資料整合平台？
2. 不同資料來源的資料特性是什麼？
3. SeaTunnel 如何抽取、轉換與載入？
4. Doris 如何接收、儲存與查詢？
5. 每一條測試管線驗證了什麼？
6. 為什麼最後選擇 SeaTunnel，而不是 Airbyte？
```

## 2. 測試目標總覽

本專案可整理為五種測試目標。每個目標都有不同的資料來源、處理模式與驗證結果。

| 編號 | 測試目標 | 核心問題 | 主要資料流 | 關鍵驗證項目 |
|---|---|---|---|---|
| T1 | 即時製造資料整合 | 能否穩定接收 MES / EAP / CFX 訊息？ | Kafka → SeaTunnel → Doris | Topic、Offset、Partition、Stream、吞吐量 |
| T2 | 複雜 JSON 與 CDC 轉換 | 能否保留巢狀資料並轉成可查詢欄位？ | Kafka → JsonPath / Filter / SQL → Doris | 欄位映射、JSON 結構、錯誤資料處理 |
| T3 | 歷史資料批次搬遷 | 能否將既有大量資料搬到 Doris？ | ClickHouse → SeaTunnel → Doris | Batch、WHERE、分區、批次大小、2PC |
| T4 | OLAP 儲存與查詢效能 | Doris 是否適合作為分析型數據倉儲？ | TPC-H → PostgreSQL → SeaTunnel → Doris | 大資料量載入、查詢、Key Model、Partition |
| T5 | Kafka 直接載入與工具選型 | SeaTunnel 與其他方案的差異？ | Kafka → Routine Load → Doris；Airbyte → Doris | 架構複雜度、轉換彈性、Connector、穩定性 |

### 測試目標與資料來源的區分

```text
Kafka
  ├─ T1：驗證即時資料流與持續消費
  ├─ T2：驗證 JSON / CDC 解析與轉換
  └─ T5：比較 SeaTunnel 與 Doris Routine Load

ClickHouse
  └─ T3：驗證歷史資料批次搬遷

PostgreSQL / TPC-H
  └─ T4：驗證關聯式資料進入 Doris 後的 OLAP 能力
```

### 測試結果應回答的問題

```text
資料是否有成功讀取？
資料是否完整寫入？
資料是否能正確轉換？
巢狀 JSON 是否能保留或展開？
大量資料是否能穩定載入？
Doris 是否能支援分區、分桶與分析查詢？
SeaTunnel 是否比直接載入或 Airbyte 更適合？
```

## 3. 專案整體資料流

```text
┌──────────────────────────────────────────────────────────────────────────────┐
│                              資料來源層                                      │
└──────────────────────────────────────────────────────────────────────────────┘

   即時製造資料                 歷史資料                    基準測試資料
┌──────────────────┐       ┌──────────────────┐       ┌──────────────────┐
│ Kafka             │       │ ClickHouse       │       │ PostgreSQL        │
│ MES / EAP / CFX   │       │ EAP database     │       │ TPC-H tables      │
│ JSON / CDC        │       │ PK_MessageBody  │       │ 關聯式測試資料     │
└────────┬─────────┘       └────────┬─────────┘       └────────┬─────────┘
         │                          │                          │
         │ Stream / Batch           │ Batch                    │ Batch
         └──────────────────────────┼──────────────────────────┘
                                    ▼
┌──────────────────────────────────────────────────────────────────────────────┐
│                         Apache SeaTunnel ETL 層                               │
│                                                                              │
│  Source                                                                     │
│  • Kafka Source                                                             │
│  • ClickHouse Source                                                        │
│  • PostgreSQL Source                                                        │
│                                                                              │
│  Transform                                                                  │
│  • JSON schema 解析                                                         │
│  • JsonPath：擷取巢狀 JSON 欄位                                              │
│  • Filter：過濾不需要的資料                                                   │
│  • SQL：欄位選擇、重新命名、計算與條件處理                                     │
│  • TimestampFormat：時間格式轉換                                             │
│                                                                              │
│  Sink                                                                       │
│  • Doris Sink                                                               │
│  • HTTP Stream Load                                                         │
│  • Batch size / Checkpoint / 2PC                                             │
└──────────────────────────────────┬───────────────────────────────────────────┘
                                   ▼
┌──────────────────────────────────────────────────────────────────────────────┐
│                            Apache Doris 數據倉儲                              │
│                                                                              │
│  FE：SQL、Metadata、叢集管理                                                  │
│  BE：資料寫入、儲存、查詢計算、Compaction                                      │
│                                                                              │
│  資料表特性：                                                                 │
│  • Unique Key / Duplicate Key                                                │
│  • Dynamic Partition：依月份分區                                             │
│  • Hash Distribution / Auto Bucket                                           │
│  • JSON、VARIANT、TEXT 等欄位                                                 │
│  • Stream Load 與 Doris Sink 寫入                                             │
└───────────────────────┬───────────────────────┬──────────────────────────────┘
                        │                       │
                        ▼                       ▼
              ┌──────────────────┐    ┌──────────────────────────┐
              │ OLAP 查詢與分析    │    │ 歷史資料 / 冷資料保存      │
              │ CFX 製造資料分析   │    │ Storage Policy / S3 選配  │
              │ TPC-H 效能測試     │    │ Repository 只有相關設定    │
              └──────────────────┘    └──────────────────────────┘
```

## 4. 主流程：Kafka → SeaTunnel → Doris

```text
┌──────────────────────┐
│ MES / EAP / CFX 系統  │
│ 製造設備與生產事件     │
└──────────┬───────────┘
           │ 發送 JSON / CDC 訊息
           ▼
┌──────────────────────┐
│ Kafka Cluster         │
│                      │
│ • 多個 Broker          │
│ • 多個 Topic           │
│ • Partition            │
│ • Offset               │
│ • SASL/PLAIN 或明文    │
└──────────┬───────────┘
           │ SeaTunnel Kafka Source
           │ auto.offset.reset = earliest / latest
           ▼
┌──────────────────────┐
│ Kafka Source          │
│                      │
│ • 讀取 Topic           │
│ • 解析 JSON            │
│ • 建立欄位 Schema      │
│ • 控制 poll records    │
└──────────┬───────────┘
           ▼
┌──────────────────────┐
│ Transform Pipeline    │
│                      │
│ 1. JsonPath           │
│    解析 columnInfo、   │
│    MessageBody 等欄位  │
│                      │
│ 2. Filter             │
│    移除不符合條件資料  │
│                      │
│ 3. SQL                │
│    欄位選取、改名、     │
│    IFNULL、NOW()       │
│                      │
│ 4. TimestampFormat     │
│    時間戳格式轉換       │
└──────────┬───────────┘
           ▼
┌──────────────────────┐
│ Doris Sink            │
│                      │
│ • JSON line 格式       │
│ • doris.batch.size     │
│ • Checkpoint 提交      │
│ • 可啟用 2PC           │
│ • Schema 自動建立      │
│ • Append / Delete      │
└──────────┬───────────┘
           │ HTTP Stream Load
           ▼
┌──────────────────────┐
│ Doris FE               │
│ 接收 SQL / Load 請求   │
└──────────┬───────────┘
           ▼
┌──────────────────────┐
│ Doris BE               │
│ 寫入資料、分區、索引    │
│ Compaction、查詢計算   │
└──────────────────────┘
```

### Kafka 流程模式

```text
Batch Mode：
Kafka Topic → 指定 Offset 範圍 → SeaTunnel 處理 → 任務完成 → Doris

Stream Mode：
Kafka Topic → 持續監控新訊息 → Checkpoint → SeaTunnel Transform → Doris
```

### Kafka 資料類型

```text
CFX 製造訊息：
CFX.Heartbeat
CFX.ResourcePerformance.StationParametersModified
CFX.ResourcePerformance.StationStateChanged
CFX.Production.UnitsArrived
CFX.Production.UnitsDeparted

CDC 訊息：
OWNER / TABLE / OP / SCN / ROWID / DBNAME
columnsBefore / columnsAfter / columnInfo
```

## 5. 歷史資料流程：ClickHouse → SeaTunnel → Doris

```text
┌────────────────────────────┐
│ ClickHouse                  │
│ database = EAP              │
│ table = PK_MessageBody_data │
└──────────────┬─────────────┘
               │ SQL SELECT
               │ LIMIT / WHERE / LineName 條件
               ▼
┌────────────────────────────┐
│ SeaTunnel ClickHouse Source │
│                            │
│ • Batch 模式                │
│ • 讀取歷史 CFX 訊息          │
│ • socket timeout 調整        │
└──────────────┬─────────────┘
               ▼
┌────────────────────────────┐
│ SeaTunnel Doris Sink        │
│                            │
│ • MessageBody 保留為 TEXT   │
│ • VARIANT JSON 測試          │
│ • APPEND_DATA               │
│ • doris.batch.size          │
│ • 可啟用 2PC                │
└──────────────┬─────────────┘
               │ HTTP Stream Load
               ▼
┌────────────────────────────┐
│ Doris test / test_variant   │
│                            │
│ • pkmsg_autobkt             │
│ • pkmsg_autobkt_c02         │
│ • PK_MessageBody_data       │
└────────────────────────────┘
```

資料處理重點：

```text
ClickHouse 原始欄位
  ↓
TimeStamp、UniqueID、LineName、MessageName、Source、Target、RequestID、MessageBody
  ↓
SeaTunnel 欄位映射與批次載入
  ↓
Doris 分區表與 JSON / TEXT 欄位
```

## 6. 基準測試流程：TPC-H → PostgreSQL → Doris

```text
┌──────────────────────┐
│ TPC-H dbgen           │
│ 產生 nation、region、  │
│ customer、orders 等資料│
└──────────┬───────────┘
           ▼
┌──────────────────────┐
│ PostgreSQL 13         │
│ docker_postgres       │
│ Port：9432 → 5432     │
│ TPC-H 關聯式資料表     │
└──────────┬───────────┘
           │ SeaTunnel Batch Source
           ▼
┌──────────────────────┐
│ Apache SeaTunnel      │
│ PostgreSQL Source      │
│ 欄位讀取與資料同步     │
└──────────┬───────────┘
           ▼
┌──────────────────────┐
│ Apache Doris          │
│ OLAP 表與查詢測試      │
└──────────┬───────────┘
           ▼
┌──────────────────────┐
│ TPC-H 查詢效能驗證     │
│ 大量資料分析測試       │
└──────────────────────┘
```

## 7. 直接流程：Kafka → Doris Routine Load

此流程不經 SeaTunnel，由 Doris 直接持續消費 Kafka。

```text
┌──────────────────────┐
│ Kafka Topic           │
│ CFX_CFX_Production_   │
│ WorkCompleted         │
└──────────┬───────────┘
           │ Kafka protocol
           ▼
┌──────────────────────┐
│ Doris Routine Load    │
│                      │
│ • 建立 Routine Load Job│
│ • 指定 Kafka Broker    │
│ • 指定 Topic           │
│ • 指定 Partition       │
│ • 設定 Consumer Group  │
│ • 批次列數與大小限制    │
└──────────┬───────────┘
           ▼
┌──────────────────────┐
│ Doris Table           │
│ test_routineload_tbl  │
│                      │
│ • Unique Key           │
│ • Month Partition      │
│ • Hash Distribution    │
└──────────────────────┘
```

Routine Load 的管理流程：

```text
Routineload.py
  ↓ HTTP POST /api/query/{database}
CREATE TABLE IF NOT EXISTS
  ↓
CREATE ROUTINE LOAD
  ↓
Doris 持續從 Kafka 消費並寫入資料表
```

## 8. Doris 內部資料處理層

```text
┌──────────────────────────────────────────┐
│ Doris FE                                  │
│                                          │
│ • 接收 SeaTunnel Stream Load               │
│ • 接收 Routine Load 設定                   │
│ • SQL Query                                │
│ • Schema / Partition / Tablet Metadata    │
│ • 管理 FE / BE 節點                        │
└──────────────────┬───────────────────────┘
                   ▼
┌──────────────────────────────────────────┐
│ Doris BE                                  │
│                                          │
│ • 接收與儲存資料                           │
│ • Hash 分桶與資料分區                      │
│ • Unique Key Merge-on-Write               │
│ • Duplicate Key 寫入                      │
│ • Compaction                              │
│ • OLAP 查詢計算                           │
└──────────────────┬───────────────────────┘
                   ▼
┌──────────────────────────────────────────┐
│ 儲存策略                                   │
│                                          │
│ • Hot data：本地 BE storage                │
│ • Cold data：S3 Storage Policy 選配         │
│ • Dynamic Partition：以月份管理             │
└──────────────────────────────────────────┘
```

## 9. Docker 部署關係

```text
┌─────────────────────────────────────────────────────────────────┐
│ Local VM / Docker Compose                                       │
│                                                                 │
│  ┌─────────────────────┐       ┌─────────────────────────────┐  │
│  │ SeaTunnel Cluster    │       │ SeaTunnel Job Submitter     │  │
│  │                      │◄──────│ seatunnel.sh --config       │  │
│  │ Port 9801 → 5801     │       │ 指定 .cfg / .config 管線      │  │
│  └──────────┬──────────┘       └─────────────────────────────┘  │
│             │                                                    │
│             │ ETL job                                            │
│             ▼                                                    │
│  ┌─────────────────────┐       ┌─────────────────────────────┐  │
│  │ Doris FE             │──────▶│ Doris BE                    │  │
│  │ SQL / Metadata       │       │ Storage / Compute            │  │
│  │ Port 8030 / 9030     │       │ Port 8040                    │  │
│  └─────────────────────┘       └─────────────────────────────┘  │
│                                                                 │
│  PostgreSQL：獨立 Docker Compose                                │
│  Kafka / ClickHouse：以外部服務 endpoint 連接                     │
└─────────────────────────────────────────────────────────────────┘
```

## 10. 未採用的 Airbyte 評估流程

```text
┌──────────────────────┐
│ Kafka / PostgreSQL    │
└──────────┬───────────┘
           ▼
┌──────────────────────┐
│ Airbyte               │
│ 評估階段              │
│ EL / Connector 模式    │
└──────────┬───────────┘
           ▼
┌──────────────────────┐
│ Doris Connector       │
│ 官方已 ARCHIVED       │
│ 測試時資料未成功導入   │
└──────────────────────┘

結論：不納入正式主流程，改採 Apache SeaTunnel。
```

## 11. 主要資料流對照表

| 流程 | 來源 | 處理方式 | 目的地 | 模式 | 狀態 |
|---|---|---|---|---|---|
| A | Kafka MES/EAP/CFX | JsonPath、Filter、SQL | Doris | Stream / Batch | 主要採用 |
| B | ClickHouse EAP | SQL SELECT、批次同步 | Doris | Batch | 已驗證 |
| C | PostgreSQL TPC-H | 批次讀取與載入 | Doris | Batch | 基準測試 |
| D | Kafka CFX | Doris Routine Load | Doris | 持續消費 | 直接整合測試 |
| E | Kafka / PostgreSQL | Airbyte Connector | Doris | Batch / EL | 評估後未採用 |

## 12. 專案資料夾與架構角色

```text
doris-seatunnel-etl-poc/
│
├── doris/
│   ├── doris/                  Doris FE / BE Docker 部署
│   ├── seatunnel/              SeaTunnel ETL 管線設定
│   │   ├── Kafka/              Kafka Source、JsonPath、SQL 管線
│   │   ├── EAP/                EAP / CFX 多管線設定
│   │   ├── kafka.cfg           Kafka → Doris 測試
│   │   ├── kafka_doris.cfg     Kafka → Doris 管線
│   │   ├── clickhouse_doris.cfg ClickHouse → Doris 管線
│   │   └── dockercompose.yml   SeaTunnel Cluster / Job Submitter
│   ├── postgres/               PostgreSQL TPC-H Docker 環境
│   └── kafka_RoutineLoad/      Kafka → Doris 直接載入測試
│
├── Postgresdb/                 TPC-H 資料載入 PostgreSQL 的腳本
├── TPC-H V3.0.1/               TPC-H dbgen 基準資料產生工具
├── kafka/                      Kafka 測試欄位與問題紀錄
├── Airbyte/                    Airbyte 評估與部署檔案
└── doc/                        架構、選型、測試與問題紀錄
```

## 13. 簡報用一句話版本

```text
Kafka 提供 MES / EAP 即時製造資料，ClickHouse 提供歷史資料，PostgreSQL 提供 TPC-H 基準資料；
三種來源透過 Apache SeaTunnel 進行批次或串流抽取、JSON 解析、欄位轉換與資料清洗，
再經由 Doris Sink / HTTP Stream Load 寫入 Apache Doris，最後由 Doris FE / BE 提供分區儲存、
OLAP 查詢與歷史資料分析；另有一條 Kafka 直接進入 Doris Routine Load 的替代驗證流程。
```

## 14. 範圍與限制

```text
已包含：
• Kafka → Doris 即時 / 批次資料流
• ClickHouse → Doris 歷史資料遷移
• PostgreSQL → Doris TPC-H 批次測試
• Kafka → Doris Routine Load
• Doris FE / BE Docker 部署
• JSON、VARIANT、TEXT 與複雜 MessageBody 驗證

未包含：
• Airflow DAG 與 Dynamic Task Mapping
• Prometheus / Grafana 監控與告警
• MinIO 實際部署
• 生產環境 HA、負載平衡與災難復原
• 完整資料品質管理與資料血緣系統
```
