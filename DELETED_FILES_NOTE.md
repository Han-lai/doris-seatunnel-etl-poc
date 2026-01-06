# 已刪除檔案說明

## ⚠️ 注意

在清理過程中，以下檔案已被刪除。如果你需要這些檔案，請從備份中還原。

## 已刪除的檔案清單

### 1. Excel 臨時檔案
- `Airbyte/~$數據中台POC1_WBS.xlsx`
  - **類型**：Excel 臨時檔案
  - **說明**：這是 Excel 自動產生的臨時檔案，通常在 Excel 檔案開啟時產生
  - **是否需要還原**：❌ 不需要，這是系統自動產生的檔案

### 2. 大型二進位檔案
- `doris_resource_tar/` 整個資料夾
  - **內容**：`apache-doris-2.0.12-bin-x64.tar.gz`
  - **大小**：可能超過 100MB
  - **說明**：Apache Doris 二進位發行版
  - **是否需要還原**：✅ 如果本地開發需要，請還原；但不應上傳到 GitHub
  - **替代方案**：從 [Apache Doris 官網](https://doris.apache.org/download) 重新下載

- `doris/doris.tar`
  - **說明**：Doris 打包檔案
  - **是否需要還原**：視需求而定
  - **替代方案**：如需要，可重新打包

- `doris/doris.zip`
  - **說明**：Doris 打包檔案
  - **是否需要還原**：視需求而定
  - **替代方案**：如需要，可重新打包

## 如何還原

### 方法 1：從備份還原
如果你有備份，請從備份中複製這些檔案回來。

### 方法 2：從 Git 歷史還原（如果之前有 commit）
```bash
# 查看被刪除的檔案
git log --all --full-history -- "doris_resource_tar/*"

# 還原特定檔案
git checkout <commit-hash> -- doris_resource_tar/
```

### 方法 3：重新下載
對於 Apache Doris 二進位檔案，建議從官方網站重新下載：
- 官網：https://doris.apache.org/download
- 版本：2.0.12

## .gitignore 設定

這些檔案類型已加入 `.gitignore`，即使還原後也不會被上傳到 GitHub：

```
# Large binary files (不上傳到 GitHub，但保留在本地)
*.tar
*.tar.gz
*.zip
doris_resource_tar/
doris/doris.tar
doris/doris.zip

# Excel 臨時檔案
~$*.xlsx
~$*.xls
~$*.doc
~$*.docx
```

## 建議

1. **Excel 臨時檔案**：不需要還原，這些是系統自動產生的
2. **大型二進位檔案**：
   - 如果本地開發需要：從備份還原或重新下載
   - 如果只是要上傳到 GitHub：不需要還原，已正確設定 .gitignore

## 確認 .gitignore 是否生效

在還原檔案後，可以執行以下命令確認這些檔案不會被 Git 追蹤：

```bash
# 查看 Git 狀態
git status

# 確認特定檔案是否被忽略
git check-ignore -v doris_resource_tar/apache-doris-2.0.12-bin-x64.tar.gz
git check-ignore -v doris/doris.tar
git check-ignore -v doris/doris.zip
```

如果輸出顯示這些檔案被 `.gitignore` 規則匹配，表示設定正確。
