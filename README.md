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

### 核心模块

| 模块 | 说明 |
|------|------|
| `fileutil` | 文件操作工具 |
| `strutil` | 字符串工具（IP 验证、布尔转换） |
| `input` | 用户交互输入 |
| `system` | 系统信息（CPU、磁盘、网络等） |
| `textutil` | 文本处理工具 |
| `funcutil` | 函数工具 |
| `pkg` | 包管理工具 |
| `code` | 代码质量检查（格式化、测试） |


## 开发

```bash
# 安装依赖
uv sync --all-extras

# 运行测试
pytest

# 代码检查
ruff check .
```

### 代码质量工具

使用内置的代码质量检查工具：

```python
from pystonic.tools.code import check_code

# 运行格式化和 lint 检查
check_code()

# 运行测试
check_code(test=True)

# 运行测试并查看覆盖率
check_code(test=True, cover=True)
```

或者使用命令行：

```bash
python -m pystonic.tools.code check
python -m pystonic.tools.code check --test
python -m pystonic.tools.code check --test --cover
```

## 发布

```bash
uv build --clear
uv publish -v --index testpypi --username __token__ --password <your token>
```
