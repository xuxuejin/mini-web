import socket
import os
from threading import Thread
import pymysql
import json
from decimal import Decimal
from datetime import datetime

# 数据库相关
DB_CONFIG = {
    'host': '10.1.8.13',
    'user': 'pi',
    'password': 'xxj123',
    'db': 'minics'
}

# 接口路由
api_router = {}


# 正常来说，数据库连接应当使用连接池来管理，而不是每次请求时都创建和关闭数据库连接
# PyMySQL 自身没有连接池，可以结合第三方库如 DBUtils 或 SQLAlchemy 来实现连接池功能
def get_db_connection():
    """获取数据库连接"""
    return pymysql.connect(
        host=DB_CONFIG['host'],
        user=DB_CONFIG['user'],
        password=DB_CONFIG['password'],
        db=DB_CONFIG['db'],
        charset='utf8mb4',
        # 查询结果会返回 字典
        cursorclass=pymysql.cursors.DictCursor,
        # 指定转换器
        conv={pymysql.converters.FIELD_TYPE.DECIMAL: str}
    )


# 路由装饰器，自动处理路由
def router(path):
    def wrapper(func):
        def inner_router():
            # some code else
            return func()
        api_router[path] = inner_router
        return inner_router

    return wrapper


# 定义处理数据函数
@router(path='/api/v1/products')
def products():

    response = {
        'code': 0,
        'message': '',
        'data': []
    }

    try:
        db_connect = get_db_connection()
        cursor = db_connect.cursor()
        sql_str = '''SELECT p.name, p.price, p.image_url FROM products p'''
        cursor.execute(sql_str)
        result = cursor.fetchall()

        if result:
            response['data'] = result
            response['message'] = 'Products retrieved successfully'
        else:
            response['message'] = 'No products found'

    except Exception as e:
        response['code'] = -1
        response['message'] = f'Error occurred: {str(e)}'

    finally:
        if cursor:
            cursor.close()
        if db_connect:
            db_connect.close()

    return response


def api_request(path):
    modal = api_router.get(path)
    if modal is None:
        return None
    else:
        return api_router.get(path)()


# MIME 类型映射
def get_content_type(file_path):
    content_type_map = {
        '.html': 'text/html',
        '.js': 'application/javascript',
        '.css': 'text/css',
        '.png': 'image/png',
        '.svg': 'image/svg+xml',
        '.jpg': 'image/jpeg',
        '.jpeg': 'image/jpeg',
        '.gif': 'image/gif',
        '.mp3': 'audio/mpeg',
        '.mp4': 'video/mpeg',
        '.ogg': 'audio/ogg',
        '.webm': 'video/webm',
        '.ttf': 'font/ttf',
        '.woff': 'font/woff',
        '.woff2': 'font/woff2',
        '.eot': 'font/eot'
    }
    # 处理静态资源路径带参数的
    if '?' in file_path:
        file_path = file_path.split('?')[0]

    file_name = os.path.basename(file_path)
    ext = os.path.splitext(file_name)[1]

    return content_type_map.get(ext, 'text/plain')


# 通用序列化工具
def serialize_data(data):
    """递归处理数据中的特殊类型"""
    if isinstance(data, list):
        return [serialize_data(item) for item in data]
    elif isinstance(data, dict):
        return {key: serialize_data(value) for key, value in data.items()}
    elif isinstance(data, Decimal):
        return float(data)  # 或者使用 str(data) 保持更高精度
    elif isinstance(data, datetime):
        return data.isoformat()  # 将 datetime 转换为 ISO 格式字符串
    else:
        return data


