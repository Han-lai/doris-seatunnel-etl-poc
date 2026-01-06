# GitHub 上架前人工檢查清單

## ⚠️ 敏感資訊檢查

在公開此專案到 GitHub 前，請逐項確認以下內容：

---

## 1. 硬編碼憑證（Hard-coded Credentials）

### 🔴 高風險項目（必須處理）

- [ ] **Kafka 帳號密碼**
  - 檔案：`doris/seatunnel/kafka_doris.cfg`
  - 內容：`username=\"MFG_DC\" password=\"MFG$DC0924\"`
  - 建議：替換為 `username=\"<KAFKA_USERNAME>\" password=\"<KAFKA_PASSWORD>\"`

- [ ] **PostgreSQL 帳號密碼**
  - 檔案：`doris/postgres/docker-compose.yaml`
  - 內容：`POSTGRES_USER: admin`, `POSTGRES_PASSWORD: passw0rd`
  - 建議：替換為 `POSTGRES_USER: <username>`, `POSTGRES_PASSWORD: <password>`

- [ ] **pgAdmin 帳號密碼**
  - 檔案：`doris/postgres/docker-compose.yaml`
  - 內容：`PGADMIN_DEFAULT_EMAIL: admin@example.comman`, `PGADMIN_DEFAULT_PASSWORD: admin`
  - 建議：替換為範例值或移除

- [ ] **PostgreSQL 連線資訊**
  - 檔案：`Postgresdb/tpch2postgresdb.py`
  - 內容：硬編碼的 host、port、database、user、password
  - 建議：替換為 `'your_postgres_host'`, `'your_postgres_password'` 等佔位符

---

## 2. 內部系統 IP 位址與主機名稱

### 🟡 中風險項目（建議處理）

- [ ] **Kafka Broker IP**
  - 檔案：`doris/seatunnel/kafka_doris.cfg`
  - 內容：`10.146.192.81:9092,10.146.192.82:9092,10.146.192.83:9092`
  - 建議：替換為 `<kafka-broker-1>:9092,<kafka-broker-2>:9092,<kafka-broker-3>:9092`

- [ ] **Kafka Broker IP (EAP)**
  - 檔案：`doris/seatunnel/EAP/eap_cfx_workcomplete.config`
  - 內容：`10.136.218.207:9092`
  - 建議：替換為 `<kafka-broker>:9092`

- [ ] **Doris FE IP**
  - 檔案：`doris/seatunnel/kafka_doris.cfg`, `doris/seatunnel/clickhouse_doris.cfg`, `doris/seatunnel/EAP/*.config`
  - 內容：`10.136.147.130:8030`
  - 建議：替換為 `<doris-fe-host>:8030`

- [ ] **ClickHouse IP**
  - 檔案：`doris/seatunnel/clickhouse_doris.cfg`
  - 內容：`10.136.218.207:8123`
  - 建議：替換為 `<clickhouse-host>:8123`

- [ ] **PostgreSQL IP**
  - 檔案：`Postgresdb/tpch2postgresdb.py`
  - 內容：`host='10.136.159.47'`
  - 建議：替換為 `host='<postgres-host>'`

- [ ] **Docker Volume 路徑**
  - 檔案：`doris/doris/docker-compose.yaml`
  - 內容：`/mnt/data/mfg_dp/doris/...`
  - 建議：替換為相對路徑或通用路徑 `./data/doris/...`

---

## 3. 公司專屬資訊

### 🟡 中風險項目（建議處理）

- [ ] **GitLab 內部 URL**
  - 檔案：`doris/README.md`, `Postgresdb/README.md`
  - 內容：`https://gitlab.deltaww.com/corp/corp/ait/data/mfg_dp.git`
  - 建議：移除或替換為 GitHub URL

- [ ] **Kafka Topic 命名**
  - 檔案：`doris/seatunnel/kafka_doris.cfg`
  - 內容：`MES-IT__WJIAMES__WJ_IA__POC__R_SN_CNF_T`
  - 檔案：`doris/seatunnel/EAP/eap_cfx_workcomplete.config`
  - 內容：`CFX_CFX_Production_WorkCompleted`
  - 建議：評估是否包含公司專屬命名規則，考慮替換為 `<topic-name>`

- [ ] **Doris 資料庫與表格命名**
  - 檔案：多個 SeaTunnel 配置檔案
  - 內容：`test_variant`, `wj_c11_wjadpmes__wj_adp__poc__r_sn_cnf_t`, `ods_eap_workcomplete_U`
  - 建議：評估是否包含公司專屬命名規則

- [ ] **ClickHouse 資料庫與表格**
  - 檔案：`doris/seatunnel/clickhouse_doris.cfg`
  - 內容：`database = "EAP"`, `LineName = 'wj_c02'`
  - 建議：評估是否包含公司專屬資訊

