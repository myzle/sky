# encoding=utf-8

import collections
import importlib
import logging
import re
import sys
import time
import openpyxl
from multiprocessing import Manager
import config
import os
from datetime import datetime
from time import sleep


def get_config(product_name):
    if product_name == 'qb':
        importlib.reload(config)
        monitor_api_task = config.monitor_api_task
        monitor_api_circle = config.monitor_circle
        return monitor_api_task, monitor_api_circle
    else:
        print('config_file does not exist')
        return


def timer():
    communication_dict = Manager().dict()
    communication_dict['qb_result'] = False
    print(communication_dict)

    if not os.path.exists('log'):
        os.mkdir('log')
    log_file = os.path.join(os.path.abspath('.'), 'log',
                            'sky' + datetime.now().strftime('%Y%m%d%H%M') + '.txt')
    log = logging.getLogger('sky')
    log.setLevel(logging.DEBUG)
    stream_handler = logging.StreamHandler()
    stream_handler.setLevel(logging.INFO)
    file_handler = logging.FileHandler(log_file)
    file_handler.setLevel(logging.DEBUG)
    log_formate = logging.Formatter('%(asctime)s  %(filename)s %(message)s')
    stream_handler.setFormatter(log_formate)
    file_handler.setFormatter(log_formate)
    log.addHandler(stream_handler)
    log.addHandler(file_handler)

    log.info('启动')
    while True:
        try:
            if '08:00:59' > datetime.now().strftime('%H:%M:%S') > '08:00:00' or '12:00:59' > datetime.now().strftime(
                    '%H:%M:%S') > '12:00:00' or '15:00:59' > datetime.now().strftime(
                    '%H:%M:%S') > '15:00:00' or '17:00:59' > datetime.now().strftime('%H:%M:%S') > '17:00:00':
                api_monitor('qb', communication_dict, '33389629472769')
                print(communication_dict)

                # if communication_dict['qb_result'] is True:
                #     print('开始发送图片')
                #     # send_pic()
                sleep(60)
            else:
                pass
        except KeyboardInterrupt as e:
            log.info(e)
            time.sleep(1)
            sys.exit()
        except BaseException as e:
            if isinstance(e, SystemExit):
                sys.exit()
            else:
                error_info = sys.exc_info()
                print(error_info)


def api_monitor(product_name, comm_dict, receive_group_id, status=False):
    monitor_api_task, monitor_api_circle = get_config(product_name)
    if not os.path.exists('log'):
        os.mkdir('log')
    log_file = os.path.join(os.path.abspath('.'), 'log',
                            'sky_api_' + datetime.now().strftime('%Y%m%d%H%M') + '.txt')
    log = logging.getLogger('sky_api')
    log.setLevel(logging.DEBUG)
    stream_handler = logging.StreamHandler()
    stream_handler.setLevel(logging.INFO)
    file_handler = logging.FileHandler(log_file)
    file_handler.setLevel(logging.DEBUG)
    log_formate = logging.Formatter('%(asctime)s  %(filename)s %(message)s')
    stream_handler.setFormatter(log_formate)
    file_handler.setFormatter(log_formate)
    log.addHandler(stream_handler)
    log.addHandler(file_handler)

    if len(monitor_api_task) > 0:
        for task in monitor_api_task:
            case_file = task.get('case_file', None)
            argv_file = task.get('argv_file', None)
            name = task.get('packagename', None)
            case_list = task.get('case_list', None)
            if case_file is not None and argv_file is not None and name is not None:
                result_html_file = os.path.join(os.path.split(case_file)[0],
                                                datetime.now().strftime('%Y%m%d%H%M%S') + '.html')
                result_txt_file = os.path.join(os.path.split(case_file)[0],
                                               datetime.now().strftime('%Y%m%d%H%M%S') + '.txt')
                excute_string = ''' newman run {0} --globals {1}  --timeout-request 30000 --reporters cli,html --reporter-html-export {2} >{3}'''.format(
                    case_file, argv_file, result_html_file, result_txt_file)

                log.debug(excute_string)
                os.system(excute_string)
                try:
                    contents_sms = read_newman_console_result(case_list, product_name, result_txt_file,
                                                              comm_dict, receive_group_id, status)
                    print(contents_sms)
                except BaseException as e:
                    log.info(e)
                # if contents_sms.find('fail')>-1 or contents_sms.find('timeout')>-1:
                print('---------------------------------------------')

            else:
                log.info('接口测试配置文件错误,接口巡检退出')
                return
    else:
        log.info('接口测试没有任务,退出')
        return


