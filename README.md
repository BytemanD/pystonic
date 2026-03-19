# pystonic

Python 应用基石

## 安装

```bash
pip install pystonic
```

## 功能特性

### 日志系统

基于 [loguru](https://loguru.readthedocs.io/) 的日志配置，支持：
- 自定义日志格式
- 文件/控制台输出
- 上下文变量

```python
from pystonic.log import setup_logger, LogConfig

config = LogConfig(level="INFO")
setup_logger(config)
```

### 配置管理

基于 [pydantic-settings](https://docs.pydantic.dev/latest/concepts/pydantic_settings/) 的配置管理，支持：
- `.env` 文件加载
- 环境变量映射
- 嵌套配置

```python
from pystonic.conf import BaseAppConfig

class AppConfig(BaseAppConfig):
    app_name: str = "my-app"

config = AppConfig.setup()
```

### HTTP 客户端

基于 [httpx](https://www.python-httpx.org/) 的 HTTP 客户端封装：

```python
from pystonic.utils.httpclient import default_client

client = default_client(base_url="https://api.example.com")
response = client.get("/users")
```

### 工具模块

| 模块 | 说明 |
|------|------|
| `command` | 系统命令执行 |
| `fileutil` | 文件操作工具 |
| `strutil` | 字符串工具（IP验证、布尔转换） |
| `table` | 表格显示（基于 prettytable） |
| `input` | 用户交互输入 |


## 开发

```bash
# 安装依赖
pip install -e .

# 运行测试
pytest

# 代码检查
ruff check .
```


## 发布

```bash
uv build --clear
uv publish -v --index testpypi --username __token__ --password <your token>
```