---

## 4. 個人識別資訊（PII）

### 🟢 低風險項目（建議檢查）

- [ ] **Email 地址**
  - 檔案：`doris/postgres/docker-compose.yaml`
  - 內容：`PGADMIN_DEFAULT_EMAIL: admin@example.comman`
  - 建議：確認是否為範例值（目前看起來是範例）

- [ ] **作者資訊**
  - 檔案：所有 Python 檔案
  - 建議：檢查是否有個人姓名、員工編號等資訊

---

## 5. 商業機密與專有資料

### 🟡 中風險項目（建議處理）

- [ ] **WBS 檔案**
  - 檔案：`wbs.xlsx`, `數據中台POC1_WBS.xlsx`
  - 建議：檢查是否包含專案預算、人力配置、商業策略等敏感資訊
  - 考慮：移除或僅保留檔案名稱說明用途

- [ ] **測試資料**
  - 檔案：`doris/data.csv`, `doris/pk_message.csv`, `doris/streamload_example.csv`
  - 建議：檢查是否包含真實生產資料

- [ ] **JSON 測試資料**
  - 檔案：`kafka/test_column.json`
  - 建議：檢查是否包含真實資料結構或敏感欄位

---

## 6. 二進位檔案與大型檔案

### 🟢 低風險項目（建議檢查）

- [ ] **Doris 二進位檔案**
  - 檔案：`doris_resource_tar/apache-doris-2.0.12-bin-x64.tar.gz`
  - 大小：可能超過 GitHub 檔案大小限制（100MB）
  - 建議：移除並在 README 中提供官方下載連結

- [ ] **TPC-H 壓縮檔**
  - 檔案：`doris/postgres/TPCH.tar.gz`
  - 建議：檢查檔案大小，考慮移除並提供官方連結

- [ ] **Doris 打包檔案**
  - 檔案：`doris/doris.tar`, `doris/doris.zip`
  - 建議：檢查檔案大小與必要性

---

## 7. Git 歷史記錄

### 🔴 高風險項目（必須處理）

- [ ] **檢查 Git 歷史**
  - 資料夾：`doris/.git`, `Postgresdb/.git`
  - 建議：檢查 commit 歷史是否包含敏感資訊
  - 考慮：使用 `git filter-branch` 或 `BFG Repo-Cleaner` 清理歷史

- [ ] **檢查 commit message**
  - 建議：確認 commit message 中無敏感資訊、內部專案代號或人名

---

## 8. 其他檢查項目

### 🟢 一般性檢查

- [ ] **移除臨時檔案**
  - 檔案：`Airbyte/~$數據中台POC1_WBS.xlsx`（Excel 臨時檔案）
  - 建議：刪除

- [ ] **Python 虛擬環境**
  - 資料夾：`Postgresdb/postgres_venv/`
  - 建議：加入 `.gitignore` 或移除

- [ ] **空資料夾**
  - 資料夾：`POC/`
  - 建議：移除或加入 `.gitkeep` 說明用途

- [ ] **建立 .gitignore**
  - 建議內容：
    ```
    # Python
    __pycache__/
    *.py[cod]
    *$py.class
    *.so
    .Python
    env/
    venv/
    */venv/
    
    # Docker
    *.log
    
    # IDE
    .vscode/
    .idea/
    
    # OS
    .DS_Store
    Thumbs.db
    
    # Excel temp files
    ~$*.xlsx
    ~$*.xls
    
    # Large binary files
    *.tar
    *.tar.gz
    *.zip
    
    # Data files (optional)
    *.csv
    ```

- [ ] **建立 LICENSE**
  - 建議：選擇適當的開源授權（MIT、Apache 2.0 等）

---

## 檢查工具建議

### 自動化掃描工具

1. **git-secrets**
   ```bash
   git secrets --scan
   ```

2. **truffleHog**
   ```bash
   trufflehog git file://. --only-verified
   ```

3. **detect-secrets**
   ```bash
   detect-secrets scan
   ```

4. **gitleaks**
   ```bash
   gitleaks detect --source . --verbose
   ```

---

## 完成確認

- [ ] 我已逐項檢查上述所有項目
- [ ] 我已使用至少一種自動化工具掃描敏感資訊
- [ ] 我已檢查 Git 歷史記錄
- [ ] 我已建立 .gitignore 檔案
- [ ] 我已建立 LICENSE 檔案
- [ ] 我已更新 README.md 移除內部資訊
- [ ] 我確認此專案可以安全公開

---

**最後提醒：**
一旦推送到 GitHub，即使後續刪除，資料仍可能被他人 fork 或快取。請務必在首次推送前完成所有檢查。
