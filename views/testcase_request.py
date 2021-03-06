import json
from _datetime import datetime
from flask.views import MethodView
from flask import render_template, Blueprint, request, session, current_app
from modles.testcase import TestCases
from modles.testcase_result import TestCaseResult
from modles.case_group import CaseGroup
from modles.testcase_start_times import TestCaseStartTimes
from modles.testcase_scene import TestCaseScene
from modles.user import User
from common.tail_font_log import FrontLogs
from app import db
from common.analysis_params import AnalysisParams
from common.execute_testcase import to_execute_testcase
from common.assert_method import AssertMethod
from common.most_common_method import NullObject
from views.mysql import mysqlrun

test_case_request_blueprint = Blueprint('test_case_request_blueprint', __name__)


class TestCaseRequest(MethodView):

    def get(self):
        user_id = session.get('user_id')
        user = User.query.get(user_id)
        print('user_id:', user_id)
        FrontLogs('进入测试用例执行页面').add_to_front_log()
        case_groups = user.user_case_groups
        case_groups_new = []
        for case_group in case_groups:
            case_group_NullObject = NullObject()
            case_group_NullObject.name = case_group.name
            testcase_list = []
            testcases = TestCases.query.join(CaseGroup, CaseGroup.id == TestCases.group_id).filter(
                TestCases.testcase_scene_id.is_(None), TestCases.group_id == case_group.id, TestCases.user_id == user_id).all()
            print(' %s testcases_:' % case_group, testcases)
            for testcase in testcases:
                testcase_NullObject = NullObject()
                testcase_NullObject.id = testcase.id
                testcase_NullObject.name = testcase.name
                testcase_NullObject.is_testcase_scene = 0
                testcase_list.append(testcase_NullObject)
            try:
                case_group_scene = TestCaseScene.query.join(CaseGroup, CaseGroup.id == TestCaseScene.group_id).filter(
                    TestCaseScene.user_id == user_id, CaseGroup.name == case_group.name).all()
                for testcase_scene in case_group_scene:
                    testcase_scene_NullObject = NullObject()
                    testcase_scene_NullObject.id = testcase_scene.id
                    testcase_scene_NullObject.name = testcase_scene.name
                    testcase_scene_NullObject.is_testcase_scene = 1
                    testcase_list.append(testcase_scene_NullObject)
            except KeyError:
                pass

            case_group_NullObject.testcase_list = testcase_list
            case_groups_new.append(case_group_NullObject)
            print('testcase_list: ', case_group_NullObject.name, testcase_list)

        no_case_group = type('no_case_group', (object,), dict(a=-1))
        case_groups_new.append(no_case_group)
        no_case_group.testcases = TestCases.query.filter(
            TestCases.group_id.in_([None, '']), TestCases.testcase_scene_id.is_(None), TestCases.user_id == user_id).all()
        no_case_group.name = "<span style='color: blue'>未分组测试用例</span>"
        print('no_case_group testcases :', no_case_group.testcases)

        no_scene_group = type('testcase_scene_group', (object,), dict(a=-1))
        case_groups_new.append(no_scene_group)
        no_scene_group.testcases = TestCaseScene.query.filter(
            TestCaseScene.group_id.is_(None), TestCaseScene.user_id == user_id).all()
        no_scene_group.name = "<span style='color: blue'>未分组测试场景</span>"
        print('no_scene_group.testcases :', no_scene_group.testcases)

        return render_template('test_case_request/test_case_request.html', case_groups=case_groups_new)

    def post(self):
        print('TestCaseRequest post request.form: ', request.form)
        testcase_ids = request.form.getlist('testcase')
        print("request_from_list: ", testcase_ids)
        testcase_list = []
        for index, testcase_id in enumerate(testcase_ids):
            testcase = TestCases.query.get(testcase_id)
            testcase.name = AnalysisParams().analysis_params(testcase.name)
            testcase_list.append(testcase)
        print('testcase_list: ', testcase_list)

        testcase_scene_ids = request.form.getlist('testcase_scene')
        for testcase_scene_id in testcase_scene_ids:
            testcase_scene = TestCaseScene.query.get(testcase_scene_id)
            testcases = testcase_scene.testcases
            for testcase in testcases:
                testcase.scene_name = testcase.testcase_scene.name
                testcase_list.append(testcase)
        print("request_testcase_ids_list: ", testcase_ids)

        return render_template('test_case_request/test_case_request_list.html', items=testcase_list)


