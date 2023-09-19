"""常量
Date: 2023/9/14 17:59

Author: Fengchunyang

Contact: fengchunyang

Record:
    2023/9/14 Create file.

"""

# 日期格式相关
DATE_STANDARD = '%Y-%m-%d'  # 标准日期格式化
TIME_STANDARD = '%H:%M:%S'  # 标准时间格式化
DATETIME_STANDARD = f'{DATE_STANDARD} {TIME_STANDARD}'  # 标准日期时间格式化

DEFAULT_CONTENT_TYPE = 'application/json'

# 模型相关
DEFAULT_PK = 'pk'  # 默认主键字段
LOGIN_EXPIRE_HOUR = 8  # 默认登录过期时长

# 分页查询相关
PAGINATE_PAGE = 'page'  # 页码字段
PAGINATE_LIMIT = 'limit'  # 分页大小字段
PAGINATE_DISABLE = 'PAGINATE_DISABLE'  # 禁用分页字段

# 系统分隔符
SPLIT_COMMA = ','
SPLIT_DOT = '.'
SPLIT_DASH = '-'

# http响应状态
HTTP_SUCCESS = 'Success'
HTTP_Failed = 'Failed'

# 数据类型
DATA_TYPE_COMMON = 'common'
DATA_TYPE_FIELD = 'data_type'

# 通用数据操作类型
DATA_OPERATION_ADD = '创建'
DATA_OPERATION_MODIFY = '修改'
DATA_OPERATION_DELETE = '逻辑删除'

# 通用资源权限类型
RES_PERMISSION_GET = 'get'
RES_PERMISSION_POST = 'post'
RES_PERMISSION_PUT = 'put'
RES_PERMISSION_DEL = 'delete'
# RES_PERMISSION_PATCH = 'patch'
RES_PERMISSION_CHOICE = (
    (RES_PERMISSION_GET, "查询"),
    (RES_PERMISSION_POST, "创建"),
    (RES_PERMISSION_PUT, "修改"),
    (RES_PERMISSION_DEL, "删除"),
    # (RES_PERMISSION_PATCH, "审核"),
)

# 通用资源类型
RES_PERM_TYPE_INNER = 'inner'
RES_PERM_TYPE_OUTER = 'outer'
RES_PERM_TYPE_CHOICE = (
    (RES_PERM_TYPE_INNER, '内部权限'),
    (RES_PERM_TYPE_OUTER, '外部权限'),
)

# HTTP Method
HTTP_METHOD_GET = 'get'
HTTP_METHOD_PUT = 'put'
HTTP_METHOD_POST = 'post'
HTTP_METHOD_DELETE = 'delete'
HTTP_METHOD_PATCH = 'patch'
HTTP_METHOD_CHOICE = (
    (HTTP_METHOD_GET, 'GET'),
    (HTTP_METHOD_PUT, 'PUT'),
    (HTTP_METHOD_POST, 'POST'),
    (HTTP_METHOD_DELETE, 'DELETE'),
    (HTTP_METHOD_PATCH, 'PATCH'),
)
