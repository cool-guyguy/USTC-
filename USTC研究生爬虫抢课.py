import requests
from typing import List, Dict

# 配置参数
CONFIG = {
    'cookies': {
        'sduuid': 'b851401dd049b80828f13c999fec9109',
        'SESSION': 'd32c9757-fcf0-4341-b2ed-41cabe5d41bc',
        'fine_auth_token': 'eyJhbGci...',  # 简化的token
        'fine_remember_login': '-1',
        'SVRNAME': 'teacher1'
    },
    'student_id': 498393,
    'lesson_code': "001108.01"
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

    def run(self):
        try:
            # 获取选课轮次和课程列表
            turn_id = self.get_turn_id()
            lessons = self.get_lessons(turn_id)

            # 查找目标课程
            target = self.find_lesson(lessons, CONFIG['lesson_code'])
            if not target:
                print(f"错误: 未找到课程 {CONFIG['lesson_code']}")
                return

            print(f"准备选择课程: {target['name']} (ID: {target['id']})")

            # 提交选课请求
            submit_res = self.submit_request(target['id'], turn_id, target['schedule_id'])
            if submit_res.status_code != 200:
                print("选课请求失败!")
                return

            # 检查选课结果
            request_id = submit_res.text.strip('"')
            status = self.check_status(request_id)

            if status['success']:
                print("选课成功!")
            else:
                print(f"选课失败: {status['errorMessage']['textZh']}")

        except Exception as e:
            print(f"程序出错: {e}")
        finally:
            self.session.close()


if __name__ == "__main__":
    selector = CourseSelector()
    selector.run()