class TestCaseRequestStart(MethodView):

    def post(self, request_is_xhr=None):
        if request.is_xhr or request_is_xhr:
            print(request.args)
            test_case_id = request.form.get('testcase_id')
            testcase_time_id = request.form.get('test_case_time_id')
            print('异步请求的test_case_id,testcase_time_id: ', test_case_id, testcase_time_id)
            response_body = post_testcase(test_case_id, testcase_time_id)
            return response_body


def post_testcase(test_case_id, testcase_time_id):
    testcase = TestCases.query.get(test_case_id)
    url, data, hope_result = AnalysisParams().analysis_more_params(testcase.url, testcase.data, testcase.hope_result)
    method = testcase.method
    response_body, regist_variable_value = to_execute_testcase(testcase)
    testcase_test_result = AssertMethod(actual_result=response_body, hope_result=hope_result).assert_method()
    if testcase.old_sql and testcase.old_sql_id and testcase.old_sql_regist_variable:
        old_sql_value = mysqlrun(mysql_id=testcase.old_sql_id, sql=testcase.old_sql, regist_variable=testcase.old_sql_regist_variable, is_request=False)
        old_sql_value_result = AssertMethod(actual_result=old_sql_value, hope_result=AnalysisParams().analysis_params(testcase.old_sql_hope_result)).assert_method()
    else:
        old_sql_value = old_sql_value_result = ''

    if testcase.new_sql and testcase.new_sql_id and testcase.new_sql_regist_variable:
        new_sql_value = mysqlrun(mysql_id=testcase.new_sql_id, sql=testcase.new_sql,
                                 regist_variable=testcase.new_sql_regist_variable, is_request=False)
        new_sql_value_result = AssertMethod(actual_result=new_sql_value, hope_result=AnalysisParams().analysis_params(testcase.new_sql_hope_result)).assert_method()

    else:
        new_sql_value = new_sql_value_result = ''
    # 调用比较的方法判断响应报文是否满足期望

    print('testcase_test_result:', testcase_test_result)
    if testcase_test_result == "测试失败" or old_sql_value_result == "测试失败" or new_sql_value_result == "测试失败":
        test_result = "测试失败"
    else:
        test_result = "测试成功"
    testcase_result = TestCaseResult(test_case_id, testcase.name, url, data, method, hope_result,
                                     testcase_time_id, response_body, testcase_test_result, old_sql_value=old_sql_value,
                                     new_sql_value=new_sql_value, old_sql_value_result=old_sql_value_result,
                                     new_sql_value_result=new_sql_value_result, result=test_result, scene_id=testcase.testcase_scene_id)
    # 测试结果实例化
    db.session.add(testcase_result)
    db.session.commit()
    return response_body


class TestCaseTimeGet(MethodView):

    def get(self):
        print('current_app.name: ', current_app.name)
        user_id = session.get('user_id')
        time_strftime = datetime.now().strftime('%Y%m%d%H%M%S')
        testcase_time = TestCaseStartTimes(time_strftime=time_strftime, user_id=user_id)
        db.session.add(testcase_time)
        db.session.commit()
        print('testcase_time: ', testcase_time)
        return json.dumps({"testcase_time_id": str(testcase_time.id)})


test_case_request_blueprint.add_url_rule('/testcaserequest/', view_func=TestCaseRequest.as_view('test_case_request'))
test_case_request_blueprint.add_url_rule('/testcaserequeststart/', view_func=TestCaseRequestStart.as_view('test_case_request_start'))
test_case_request_blueprint.add_url_rule('/testcasetimeget/', view_func=TestCaseTimeGet.as_view('test_case_time_get'))