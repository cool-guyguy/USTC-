import requests
import time
from datetime import datetime
from typing import List, Dict, Optional
import json

# 配置参数
CONFIG = {
    'cookies': {
        'cookie_vjuid_portal_login': '',
        'SESSION': '',
        'fine_auth_token': '',
        'fine_remember_login': '-1',
        'SVRNAME': 'teacher1'
    },
    'student_id': 12345,
    'lesson_code': "CONT6407P.02",
    'start_time': "2025-7-18 14:59:55",  # 定时启动时间，格式为"YYYY-MM-DD HH:MM:SS"
    'retry_interval': 3,  # 重试间隔(秒)
    'max_retries': 99999999999  # 最大重试次数
}

BASE_HEADERS = {
    'authority': 'jw.ustc.edu.cn',
    'accept': '*/*',
    'accept-language': 'zh-CN,zh;q=0.9,en;q=0.8',
    'content-type': 'application/x-www-form-urlencoded; charset=UTF-8',
    'origin': 'https://jw.ustc.edu.cn',
    'user-agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
    'x-requested-with': 'XMLHttpRequest'
}


class CourseSelector:
    def __init__(self):
        self.session = requests.Session()
        # 设置会话重试策略
        retry_strategy = requests.adapters.Retry(
            total=3,
            backoff_factor=0.5,
            status_forcelist=[429, 500, 502, 503, 504],
        )
        adapter = requests.adapters.HTTPAdapter(max_retries=retry_strategy)
        self.session.mount("https://", adapter)
        self.session.mount("http://", adapter)

        self.student_id = CONFIG['student_id']
        self.cookies = CONFIG['cookies']
        self.lesson_code = CONFIG['lesson_code']
        self.start_time = datetime.strptime(CONFIG['start_time'], "%Y-%m-%d %H:%M:%S")
        self.turn_id = None

    def _make_request(self, url, data, extra_headers=None, method='POST', timeout=10):
        headers = BASE_HEADERS.copy()
        if extra_headers:
            headers.update(extra_headers)

        try:
            if method.upper() == 'POST':
                response = self.session.post(url, headers=headers, cookies=self.cookies,
                                             data=data, timeout=timeout)
            else:
                response = self.session.get(url, headers=headers, cookies=self.cookies,
                                            params=data, timeout=timeout)

            # 检查响应状态
            if response.status_code != 200:
                print(f"请求失败，状态码: {response.status_code}")
                return None

            # 检查响应内容是否为空
            if not response.text.strip() or response.text.strip().lower() == 'null':
                print("收到空响应")
                return None

            return response

        except requests.exceptions.RequestException as e:
            print(f"请求异常: {e}")
            return None
        except Exception as e:
            print(f"未知错误: {e}")
            return None

    def get_turn_id(self):
        """获取当前选课轮次ID"""
        url = "https://jw.ustc.edu.cn/ws/for-std/course-select/open-turns"
        data = {'bizTypeId': '3', 'studentId': str(self.student_id)}
        response = self._make_request(url, data)

        if not response:
            return None

        try:
            turn_info = response.json()[0]
            print(f"当前选课轮次: {turn_info['name']}")
            return turn_info['id']
        except (IndexError, KeyError, ValueError) as e:
            print(f"解析轮次信息失败: {e}")
            return None

    def get_lessons(self, turn_id):
        """获取可选课程列表"""
        url = "https://jw.ustc.edu.cn/ws/for-std/course-select/addable-lessons"
        data = {'turnId': str(turn_id), 'studentId': str(self.student_id)}
        response = self._make_request(url, data)

        if not response:
            return None

        try:
            return response.json()
        except ValueError as e:
            print(f"解析课程列表失败: {e}")
            return None

    def submit_request(self, lesson_id, turn_id, schedule_group_id):
        """提交选课请求"""
        url = "https://jw.ustc.edu.cn/ws/for-std/course-select/add-request"
        data = {
            'studentAssoc': str(self.student_id),
            'lessonAssoc': str(lesson_id),
            'courseSelectTurnAssoc': str(turn_id),
            'scheduleGroupAssoc': str(schedule_group_id),
            'virtualCost': '0'
        }
        return self._make_request(url, data, {'priority': 'u=1, i'})

    def check_status(self, request_id, max_retries=5):
        """检查选课状态，增加重试机制"""
        url = "https://jw.ustc.edu.cn/ws/for-std/course-select/add-drop-response"
        data = {'studentId': str(self.student_id), 'requestId': str(request_id)}

        for attempt in range(max_retries):
            response = self._make_request(url, data, {'priority': 'u=1, i'})

            if not response:
                print(f"状态检查失败 (尝试 {attempt + 1}/{max_retries})")
                time.sleep(1)
                continue

            try:
                return response.json()
            except ValueError:
                print(f"状态响应不是有效JSON (尝试 {attempt + 1}/{max_retries})")
                time.sleep(1)
                continue

        print(f"经过 {max_retries} 次尝试后仍无法获取有效状态")
        return None

    @staticmethod
    def find_lesson(lessons, lesson_code):
        """根据课程号查找课程信息"""
        if not lessons:
            return None

        for lesson in lessons:
            if lesson['code'] == lesson_code:
                return {
                    'id': lesson['id'],
                    'name': lesson['course']['nameZh'],
                    'schedule_id': lesson['scheduleGroups'][0]['id']
                }
        return None

    def wait_until_start(self):
        """等待到设定的启动时间"""
        now = datetime.now()
        if now < self.start_time:
            wait_seconds = (self.start_time - now).total_seconds()
            print(f"等待到启动时间: {self.start_time} (还剩{wait_seconds:.1f}秒)")
            time.sleep(wait_seconds)

    def run(self):
        try:
            print("抢课程序启动...")
            self.wait_until_start()

            # 获取轮次ID
            self.turn_id = self.get_turn_id()
            if not self.turn_id:
                print("获取轮次ID失败，程序退出")
                return False

            retry_count = 0
            last_lesson_check = 0
            lesson_cache = None

            while retry_count < CONFIG['max_retries']:
                retry_count += 1
                print(f"\n尝试第 {retry_count} 次抢课...")

                try:
                    # 每5次请求更新一次课程列表，减少服务器压力
                    if retry_count % 5 == 1 or not lesson_cache:
                        lessons = self.get_lessons(self.turn_id)
                        if lessons:
                            lesson_cache = lessons
                            last_lesson_check = time.time()
                        else:
                            print("获取课程列表失败，等待重试...")
                            time.sleep(CONFIG['retry_interval'])
                            continue
                    else:
                        lessons = lesson_cache

                    target = self.find_lesson(lessons, self.lesson_code)

                    if not target:
                        print(f"未找到课程 {self.lesson_code}, 等待重试...")
                        time.sleep(CONFIG['retry_interval'])
                        continue

                    print(f"找到课程: {target['name']} (ID: {target['id']})")

                    submit_res = self.submit_request(target['id'], self.turn_id, target['schedule_id'])
                    if not submit_res:
                        print("选课请求失败, 等待重试...")
                        time.sleep(CONFIG['retry_interval'])
                        continue

                    request_id = submit_res.text.strip('"')
                    print(f"请求ID: {request_id}")

                    status = self.check_status(request_id)
                    if not status:
                        print("无法获取选课状态, 等待重试...")
                        time.sleep(CONFIG['retry_interval'])
                        continue

                    if status.get('success'):
                        print("🎉 抢课成功! 🎉")
                        return True
                    else:
                        error_msg = status.get('errorMessage', {}).get('textZh', '未知错误')
                        print(f"选课失败: {error_msg}, 等待重试...")

                except Exception as e:
                    print(f"请求出错: {e}, 等待重试...")

                time.sleep(CONFIG['retry_interval'])

            print(f"已达到最大重试次数 {CONFIG['max_retries']}, 抢课结束")
            return False

        except Exception as e:
            print(f"程序出错: {e}")
            return False
        finally:
            self.session.close()


if __name__ == "__main__":
    selector = CourseSelector()
    if selector.run():
        print("抢课任务完成!")
    else:
        print("抢课任务失败!")