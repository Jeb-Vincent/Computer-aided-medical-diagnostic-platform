import requests
from bs4 import BeautifulSoup
import pymysql
import time

# 数据库连接配置
db_config = {
    "host": "localhost",  # 数据库主机地址
    "user": "root",       # 数据库用户名
    "password": "zhai3716",  # 数据库密码
    "database": "data_practice",  # 数据库名称
    "charset": "utf8mb4"  # 字符集
}

def crawl_page(url):
    """爬取单页的内容"""
    try:
        response = requests.get(url)
        response.encoding = 'utf-8'
        html = response.text
        soup = BeautifulSoup(html, 'html.parser')

        table = soup.find('table')
        rows = table.find_all('tr')

        data = []
        for row in rows:
            cols = row.find_all('td')
            if len(cols) >= 4:  # 确保有至少四列（项目编码、项目名称、价格单位、价格）
                project_name = cols[1].text.strip()  # 项目名称
                price = cols[3].text.strip()         # 价格
                data.append((project_name, price))
        return data
    except Exception as e:
        print(f"爬取页面 {url} 时出错: {e}")
        return []

def save_to_mysql(data):
    """将数据存入 MySQL 数据库"""
    try:
        connection = pymysql.connect(**db_config)
        with connection.cursor() as cursor:
            # 创建表（如果不存在）
            create_table_sql = """
            CREATE TABLE IF NOT EXISTS ct_prices (
                id INT AUTO_INCREMENT PRIMARY KEY,
                project_name VARCHAR(255) NOT NULL,
                price VARCHAR(50) NOT NULL,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;
            """
            cursor.execute(create_table_sql)

            # 插入数据
            insert_sql = "INSERT INTO ct_prices (project_name, price) VALUES (%s, %s)"
            cursor.executemany(insert_sql, data)
            connection.commit()
        print(f"成功插入 {len(data)} 条数据")
    except Exception as e:
        print(f"存入数据库时出错: {e}")
        connection.rollback()
    finally:
        connection.close()

def main():
    base_url = "https://xhhos.com/server/check_price/6/47?keyword=CT&type=2&page={}"
    all_data = []

    for page in range(1, 4):  # 爬取第 1 到 3 页
        url = base_url.format(page)
        print(f"正在爬取第 {page} 页: {url}")
        page_data = crawl_page(url)
        if page_data:
            all_data.extend(page_data)
        time.sleep(2)  # 每次请求后暂停 2 秒，避免对服务器造成过大压力

    # 将所有数据存入 MySQL 数据库
    if all_data:
        save_to_mysql(all_data)
    else:
        print("没有获取到数据，无法存入数据库")

if __name__ == "__main__":
    main()