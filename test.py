import os
from typing import List, Dict

import requests

"""
 以下参数需手动设置
 - cookies:登录后的cookies
 - lesson_code: 课堂号
 - student_id: 学生id
 返回:
 - 响应对象
 """
# 从环境变量读取配置（或直接赋值）

lesson_code = "CONT6209P.01"  #课堂号
student_id= xxxxx  # 学生ID
cookies={
        'sduuid': 'xxxxxxxx',
        'SESSION': 'xxxxxxxxxx',
        'fine_auth_token': 'xxxxx',
        'fine_remember_login': '-1',
        'SVRNAME': 'student7'
    }


turn_id = None  # 选课轮次ID,无需填写会自动配置
#获取turn_id
def get_turn_id(session, student_id, cookies, headers=None):

    url = "https://jw.ustc.edu.cn/ws/for-std/course-select/open-turns"
    # 默认请求头
    default_headers = {
        'authority': 'jw.ustc.edu.cn',
        'accept': '*/*',
        'accept-language': 'zh-CN,zh;q=0.9,en;q=0.8,en-GB;q=0.7,en-US;q=0.6,nl;q=0.5',
        'content-type': 'application/x-www-form-urlencoded; charset=UTF-8',
        'origin': 'https://jw.ustc.edu.cn',
        'referer': f'https://jw.ustc.edu.cn/for-std/course-select/turns/498393/{student_id}',
        'sec-ch-ua': '"Not)A;Brand";v="8", "Chromium";v="138", "Microsoft Edge";v="138"',
        'sec-ch-ua-mobile': '?0',
        'sec-ch-ua-platform': '"Windows"',
        'sec-fetch-dest': 'empty',
        'sec-fetch-mode': 'cors',
        'sec-fetch-site': 'same-origin',
        'user-agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/138.0.0.0 Safari/537.36 Edg/138.0.0.0',
        'x-requested-with': 'XMLHttpRequest'
    }
    # 更新自定义请求头
    if headers:
        default_headers.update(headers)
    # 请求数据
    data = {
        'bizTypeId': str(3),
        'studentId': str(student_id)
    }
    # 发送POST请求
    response = session.post(
        url,
        headers=default_headers,
        cookies=cookies,
        data=data
    )
    turnid = response.json()[0]['id']
    print("本次选课为：",response.json()[0]["name"])
    return turnid

#获取可选课程列表
def get_addable_lessons(session, student_id, turn_id, cookies, headers=None):
    """
    获取可选课程列表
    参数:
    - session: requests.Session对象
    - student_id: 学生ID
    - turn_id: 轮次ID
    - cookies: 登录后的cookies
    - headers: 自定义请求头
    返回:
    - 响应对象
    """
    url = "https://jw.ustc.edu.cn/ws/for-std/course-select/addable-lessons"
    # 默认请求头
    default_headers = {
        'authority': 'jw.ustc.edu.cn',
        'accept': '*/*',
        'accept-language': 'zh-CN,zh;q=0.9,en;q=0.8,en-GB;q=0.7,en-US;q=0.6,nl;q=0.5',
        'content-type': 'application/x-www-form-urlencoded; charset=UTF-8',
        'origin': 'https://jw.ustc.edu.cn',
        'referer': f'https://jw.ustc.edu.cn/for-std/course-select/{student_id}/turn/{turn_id}/select',
        'sec-ch-ua': '"Not)A;Brand";v="8", "Chromium";v="138", "Microsoft Edge";v="138"',
        'sec-ch-ua-mobile': '?0',
        'sec-ch-ua-platform': '"Windows"',
        'sec-fetch-dest': 'empty',
        'sec-fetch-mode': 'cors',
        'sec-fetch-site': 'same-origin',
        'user-agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/138.0.0.0 Safari/537.36 Edg/138.0.0.0',
        'x-requested-with': 'XMLHttpRequest'
    }
    # 更新自定义请求头
    if headers:
        default_headers.update(headers)
    # 请求数据
    data = {
        'turnId': str(turn_id),
        'studentId': str(student_id)
    }
    # 发送POST请求
    response = session.post(
        url,
        headers=default_headers,
        cookies=cookies,
        data=data
    )
    return response


def submit_course_request(session, student_id, lesson_id, turn_id, schedule_group_id, cookies, virtual_cost=0,
                          headers=None):
    """
    提交选课请求
    参数:
    - session: requests.Session对象
    - student_id: 学生ID
    - lesson_id: 课程ID (从第一个请求的响应中获取)
    - turn_id: 轮次ID
    - schedule_group_id: 课程安排组ID (从第一个请求的响应中获取)
    - cookies: 登录后的cookies
    - virtual_cost: 虚拟消耗，默认为0
    - headers: 可选的自定义请求头

    返回:
    - 响应对象
    """
    url = "https://jw.ustc.edu.cn/ws/for-std/course-select/add-request"
    # 默认请求头
    default_headers = {
        'authority': 'jw.ustc.edu.cn',
        'accept': '*/*',
        'accept-language': 'zh-CN,zh;q=0.9,en;q=0.8,en-GB;q=0.7,en-US;q=0.6,nl;q=0.5',
        'content-type': 'application/x-www-form-urlencoded; charset=UTF-8',
        'origin': 'https://jw.ustc.edu.cn',
        'referer': f'https://jw.ustc.edu.cn/for-std/course-select/{student_id}/turn/{turn_id}/select',
        'sec-ch-ua': '"Not)A;Brand";v="8", "Chromium";v="138", "Microsoft Edge";v="138"',
        'sec-ch-ua-mobile': '?0',
        'sec-ch-ua-platform': '"Windows"',
        'sec-fetch-dest': 'empty',
        'sec-fetch-mode': 'cors',
        'sec-fetch-site': 'same-origin',
        'user-agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/138.0.0.0 Safari/537.36 Edg/138.0.0.0',
        'x-requested-with': 'XMLHttpRequest',
        'priority': 'u=1, i'  # 注意这个header在第一个请求中没有
    }

    # 更新自定义请求头
    if headers:
        default_headers.update(headers)
    # 请求数据
    data = {
        'studentAssoc': str(student_id),
        'lessonAssoc': str(lesson_id),
        'courseSelectTurnAssoc': str(turn_id),
        'scheduleGroupAssoc': None,
        'virtualCost': str(virtual_cost)
    }
    # 发送POST请求
    response = session.post(
        url,
        headers=default_headers,
        cookies=cookies,
        data=data
    )
    return response


