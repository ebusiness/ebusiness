# coding: UTF-8
"""
Created on 2016/01/12

@author: Yang Wanjun
"""
import os
import urllib2
import json
import datetime

import models

from django.db.models import Q
from django.contrib.auth.models import User
from django.core.exceptions import ObjectDoesNotExist

from openpyxl import load_workbook
from openpyxl.writer.excel import save_virtual_workbook

from utils import common, constants, errors


def get_company():
    company_list = models.Company.objects.all()
    if company_list.count() == 0:
        return None
    else:
        return company_list[0]


def get_admin_user():
    try:
        return User.objects.get(username='admin')
    except ObjectDoesNotExist:
        return None


def get_all_members(user=None):
    if user:
        if user.is_superuser:
            return models.Member.objects.public_filter(Q(section__is_on_sales=True) | Q(member_type=4))
        elif common.is_salesperson(user):
            return user.salesperson.get_all_members()

    return models.Member.objects.none()


def get_working_members(user=None):
    now = datetime.date.today()
    if user:
        if user.is_superuser:
            # 管理員の場合全部見られる
            members = models.Member.objects.public_filter(Q(section__is_on_sales=True) | Q(member_type=4),
                                                          projectmember__start_date__lte=now,
                                                          projectmember__end_date__gte=now,
                                                          projectmember__status=2)
            return members
        elif common.is_salesperson(user):
            # 営業員の場合、担当している社員だけ見られる
            return user.salesperson.get_working_members()

    return models.Member.objects.none()


def get_waiting_members(user=None):
    if user:
        if user.is_superuser:
            # 管理員の場合全部見られる
            working_members = get_working_members(user)
            members = get_all_members(user).exclude(pk__in=working_members)
            return members
        elif common.is_salesperson(user):
            # 営業員の場合、担当している社員だけ見られる
            return user.salesperson.get_waiting_members()

    return models.Member.objects.none()


def get_project_members_month(date):
    """指定月の案件メンバー全部取得する。

    :param date 指定月
    """
    first_day = common.get_first_day_by_month(date)
    today = datetime.date.today()
    if date.year == today.year and date.month == today.month:
        first_day = today
    last_day = common.get_last_day_by_month(date)
    return models.ProjectMember.objects.public_filter(end_date__gte=first_day,
                                                      end_date__lte=last_day,
                                                      status=2)


def get_release_members_by_month(date, salesperson=None, is_superuser=False):
    """指定営業員配下の案件メンバー取得する。

    :param date 指定月
    :param salesperson 指定営業員配下の案件メンバー
    :param is_superuser スーパーユーザ
    """
    if salesperson:
        return get_project_members_month(date).filter(member__salesperson__in=salesperson.get_under_salesperson())
    elif is_superuser:
        return get_project_members_month(date)
    return models.ProjectMember.objects.none()


def get_release_current_month(salesperson=None, is_superuser=False):
    """指定営業員配下の当月の案件メンバー取得する。

    :param salesperson 指定営業員配下の案件メンバー
    :param is_superuser スーパーユーザ
    """
    return get_release_members_by_month(datetime.date.today(), salesperson, is_superuser)


def get_release_next_month(salesperson=None, is_superuser=False):
    """指定営業員配下の来月の案件メンバー取得する。

    :param salesperson 指定営業員配下の案件メンバー
    :param is_superuser スーパーユーザ
    """
    next_month = common.add_months(datetime.date.today(), 1)
    return get_release_members_by_month(next_month, salesperson, is_superuser)


def get_release_next_2_month(salesperson=None, is_superuser=False):
    """指定営業員配下の再来月の案件メンバー取得する。

    :param salesperson 指定営業員配下の案件メンバー
    :param is_superuser スーパーユーザ
    """
    next_2_month = common.add_months(datetime.date.today(), 2)
    return get_release_members_by_month(next_2_month, salesperson, is_superuser)