def read_newman_console_result(case_list, name, filename, communication_dict, receive_group_id, status=False):
    log = logging.getLogger('sky_api')
    case_list = case_list.split()
    apiid_apiname_list = []
    for n in case_list:
        log.debug(n)
        apiid_apiname_list.append(n.split('-')[0])
        apiid_apiname_list.append(n.split('-')[1])
        # apiid_apiname_list.append(n.split('-')[2])
    apiid_apiinfo_oderdict = collections.OrderedDict()
    for n in range(0, len(apiid_apiname_list), 2):
        apiid_apiinfo_oderdict[apiid_apiname_list[n]] = [apiid_apiname_list[n + 1], '', '']
    log.debug(apiid_apiinfo_oderdict)

    with open(filename, 'r', encoding='utf-8') as f:
        result = []
        lines = f.readlines()
        # print(lines)
        # 过滤结尾无用的行
        for line in lines:
            if 'AssertionFailure' in line or 'AssertionError' in line:
                # print(lines.index(line))
                lines = lines[:lines.index(line)]
                break

        print(lines)
        print('---------------------------------------------')
        for line in lines:
            if len(re.findall('[\_\-][0-9]{4}$', line)) > 0:
                apiid = re.findall('[0-9]+', line)
                if len(apiid) > 0:
                    apiid = apiid[0]
                result.append(apiid)
            elif line.find('POST') > -1 or line.find('GET') > -1:
                times = line[line.find('[') + 1:-2]
                result.append(times)
            elif line.find('Result:Pass') > -1 or line.find('Result:Failed') > -1:
                result.append(line)

        print(result)

        # get api index in the result
        api_position = []
        for index, item in enumerate(result):
            if len(item) == 4:
                api_position.append(index)
        print(api_position)
        api_position.append(len(result))

        # 获取两个api之间的index区间
        api_results = []
        for i in range(0, len(api_position)-1):
            api_results.append(api_position[i:i+2])

        print(api_results)

        # 截取result中每个api对应的字段
        final_results = []
        for item in api_results:
            final_results.append(result[item[0]:item[1]])

        print(final_results)
        for item in final_results:
            print(item)

        # 开始处理最后的结果
        print('##开始处理最后的结果##')
        if name in ['qb']:

            for item in final_results:
                if 'errored' in item[1]:
                    apiid_apiinfo_oderdict[item[0]][1] = 'errored'
                    continue
                elif '500 Internal Server Error' in item[1]:
                    apiid_apiinfo_oderdict[item[0]][1] = '500Error'
                    continue
                else:
                    if '200 OK' in item[1]:
                        apiid_apiinfo_oderdict[item[0]][1] = 'pass'
                        times = item[1].split(',')[2].strip()
                        apiid_apiinfo_oderdict[item[0]][2] = times
                    if 'JSONError' in item[2]:
                        apiid_apiinfo_oderdict[item[0]][1] = 'Exception'
                        apiid_apiinfo_oderdict[item[0]][2] = 'JSONError'
                    else:
                        if 'Result:Failed' in item[3]:
                            apiid_apiinfo_oderdict[item[0]][1] = 'APIfail'
                            s1 = str(item[3])
                            apifailed_info = 'result=' + s1[s1.find('实际值：') + 4:-2]
                            apiid_apiinfo_oderdict[item[0]][2] = apifailed_info

                        else:
                            if len(item) >= 4:
                                for child_item in item[3:len(item)]:
                                    if 'Failed' in child_item:
                                        apiid_apiinfo_oderdict[item[0]][1] = 'Datafail'
                                        s_original = str(child_item)
                                        s2 = s_original[s_original.find('response') + 8:-1]
                                        s3 = s2.replace('期待包含：', 'EXP:')
                                        s4 = s3.replace('期待值：', 'EXP:')
                                        s5 = s4.replace('实际值：', 'ACT:')
                                        s6 = s5.replace('期待包含的数据为：', 'toHava:')
                                        apiid_apiinfo_oderdict[item[0]][2] = s6
                                        break
        else:
            for item in final_results:
                if 'errored' in item[1]:
                    apiid_apiinfo_oderdict[item[0]][1] = 'errored'
                    continue
                elif '500 Internal Server Error' in item[1]:
                    apiid_apiinfo_oderdict[item[0]][1] = '500Error'
                    continue
                else:
                    if '200 OK' in item[1]:
                        apiid_apiinfo_oderdict[item[0]][1] = 'pass'
                        times = item[1].split(',')[2].strip()
                        apiid_apiinfo_oderdict[item[0]][2] = times
                    if 'JSONError' in item[2]:
                        apiid_apiinfo_oderdict[item[0]][1] = 'Exception'
                        apiid_apiinfo_oderdict[item[0]][2] = 'JSONError'
                    else:

                        if len(item) >= 3:
                            for child_item in item[2:len(item)]:
                                if 'Failed' in child_item:
                                    apiid_apiinfo_oderdict[item[0]][1] = 'Datafail'
                                    s_original = str(child_item)
                                    s2 = s_original[s_original.find('response') + 8:-1]
                                    s3 = s2.replace('期待包含：', 'EXP:')
                                    s4 = s3.replace('期待值：', 'EXP:')
                                    s5 = s4.replace('实际值：', 'ACT:')
                                    s6 = s5.replace('期待包含的数据为：', 'toHava:')
                                    apiid_apiinfo_oderdict[item[0]][2] = s6
                                    break

        # print(apiid_apiinfo_oderdict)

    contents_sms = ''

    print('**********************************************')
    # add a method to store result in the excel file
    report_path = os.path.join(os.path.expanduser('~'), 'Desktop', 'sky')
    if not os.path.exists(report_path):
        os.mkdir(report_path)
    print(apiid_apiinfo_oderdict)
    create_api_report(apiid_apiinfo_oderdict, report_path, communication_dict, name, receive_group_id, status)
    return contents_sms


