# 电商专题共享资源

这里存放 `proj1`、`proj3`、`proj4` 共用但不属于某一个 project 的说明和配置。

## 文件

- `config/db.env.example`：统一数据库环境变量示例。不要把真实密码提交进仓库。
- `sql/00_check_proj1_ready.sql`：检查 `proj1_3nf` 基础表是否存在并有数据。

## 使用方式

电商专题的 Python/Streamlit 应用默认使用以下连接：

```text
DB_NAME=ecommerce_db
DB_USER=gaussdb
DB_HOST=localhost
DB_PORT=15432
DB_SCHEMA=proj1_3nf
```

如果本机配置不同，在 PowerShell 中可以临时设置：

```powershell
$env:DB_NAME="ecommerce_db"
$env:DB_USER="gaussdb"
$env:DB_PASSWORD="<your-password>"
$env:DB_HOST="localhost"
$env:DB_PORT="15432"
$env:DB_SCHEMA="proj1_3nf"
```

随后进入对应 project 目录运行 Streamlit。