def sync_members():
    company = get_company()
    response = urllib2.urlopen(constants.URL_SYNC_MEMBERS)
    html = response.read()
    dict_data = json.loads(html.replace("\r", "").replace("\n", ""))
    message_list = []
    if 'employeeList' in dict_data:
        for data in dict_data.get("employeeList"):
            employee_code = data.get("id", None)
            name = data.get("name", None)
            birthday = data.get("birthDate", None)
            address = data.get("address", None)
            department_name = data.get("department", None)
            eb_mail = data.get("ebMailAddress", None)
            introduction = data.get("introduction", None)
            join_date = data.get("joinDate", None)
            name_jp = data.get("kana", None)
            private_mail = data.get("mailAddress", None)
            phone = data.get("phone", None)
            postcode = data.get("postcode", None)
            sex = data.get("sex", None)
            station = data.get("station", None)
            if employee_code:
                if department_name == u"営業部" or employee_code in ('0123', '0126', '0198', '0150', '0249', '0335'):
                    # 0123 馬婷婷
                    # 0150 孫雲釵
                    # 0198 劉 暢
                    # 0126 丁 玲
                    # 0249 齋藤 善次
                    # 0335 蒋杰
                    if models.Salesperson.objects.filter(employee_id=employee_code).count() == 0:
                        member = models.Salesperson(employee_id=employee_code)
                    else:
                        # message_list.append(("WARN", name, birthday, address, u"既に存在しているレコードです。"))
                        continue
                else:
                    if models.Member.objects.filter(employee_id=employee_code).count() == 0:
                        member = models.Member(employee_id=employee_code)
                    else:
                        # message_list.append(("WARN", name, birthday, address, u"既に存在しているレコードです。"))
                        continue

                try:
                    # コストを取得する。
                    member.first_name = common.get_first_last_name(name)[0]
                    member.last_name = common.get_first_last_name(name)[1]
                    if name_jp:
                        lst = common.get_first_last_ja_name(name_jp)
                        if len(lst) == 2 and lst[0]:
                            member.first_name_ja = common.get_first_last_ja_name(name_jp)[0]
                            member.last_name_ja = common.get_first_last_ja_name(name_jp)[1]
                        elif len(lst) == 1:
                            member.first_name_ja = common.get_first_last_ja_name(name_jp)[0]
                    if birthday:
                        try:
                            member.birthday = common.parse_date_from_string(birthday)
                        except Exception as ex:
                            print ex.message
                            message_list.append(("WARN", name, birthday, address, u"生年月日が存在しません。"))
                            member.birthday = None
                    else:
                        member.birthday = datetime.date.today()
                    member.address1 = address if address else station
                    if department_name:
                        try:
                            section = models.Section.objects.get(name=department_name)
                        except ObjectDoesNotExist:
                            section = models.Section(name=department_name)
                            section.company = company
                            section.save()
                        member.section = section
                    member.email = eb_mail
                    member.private_email = private_mail
                    member.comment = introduction
                    if join_date:
                        member.join_date = common.parse_date_from_string(join_date)
                    if phone:
                        member.phone = phone.replace("-", "")
                    if postcode:
                        member.post_code = postcode.strip().replace("/", "").replace("-", "").strip()
                        if len(member.post_code.strip()) == 8:
                            member.post_code = member.post_code[3:] + member.post_code[4:]
                        if len(member.post_code) != 7:
                            member.post_code = None
                    member.nearest_station = station if station and len(station) <= 15 else None
                    member.sex = "2" if sex == "0" else "1"
                    member.cost = get_cost(employee_code)
                    member.company = company
                    member.save()
                    message_list.append(("INFO", name, birthday, address, u"完了"))
                except Exception as e:
                    message_list.append(("ERROR", name, birthday, address, u"エラー：" + str(e)))
    return message_list


def get_cost(code):
    if code:
        url = constants.URL_CONTRACT % (code,)
        response = urllib2.urlopen(url)
        html = response.read()
        data = json.loads(html.replace("\r", "").replace("\n", ""))
        period_list = []
        for item in data['contractList']:
            period_list.append(item['EMPLOYMENT_PERIOD_END'])
        latest_period = None
        if period_list:
            latest_period = max(period_list)
        for item in data['contractList']:
            if latest_period and item['EMPLOYER_NO'] == code and item['EMPLOYMENT_PERIOD_END'] == latest_period:
                if item['ALLOWANLE_COST'] != "-":
                    return item['ALLOWANLE_COST']
        for item in data['contractList']:
            if item['EMPLOYER_NO'] == code:
                return item['ALLOWANLE_COST'] if item['ALLOWANLE_COST'] != "-" else 0
    return 0


def company_turnover_month(ym, client_id=None):
    first_day = common.get_first_day_from_ym(ym)

    client_turnovers = []

    if client_id:
        clients = models.Client.objects.public_filter(pk=client_id)
    else:
        clients = models.Client.objects.public_all()

    for client in clients:
        d = dict()
        d['id'] = client.pk
        d['name'] = client.name
        d.update(client.get_turnover_month(first_day))
        client_turnovers.append(d)

    return client_turnovers


def get_salesperson_director():
    """営業の管理者を取得する。
    """
    return models.Salesperson.objects.public_filter(member_type=0, is_notify=True)


def get_salesperson_members():
    """営業のメンバーを取得する。
    """
    return models.Salesperson.objects.public_filter(member_type=5, is_notify=True)