def create_api_report(result, report_path, communication_dict, product_name, receive_group_id, status=False):
    if result is None:
        print('接口结果为空，退出')
        return
    elif report_path is None:
        print('报告保存地址为空，退出')
    else:
        os.chdir(report_path)
        current_time = datetime.now().strftime('%Y%m%d%H%M%S')
        mywb = openpyxl.Workbook()
        sheet = mywb.get_sheet_by_name('Sheet')
        sheet['A1'].value = product_name + ' api巡检报告'
        sheet['A2'].value = '接口编号'
        sheet['C2'].value = '接口名称'
        sheet['E2'].value = '接口状态'
        sheet['G2'].value = '接口时间'
        i = 2

        error_count = 0
        for key, value in result.items():
            sheet['A' + str(i + 1)].value = key
            sheet['C' + str(i + 1)].value = value[0]
            sheet['E' + str(i + 1)].value = value[1]
            if value[1] != 'pass':
                error_count = error_count + 1

            sheet['G' + str(i + 1)].value = value[2]
            i = i + 1
        mywb.save(current_time + product_name + '.xlsx')

        print(os.path.abspath('') + '/' + current_time + '.xlsx')
        print('-------------------------------')
        print(error_count)
        print('-------------------------------')
        if error_count == 0:
            communication_dict[product_name + '_result'] = True
            print(communication_dict)
        else:
            communication_dict[product_name + '_result'] = False
            print(communication_dict)
        if status is True:
            print(os.path.abspath('') + '/' + current_time + '.xlsx')
            apireport_path = os.path.abspath('') + '/' + current_time + product_name + '.xlsx'
            print('-------------------------------')
            print(error_count)
            print('-------------------------------')
            # 发送图片：
            print('达到图片发送标准！！！！')
            # generate_jpg_from_excel_and_send_to_group(receive_group_id, apireport_path, [1, 3, 5, 7])


# def send_pic():
#     jpg_url = 'https://air.hecom.cn/herobot.jpg'
#     httplib2.debuglevel = 4
#     h = httplib2.Http()
#     send_jpg_url = jpg_url
#     url_data = 'https://mm.hecom.cn/mobile-0.0.1-SNAPSHOT/rcm/common/user/sendGroupImage.do?userStr=' \
#                '{"receiveGroupId":"33389629472769","sendUid":"rcmuser10062739","url":"' + send_jpg_url + \
#                '","key":"xiaojiejie654321"}'
#     r, c = h.request(uri=url_data)
#
#     if r.status == 429 or r.status == 503:
#         print('被限流')
#         return 'error'
#
#     return 'success'


if __name__ == '__main__':

    timer()