def check_request_status(session, student_id, request_id, cookies, headers=None):
    """
    查询选课请求状态

    参数:
    - session: requests.Session对象
    - student_id: 学生ID
    - request_id: 请求ID (从第二个请求的响应中获取)
    - cookies: 登录后的cookies
    - headers: 可选的自定义请求头

    返回:
    - 响应对象
    """
    url = "https://jw.ustc.edu.cn/ws/for-std/course-select/add-drop-response"

    # 默认请求头
    default_headers = {
        'authority': 'jw.ustc.edu.cn',
        'accept': '*/*',
        'accept-language': 'zh-CN,zh;q=0.9,en;q=0.8,en-GB;q=0.7,en-US;q=0.6,nl;q=0.5',
        'content-type': 'application/x-www-form-urlencoded; charset=UTF-8',
        'origin': 'https://jw.ustc.edu.cn',
        'referer': f'https://jw.ustc.edu.cn/for-std/course-select/{student_id}/turn/1143/select',
        'sec-ch-ua': '"Not)A;Brand";v="8", "Chromium";v="138", "Microsoft Edge";v="138"',
        'sec-ch-ua-mobile': '?0',
        'sec-ch-ua-platform': '"Windows"',
        'sec-fetch-dest': 'empty',
        'sec-fetch-mode': 'cors',
        'sec-fetch-site': 'same-origin',
        'user-agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/138.0.0.0 Safari/537.36 Edg/138.0.0.0',
        'x-requested-with': 'XMLHttpRequest',
        'priority': 'u=1, i'
    }

    # 更新自定义请求头
    if headers:
        default_headers.update(headers)

    # 请求数据
    data = {
        'studentId': str(student_id),
        'requestId': str(request_id)
    }

    # 发送POST请求
    response = session.post(
        url,
        headers=default_headers,
        cookies=cookies,
        data=data
    )
    return response

#实现课程号到课程信息的映射
def get_lesson_info_by_id(lessons: List[Dict], lesson_code: str) -> Dict:
    """
    根据课程ID获取课程信息
    返回包含 lesson_id, schedule_group_id, course_name 的字典
    如果找不到则返回None
    """
    for lesson in lessons:
        if lesson['code'] == lesson_code:
            return {
                'lesson_id': lesson['id'],
                'schedule_group_id': lesson['scheduleGroups'][0]['id'],
                'course_name': lesson['course']['nameZh']
            }
    return None
# 完整抢课流程示例
if __name__ == "__main__":
    # 1. 初始化session

    session = requests.Session()

    # 2. 设置学生ID和轮次ID
    student_id = "498393"
    turn_id=get_turn_id(session,student_id,cookies)

    # 3. 获取可选课程列表
    lessons_response = get_addable_lessons(session, student_id, turn_id, cookies)
    if lessons_response.status_code != 200:
        print("获取课程列表失败!")
        exit()

    lessons = lessons_response.json()
    print(f"找到 {len(lessons)} 门可选课程")
    # for lesson in lessons:
    #     print(lesson['code'],"     ")

    # # 选择第一门课程
    # target_lesson = lessons[0]
    # print("target_lesson:",target_lesson)
    # lesson_id = target_lesson['id']
    # schedule_group_id = target_lesson['scheduleGroups'][0]['id']
    # course_name = target_lesson['course']['nameZh']

    #选择课程
    lesson_code=lesson_code
    lesson_info = get_lesson_info_by_id(lessons, lesson_code)
    if lesson_info is None:
        print(f"错误: 找不到课程号为 {lesson_code} 的课程")
    else:
        # 使用获取到的信息
        lesson_id = lesson_info['lesson_id']
        schedule_group_id = lesson_info['schedule_group_id']
        course_name = lesson_info['course_name']
        print(f"准备选择课程: {course_name} (课程号: {lesson_code}) (ID: {lesson_id})")
    print(f"尝试选择课程: {course_name} (课程号: {lesson_code}) (ID: {lesson_id})")

    # 5. 提交选课请求
    submit_response = submit_course_request(
        session=session,
        student_id=student_id,
        lesson_id=lesson_id,
        turn_id=turn_id,
        schedule_group_id=schedule_group_id,
        cookies=cookies
    )

    # 6. 处理提交结果
    if submit_response.status_code == 200:
        request_id = submit_response.text.strip('"')  # 获取请求ID
        print(f"选课请求提交成功! 请求ID: {request_id}")

        # 7. 检查选课状态
        status_response = check_request_status(
            session=session,
            student_id=student_id,
            request_id=request_id,
            cookies=cookies
        )

        if status_response.status_code == 200:
            status_data = status_response.json()
            if status_data['success']:
                print("选课成功!")
            else:
                print(f"选课失败: {status_data['errorMessage']['textZh']}")
        else:
            print("查询选课状态失败! 状态码:", status_response.status_code)
    else:
        print("选课请求提交失败! 状态码:", submit_response.status_code)