def get_members_information():
    status_list = []
    summary = {'all_member_count': 0,
               'working_member_count': 0,
               'waiting_member_count': 0,
               'current_month_count': 0,
               'next_month_count': 0,
               'next_2_month_count': 0,
               }
    for salesperson in models.Salesperson.objects.public_filter(user__isnull=False, member_type=5):
        d = dict()
        d['salesperson'] = salesperson
        d['all_member_count'] = salesperson.get_all_members().count()
        d['working_member_count'] = salesperson.get_working_members().count()
        d['waiting_member_count'] = salesperson.get_waiting_members().count()
        d['current_month_count'] = get_release_current_month(salesperson).count()
        d['next_month_count'] = get_release_next_month(salesperson).count()
        d['next_2_month_count'] = get_release_next_2_month(salesperson).count()
        status_list.append(d)

        summary['all_member_count'] += d['all_member_count']
        summary['working_member_count'] += d['working_member_count']
        summary['waiting_member_count'] += d['waiting_member_count']
        summary['current_month_count'] += d['current_month_count']
        summary['next_month_count'] += d['next_month_count']
        summary['next_2_month_count'] += d['next_2_month_count']

    return status_list, summary


def get_order_no(user):
    """注文番号を取得する。

    :param user ログインしているユーザ
    """
    prefix = '#'
    today = datetime.date.today()
    if hasattr(user, 'salesperson'):
        if user.salesperson.first_name_en:
            prefix = user.salesperson.first_name_en[0]

    return "EB{0:04d}{1:02d}{2:02d}{3}{4}".format(today.year, today.month, today.day, prefix, "01")


def get_order_filename(subcontractor, order_no):
    """生成した註文書の名称を取得する。

    :param subcontractor 発注先
    :param order_no 請求番号
    :return 註文書の名称
    """
    return u"{0}_{1}".format(order_no, subcontractor.name)


def get_user_profile(user):
    """ログインしているユーザの詳細情報を取得する。

    :param user ログインしているユーザ
    """
    if hasattr(user, 'salesperson'):
        return user.salesperson
    return None


def generate_order(company, data):
    """註文書を生成する。

    :param company 発注元会社
    :param data 註文書の出力データ
    :return エクセルのバイナリー
    """
    # members = subcontractor.member_set.all()

    # テンプレートを取得する
    order_file = company.order_file
    if not order_file or not os.path.exists(order_file.path):
        raise errors.FileNotExistException(constants.ERROR_TEMPLATE_NOT_EXISTS)

    # 新しいエクセルを作成する。
    wb = load_workbook(order_file.path)
    ws = wb.active
    for row in ws.rows:
        for cell in row:
            if cell and cell.value:
                replacements = common.get_excel_replacements(cell.value)
                if replacements:
                    for replacement in replacements:
                        val = data.get(replacement, "{$" + replacement + "$}")
                        cell.value = cell.value.replace("{$" + replacement + "$}", val)

    return save_virtual_workbook(wb)


def generate_order_data(company, subcontractor, user, ym):
    """註文書を生成するために使うデータを生成する。

    :param company 発注元会社
    :param subcontractor 発注先
    :param user ログインしているユーザ
    :param ym 対象年月
    :return エクセルのバイナリー
    """
    data = dict()
    # 注文番号
    data['ORDER_NO'] = get_order_no(user)
    # 発行年月日
    date = datetime.date.today()
    data['PUBLISH_DATE'] = u"%s年%02d月%02d日" % (date.year, date.month, date.day)
    # 下請け会社名
    data['SUBCONTRACTOR_NAME'] = subcontractor.name
    # 作成者
    salesperson = get_user_profile(user)
    data['AUTHOR_FIRST_NAME'] = salesperson.first_name if salesperson else ''
    # 会社名
    data['COMPANY_NAME'] = company.name
    # 本社郵便番号
    data['POST_CODE'] = common.get_full_postcode(company.post_code)
    # 本社電話番号
    data['TEL'] = company.tel
    # 代表取締役
    member = company.get_master()
    data['MASTER'] = u"%s %s" % (member.first_name, member.last_name) if member else ""
    # 本社住所
    data['ADDRESS1'] = company.address1
    data['ADDRESS2'] = company.address2
    # 作業期間
    if not ym:
        first_day = common.get_first_day_current_month()
    else:
        first_day = common.get_first_day_from_ym(ym)
    last_day = common.get_last_day_by_month(first_day)
    data['START_DATE'] = u"%s年%02d月%02d日" % (first_day.year, first_day.month, first_day.day)
    data['END_DATE'] = u"%s年%02d月%02d日" % (last_day.year, last_day.month, last_day.day)

    return data