# WSGI 应用程序处理函数
def application(environ, start_response):
    """WSGI 应用程序"""

    base_url = os.path.dirname(os.path.abspath(__file__))

    path = environ.get('PATH_INFO', '/')

    # 处理静态资源
    if path.startswith('/static'):
        file_path = f'''{base_url}/app{path}'''
        if os.path.exists(file_path):
            # 读取静态资源
            with open(file_path, 'rb') as file:
                response_body = file.read()
            # 正确处理 Content-Type
            content_type = get_content_type(file_path)
            status = '200 OK'
            headers = [('Content-Type', content_type)]

            start_response(status, headers)

            return [response_body]
        else:
            status = '404 Not Found'
            headers = [('Content-type', 'text/plain')]
            start_response(status, headers)

            return [b'Resource not found']
    elif path.startswith('/api'):
        # 处理接口相关
        response_body = api_request(path)
        status = '404 Not Found'
        headers = [('Content-Type', 'text/plain')]
        if response_body is None:
            start_response(status, headers)
            return [b'api Not Found']
        else:
            # response_body 是 Python 的原生数据结构（比如字典），而 WSGI 应用程序需要返回的是字节序列
            # 1. 将 Python 字典序列化为 JSON 字符串
            response_body = json.dumps(response_body)
            # 2. 将 JSON 字符串转换为字节
            response_body = response_body.encode('utf-8')
            status = '200 OK'
            headers = [('Content-Type', 'application/json')]
            start_response(status, headers)
            return [response_body]
    else:
        if path == '/':
            path = '/index.html'
        # 资源路径
        file_path = f'''{base_url}/app{path}'''

        try:
            with open(file_path, 'rb') as file:
                response_body = file.read()

            status = '200 OK'
            headers = [('Content-Type', 'text/html')]
            start_response(status, headers)
            return [response_body]

        except FileNotFoundError:
            status = '404 Not Found'
            headers = [('Content-Type', 'text/plain')]
            start_response(status, headers)
            return [b'404 Not Found']


# Web 服务器实现部分
class WebServer:
    def __init__(self, host, port, app):
        self.port = port
        self.host = host
        self.app = app
        # 获取 socket 对象
        self.client_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        # 设置端口号复用, 程序退出端口立即释放
        self.client_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        # 绑定端口号
        self.client_socket.bind((self.host, self.port))
        # 监听端口
        self.client_socket.listen(10)

    # 解析请求
    @staticmethod
    def parse_request(conn):
        # 注意：recv 参数对静态资源的响应有影响
        request_data = conn.recv(2048).decode('utf-8')
        if not request_data:
            return None, None, None

        lines = request_data.splitlines()
        if lines:
            method, path, http_version = lines[0].split(' ')
            return method, path, http_version
        return None, None, None

    # 发送响应
    @staticmethod
    def start_response(conn, status, headers):
        response_headers = f"HTTP/1.1 {status}\r\n"
        for header in headers:
            response_headers += f"{header[0]}: {header[1]}\r\n"
        response_headers += "\r\n"
        # 发送请求头
        conn.sendall(response_headers.encode('utf-8'))

    # 处理客户端请求
    def handle_request(self, conn):
        method, path, _ = self.parse_request(conn)

        if not method or not path:
            conn.close()
            return

        # 构建 environ 字典
        environ = {
            'REQUEST_METHOD': method,
            'PATH_INFO': path,
            'SERVER_NAME': self.host,
            'SERVER_PORT': self.port,
        }

        # WSGI 响应函数
        def start_response(status, headers):
            self.start_response(conn, status, headers)

        # 调用 WSGI 应用程序
        response_body = self.app(environ, start_response)

        # 发送响应体
        for data in response_body:
            conn.sendall(data)

        # 关闭连接
        conn.close()

    def start(self):
        print(f"web server run at {self.host}:{self.port}...")
        while True:
            conn, addr = self.client_socket.accept()
            # 开启多线程处理客户端连接，并且设置为守护线程模式
            client_thread = Thread(target=self.handle_request, args=(conn,), daemon=True)

            client_thread.start()


def main():
    # WSGI 应用程序
    app = application

    # 实例化 web 服务器
    web_server = WebServer('0.0.0.0', 9999, app)

    # 启动web服务器
    web_server.start()


if __name__ == '__main__':
    main()
