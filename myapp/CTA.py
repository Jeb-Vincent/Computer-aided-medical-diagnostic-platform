import requests
from bs4 import BeautifulSoup
import pymysql
import time
import re

# 数据库连接配置
db_config = {
    "host": "localhost",  # 数据库主机地址
    "user": "root",       # 数据库用户名
    "password": "zhai3716",  # 数据库密码
    "database": "data_practice",  # 数据库名称
    "charset": "utf8mb4"  # 字符集
}

def crawl_page_xhhos(url):
    """爬取 xhhos 网页的内容"""
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

def crawl_page_baidu(url):
    """爬取百度网页的内容"""
    try:
        response = requests.get(url)
        response.encoding = 'utf-8'
        html = response.text
        soup = BeautifulSoup(html, 'html.parser')

        cta_info = []
        pattern = r'(CTA.*?)(费用|价格).*?(\d+)-?(\d+)?元'  # 匹配部位和价格信息

        for paragraph in soup.find_all('p'):
            text = paragraph.get_text(strip=True)
            if 'CTA检查多少钱' in text or 'CTA费用' in text:
                # 查找符合模式的部位和价格信息
                matches = re.findall(pattern, text)
                for match in matches:
                    position = match[0].strip()  # 部位信息
                    price_min = match[2]         # 最低价格
                    price_max = match[3] if match[3] else price_min  # 最高价格
                    # 只保留最高价格
                    price = price_max
                    cta_info.append((position, price))  # 补全字段

        return cta_info
    except Exception as e:
        print(f"爬取页面 {url} 时出错: {e}")
        return []

def save_to_mysql(data, table_name):
    """将数据存入 MySQL 数据库的不同表中"""
    try:
        connection = pymysql.connect(**db_config)
        with connection.cursor() as cursor:
            # 创建表（如果不存在）
            create_table_sql = f"""
            CREATE TABLE IF NOT EXISTS {table_name} (
                id INT AUTO_INCREMENT PRIMARY KEY,
                project_name VARCHAR(255) NOT NULL,
                price VARCHAR(50) NOT NULL,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;
            """
            cursor.execute(create_table_sql)

            # 插入数据前去重
            # 获取已存在的数据
            select_sql = f"SELECT project_name, price FROM {table_name}"
            cursor.execute(select_sql)
            existing_data = cursor.fetchall()

            # 将已存在的数据转换为集合以便快速查找
            existing_set = set(existing_data)

            # 过滤掉重复的数据
            unique_data = []
            for item in data:
                if item not in existing_set:
                    unique_data.append(item)

            # 插入数据
            if unique_data:
                insert_sql = f"INSERT INTO {table_name} (project_name, price) VALUES (%s, %s)"
                cursor.executemany(insert_sql, unique_data)
                connection.commit()
                print(f"成功插入 {len(unique_data)} 条新数据到表 {table_name}")
            else:
                print(f"没有新数据需要插入到表 {table_name}")
    except Exception as e:
        print(f"存入数据库时出错: {e}")
        connection.rollback()
    finally:
        connection.close()

def main():
    # 爬取 xhhos 网页
    xhhos_url = "https://xhhos.com/server/check_price/6/47?type=2&keyword=CTA"
    print(f"正在爬取: {xhhos_url}")
    xhhos_data = crawl_page_xhhos(xhhos_url)

    # 爬取百度网页
    baidu_url = "https://m.baidu.com/bh/m/detail/vc_15121767605556388392"
    print(f"正在爬取: {baidu_url}")
    baidu_data = crawl_page_baidu(baidu_url)

    # 合并数据
    all_data = xhhos_data + baidu_data

    # 去重（如果有重复的数据）
    unique_data = list(set(all_data))

    # 存入数据库
    table_name = "cta_prices"
    save_to_mysql(unique_data, table_name)

if __name__ == "__main__":
    main()