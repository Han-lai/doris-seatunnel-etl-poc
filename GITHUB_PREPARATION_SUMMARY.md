# GitHub 上架準備摘要

## 📋 快速總覽

本文件為 MFG_DP 專案上架 GitHub 的準備工作摘要。

---

## ✅ 已完成項目

1. ✅ **README.md** - 已建立完整的專案說明文件
2. ✅ **.gitignore** - 已建立 Git 忽略檔案清單
3. ✅ **PRE_PUBLISH_CHECKLIST.md** - 已建立上架前檢查清單

---

## ⚠️ 必須處理的敏感資訊（高風險）

### 1. Kafka 憑證
- **檔案**：`doris/seatunnel/kafka_doris.cfg`
- **內容**：`username=\"MFG_DC\" password=\"MFG$DC0924\"`
- **處理**：替換為佔位符

### 2. PostgreSQL 憑證
- **檔案**：`doris/postgres/docker-compose.yaml`
- **內容**：`POSTGRES_PASSWORD: passw0rd`
- **處理**：替換為佔位符

### 3. 內部 IP 位址
- **多個檔案**包含內部 IP（10.136.x.x, 10.146.x.x）
- **處理**：替換為 `<host>` 佔位符

### 4. GitLab 內部 URL
- **檔案**：`doris/README.md`, `Postgresdb/README.md`
- **內容**：`https://gitlab.deltaww.com/...`
- **處理**：移除或替換為 GitHub URL

### 5. Git 歷史記錄
- **資料夾**：`doris/.git`, `Postgresdb/.git`
- **處理**：檢查 commit 歷史，必要時清理

---

## 🔧 建議處理項目（中風險）

1. **WBS 檔案**：檢查 `wbs.xlsx`, `數據中台POC1_WBS.xlsx` 是否包含商業機密
2. **大型二進位檔案**：移除 `doris_resource_tar/apache-doris-2.0.12-bin-x64.tar.gz`
3. **測試資料**：檢查 CSV 檔案是否包含真實資料
4. **Docker Volume 路徑**：將 `/mnt/data/mfg_dp/` 改為相對路徑

---

## 📝 建議新增檔案

### LICENSE
建議使用 MIT License：

```
MIT License

Copyright (c) [year] [fullname]

Permission is hereby granted, free of charge, to any person obtaining a copy
of this software and associated documentation files (the "Software"), to deal
in the Software without restriction, including without limitation the rights
to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
copies of the Software, and to permit persons to whom the Software is
furnished to do so, subject to the following conditions:

The above copyright notice and this permission notice shall be included in all
copies or substantial portions of the Software.

THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
SOFTWARE.
```

---

## 🛠️ 自動化掃描建議

在推送前執行以下工具：

```bash
# 1. 安裝 gitleaks
brew install gitleaks  # macOS
# 或
wget https://github.com/gitleaks/gitleaks/releases/download/v8.18.0/gitleaks_8.18.0_linux_x64.tar.gz

# 2. 掃描敏感資訊
gitleaks detect --source . --verbose --report-path gitleaks-report.json

# 3. 檢查結果
cat gitleaks-report.json
```

---

## 📦 GitHub Repository 設定建議

### Repository Description
```
POC configurations for manufacturing data platform using Apache Doris, SeaTunnel, and Kafka. Includes Docker deployments, ETL pipeline configs for MES/EAP data integration, and TPC-H benchmark setup.
```

### Topics (Tags)
```
apache-doris, seatunnel, kafka, clickhouse, postgresql, tpc-h, etl, data-pipeline, docker-compose, manufacturing, olap, poc, data-platform, mes
```

### Repository Settings
- ✅ Public repository
- ✅ Initialize with README (已有)
- ✅ Add .gitignore (已建立)
- ✅ Choose a license (建議 MIT)
- ❌ 不啟用 Issues（因為不維護）
- ❌ 不啟用 Wiki
- ✅ 在 About 區塊標註 "Archived - Not actively maintained"

---

## 🚀 上架步驟

### 1. 本地準備
```bash
# 1. 敏感資訊已自動處理完成 ✅
# 2. 大型檔案已加入 .gitignore（保留在本地，不上傳）✅

# 3. 移除 Git 子模組歷史（如果存在）
rm -rf doris/.git Postgresdb/.git

# 4. 初始化新的 Git repository
git init
git add .
git commit -m "Initial commit: Manufacturing Data Platform POC"
```

### 2. 建立 GitHub Repository
1. 前往 GitHub 建立新 repository
2. 名稱建議：`manufacturing-data-platform-poc` 或 `mfg-dp-poc`
3. 設定為 Public
4. 不要初始化 README（本地已有）

### 3. 推送到 GitHub
```bash
git remote add origin https://github.com/<username>/<repo-name>.git
git branch -M main
git push -u origin main
```

### 4. 後續設定
1. 在 GitHub 設定 Repository description 和 topics
2. 在 About 區塊加入 "⚠️ Archived - Not actively maintained"
3. 考慮在 Settings 中將 repository 標記為 Archived

---

## ⚡ 快速檢查清單

上架前最後確認：

- [x] 已移除所有硬編碼密碼 ✅
- [x] 已替換所有內部 IP 位址 ✅
- [x] 已移除 GitLab 內部 URL ✅
- [ ] 已檢查 WBS 檔案內容（需手動確認）
- [x] 已將大型二進位檔案加入 .gitignore ✅
- [ ] 已移除 Git 子模組歷史（需手動執行）
- [ ] 已建立 LICENSE 檔案（需手動建立）
- [ ] 已執行自動化掃描工具（建議執行）
- [x] 已確認 README.md 內容正確 ✅
- [x] 已確認 .gitignore 涵蓋所有敏感檔案 ✅

---

## 📞 需要協助？

如有疑問，請參考：
- **詳細檢查清單**：`PRE_PUBLISH_CHECKLIST.md`
- **專案說明**：`README.md`

---

**最後提醒**：一旦推送到 GitHub，資料即使刪除也可能被他人保存。請務必在首次推送前完成所有檢查！
