import os
import re
import requests
from urllib.parse import quote
from tqdm import tqdm

HEADER = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/129.0.0.0 Safari/537.36",
    "Accept": "*/*",
    "Accept-Encoding": "gzip, deflate",
    "Accept-Language": "zh-CN,zh;q=0.9",
    "Connection": "keep-alive",
    "Host": "123.121.147.7:88",
    "X-Requested-With": "XMLHttpRequest",
    # "Cookie": "JSESSIONID={}"
}

class Pioneer:
    def __init__(self, cookie: dict):
        self.cookie = cookie
        self.header = HEADER
        self.header["Cookie"] = f"JSESSIONID={self.cookie['JSESSIONID']}"
        
    def get_xq(self):
        url = "http://123.121.147.7:88/ve/back/rp/common/teachCalendar.shtml?method=queryCurrentXq"
        header = self.header
        response = requests.get(url, headers=header)
        return response.json()['result'][0]['xqCode']
    
    def get_course_list(self, xq):
        url = ("http://123.121.147.7:88/ve/back/coursePlatform/course.shtml?"
               f"method=getCourseList&pagesize=100&page=1&xqCode={xq}")
        header = self.header
        response = requests.get(url, headers=header)
        return response.json()['courseList']

class Parser:
    def __init__(self, base_url, course_params, save_base, cookie):
        self.base_url = base_url
        self.course_params = course_params
        self.save_base = save_base
        self.download_queue = []
        self.header = HEADER
        self.header["Cookie"] = f"JSESSIONID={cookie['JSESSIONID']}"
        
    def sanitize_path(self, name):
        """清理路径中的非法字符"""
        return re.sub(r'[\\/*?:"<>|]', '_', name).strip()
    
    def fetch_directory_data(self, up_id):
        """获取目录数据"""
        params = {
            'method': 'stuQueryUploadResourceForCourseList',
            'courseId': self.course_params['courseId'],
            'cId': self.course_params['cId'],
            'xkhId': self.course_params['xkhId'],
            'xqCode': self.course_params['xqCode'],
            'docType': '1',
            'up_id': up_id,
            'searchName': ''
        }
        try:
            response = requests.get(self.base_url, params=params)
            response.raise_for_status()
            return response.json()
        except Exception as e:
            print(f"请求失败: {e}")
            return None
    
    def generate_download_url(self, rp_id, rp_name):
        """生成下载链接"""
        encoded_name = quote(rp_name)
        return (
            f"http://123.121.147.7:88/ve/download.shtml?"
            f"userId={self.course_params['userId']}&"
            f"id={rp_id}&p=rp&g={encoded_name}"
        )
    
    def parse(self):
        """开始解析"""
        current_path = os.path.join(self.save_base, self.course_params['courseName'])
        os.makedirs(current_path, exist_ok=True)
        self._parse_directory(up_id=0, current_path=current_path)
    
    def _parse_directory(self, up_id, current_path):
        """递归解析目录"""
        data = self.fetch_directory_data(up_id)
        if not data:
            return

        # 处理文件资源
        if data.get('resList'):
            for resource in data['resList']:
                # if resource['stu_download'] != 2:  # 检查下载权限
                #     continue
                
                filename = self.sanitize_path(
                    f"{resource['rpName']}.{resource['extName']}"
                )
                file_path = os.path.join(current_path, filename)
                download_url = self.generate_download_url(
                    resource['rpId'], 
                    resource['rpName']
                )
                self.download_queue.append({
                    'url': download_url,
                    'path': file_path
                })

        # 处理子目录
        if data.get('bagList'):
            for bag in data['bagList']:
                dir_name = self.sanitize_path(bag['bag_name'])
                dir_path = os.path.join(current_path, dir_name)
                self._parse_directory(bag['id'], dir_path)
    
    def get_download_queue(self):
        return self.download_queue


class Downloader:
    def __init__(self, download_queue, cookie):
        self.download_queue = download_queue
        self.header = HEADER
        self.header["Cookie"] = f"JSESSIONID={cookie['JSESSIONID']}"
    
    def download_all(self, max_retry=3):
        """执行全部下载"""
        for item in tqdm(self.download_queue, desc="下载进度"):
            url = item['url']
            path = item['path']
            os.makedirs(os.path.dirname(path), exist_ok=True)
            
            for attempt in range(max_retry):
                try:
                    response = requests.get(url, stream=True, timeout=10, headers=self.header)
                    response.raise_for_status()
                    with open(path, 'wb') as f:
                        for chunk in response.iter_content(1024):
                            f.write(chunk)
                    print(f"下载成功: {path}")
                    break
                except Exception as e:
                    if attempt == max_retry - 1:
                        print(f"下载失败[{url}]: {str(e)}")
                    else:
                        print(f"重试中({attempt+1}/{max_retry}) {url}")


if __name__ == "__main__":
    # 配置参数（需要根据实际情况修改）
    config = {
        "base_url": "http://123.121.147.7:88/ve/back/coursePlatform/courseResource.shtml",
        "course_params": {
            "courseName": "概率论与数理统计(B)",
            "courseId": "C108005B",
            "cId": "C108005B",
            "xkhId": "2024-2025-2-2C108005B02",
            "xqCode": "2024202502",
            "userId": "23221214"
        },
        "save_base": "./course_downloads"
    }

    # 执行流程
    parser = Parser(
        base_url=config["base_url"],
        course_params=config["course_params"],
        save_base=config["save_base"]
    )
    parser.parse()
    
    print(f"发现 {len(parser.download_queue)} 个待下载文件")
    
    downloader = Downloader(parser.download_queue)
    downloader.download_all()