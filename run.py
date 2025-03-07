from Login import Login
from Fetcher import Pioneer, Parser, Downloader

from dotenv import load_dotenv
import os

# API 配置
API_BASE = "http://123.121.147.7:88/ve/back/coursePlatform/courseResource.shtml"

# 加载 USERNAME 和 PASSWORD
load_dotenv()
USERNAME = os.getenv('USERNAME')
PASSWORD = os.getenv('PASSWORD')

# 登录
login = Login('cp')
login.login(student_id=USERNAME, password=PASSWORD)
cookie = login.method.getCookies()

# 获取课程列表
pioneer = Pioneer(cookie)
xq = pioneer.get_xq()
course_list = pioneer.get_course_list(xq)

# 遍历课程列表并下载
for course in course_list:
    course_params = {
        'courseName': course['name'],
        'courseId': course['course_num'],
        'cId': course['course_num'],
        'xkhId': course['fz_id'],
        'xqCode': xq,
        'userId': USERNAME
    }
    
    print(f"正在获取课程文件：{course['name']}")
    
    parser = Parser(API_BASE, course_params, 'download', cookie)
    parser.parse()
    download_queue = parser.get_download_queue()

    print(f"获取成功，正在下载课程文件：{course['name']}")
    
    downloader = Downloader(download_queue, cookie)
    downloader.download_all()
    
