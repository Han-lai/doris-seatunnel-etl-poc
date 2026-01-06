import os
import sys
sys.path.append('d:\\01_數據中台\postgresdb\postgres_venv\lib\site-packages')
import pandas as pd

# 定義 .tbl 文件所在的目錄和 .csv 文件的輸出目錄
input_dir = r'D:/AIT_POC/TPC-H V3.0.1/dbgen'
output_dir = r'D:/AIT_POC/TPC-H V3.0.1/tpch_data/10G'


# 確保輸出目錄存在，否則創建它
os.makedirs(output_dir, exist_ok=True)

# 定義要轉換的 .tbl 文件及其對應的列名
tables = {
    # 'customer.tbl': ['CUSTKEY', 'NAME', 'ADDRESS', 'NATIONKEY', 'PHONE', 'ACCTBAL', 'MKTSEGMENT', 'COMMENT'],
    # 'orders.tbl': ['ORDERKEY', 'CUSTKEY', 'ORDERSTATUS', 'TOTALPRICE', 'ORDERDATE', 'ORDERPRIORITY', 'CLERK', 'SHIPPRIORITY', 'COMMENT'],
    'lineitem.tbl': ['ORDERKEY', 'PARTKEY', 'SUPPKEY', 'LINENUMBER', 'QUANTITY', 'EXTENDEDPRICE', 'DISCOUNT', 'TAX', 'RETURNFLAG', 'LINESTATUS', 'SHIPDATE', 'COMMITDATE', 'RECEIPTDATE', 'SHIPINSTRUCT', 'SHIPMODE', 'COMMENT'],
    # 'part.tbl': ['PARTKEY', 'NAME', 'P_MFGR', 'BRAND', 'TYPE', 'SIZE', 'CONTAINER', 'RETAILPRICE', 'COMMENT'],
    # 'supplier.tbl': ['SUPPKEY', 'NAME', 'ADDRESS', 'NATIONKEY', 'PHONE', 'ACCTBAL', 'COMMENT'],
    # 'nation.tbl': ['NATIONKEY', 'NAME', 'REGIONKEY', 'COMMENT'],
    # 'region.tbl': ['REGIONKEY', 'NAME', 'COMMENT'],
    # 'partsupp.tbl': ['PARTKEY', 'SUPPKEY', 'AVAILQTY', 'SUPPLYCOST', 'COMMENT']
}

for tbl_file, column_names in tables.items():
    # 構建完整的文件路徑
    input_file_path = os.path.join(input_dir, tbl_file)
    output_file_path = os.path.join(output_dir, tbl_file.replace('.tbl', '.csv'))

    # 讀取 .tbl 文件，指定分隔符為 |
    df = pd.read_csv(input_file_path, sep='|', header=None, names=column_names)

    # 丟棄最後一列（空列）
    df.drop(df.columns[len(df.columns) - 1], axis=1, inplace=True)

    # 將 DataFrame 寫入 .csv 文件
    df.to_csv(output_file_path, index=False, quoting=1)  # quoting=1 確保所有字符串字段用雙引號括起來

    print(f"Converted {input_file_path} to {output_file_path}")
