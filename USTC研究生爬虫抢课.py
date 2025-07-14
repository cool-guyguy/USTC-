import requests
import time
from datetime import datetime
from typing import List, Dict, Optional

# 配置参数
CONFIG = {
    'cookies': {
        'sduuid': 'xxxxxxxxxx',
        'SESSION': 'xxxxxxxxxx',
        'fine_auth_token': 'xxxxxxxxx',
        'fine_remember_login': 'xxxxxxxxx',
        'SVRNAME': 'xxxxxxxxx'
    },
    'student_id': xxxxxx,
    'lesson_code': "001108.01",
    'start_time': "2025-7-14 15:46:00",  # 定时启动时间，格式为"YYYY-MM-DD HH:MM:SS"
    'retry_interval': 0.1,  # 重试间隔(秒)
    'max_retries': 1000  # 最大重试次数
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
        self.student_id = CONFIG['student_id']
        self.cookies = CONFIG['cookies']
        self.lesson_code = CONFIG['lesson_code']
        self.start_time = datetime.strptime(CONFIG['start_time'], "%Y-%m-%d %H:%M:%S")

    def _make_request(self, url, data, extra_headers=None):
        headers = BASE_HEADERS.copy()
        if extra_headers:
            headers.update(extra_headers)
        return self.session.post(url, headers=headers, cookies=self.cookies, data=data)

    def get_turn_id(self):
        """获取当前选课轮次ID"""
        url = "https://jw.ustc.edu.cn/ws/for-std/course-select/open-turns"
        data = {'bizTypeId': '3', 'studentId': str(self.student_id)}
        response = self._make_request(url, data)
        turn_info = response.json()[0]
        print(f"当前选课轮次: {turn_info['name']}")
        return turn_info['id']

    def get_lessons(self, turn_id):
        """获取可选课程列表"""
        url = "https://jw.ustc.edu.cn/ws/for-std/course-select/addable-lessons"
        data = {'turnId': str(turn_id), 'studentId': str(self.student_id)}
        return self._make_request(url, data).json()

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

    def check_status(self, request_id):
        """检查选课状态"""
        url = "https://jw.ustc.edu.cn/ws/for-std/course-select/add-drop-response"
        data = {'studentId': str(self.student_id), 'requestId': str(request_id)}
        return self._make_request(url, data, {'priority': 'u=1, i'}).json()

    @staticmethod
    def find_lesson(lessons, lesson_code):
        """根据课程号查找课程信息"""
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
            self.wait_until_start()

            turn_id = self.get_turn_id()
            retry_count = 0

            while retry_count < CONFIG['max_retries']:
                retry_count += 1
                print(f"\n尝试第 {retry_count} 次抢课...")

                try:
                    lessons = self.get_lessons(turn_id)
                    target = self.find_lesson(lessons, self.lesson_code)

                    if not target:
                        print(f"未找到课程 {self.lesson_code}, 等待重试...")
                        time.sleep(CONFIG['retry_interval'])
                        continue

                    print(f"找到课程: {target['name']} (ID: {target['id']})")

                    submit_res = self.submit_request(target['id'], turn_id, target['schedule_id'])
                    if submit_res.status_code != 200:
                        print("选课请求失败, 等待重试...")
                        time.sleep(CONFIG['retry_interval'])
                        continue

                    request_id = submit_res.text.strip('"')
                    status = self.check_status(request_id)

                    if status['success']:
                        print("🎉 抢课成功! 🎉")
                        return True
                    else:
                        print(f"选课失败: {status['errorMessage']['textZh']}, 等待重试...")

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
    print("抢课程序启动...")
    selector = CourseSelector()
    if selector.run():
        print("抢课任务完成!")
    else:
        print("抢课任务失败!")