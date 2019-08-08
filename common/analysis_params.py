import re
import json
from app import cdb


class AnalysisParams:

    def __init__(self):
        variables_query_sql = 'select name from variables'
        self.variables = cdb().query_db(variables_query_sql)
        print('init:self.variables:', self.variables)

    def analysis_params(self,  params, is_change=None):
        if params is "":
            return params
        while 1:
            print('analysis_before:', params)
            res = r'\${([^\${}]+)}'
            words = re.findall(re.compile(res), params)
            print('请求报文：%s, 筛选出的变量: %s' % (params, words))
            if len(words) == 0:
                return params
            for word in words:
                if (word,) in self.variables:
                    variable_value_query_sql = 'select value from variables where name=?'
                    variable_value = cdb().query_db(variable_value_query_sql, (word,), True)[0]
                    print('variable_value: ${%s}' % word, variable_value)
                    if is_change == "headers":
                        params = params.replace('${%s}' % word, '"%s"' % variable_value)
                    params = params.replace('${%s}' % word, variable_value)
                else:
                    continue
            print('解析后的参数为:', params)

    def analysis_headers(self, headers):
        print('header_before:', headers)
        header = headers.replace(' ', '').replace('\n', '').replace('\r', '')
        return header

    # def analysis_boject_value(self, object):



if __name__ == '__main__':
    AnalysisParams().analysis_params('{btest{A}{B}{C}hhh')