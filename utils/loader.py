# coding: UTF-8
"""
Created on 2015/09/28

@author: Yang Wanjun
"""
import re
import xlrd
import datetime

from django.core.exceptions import ObjectDoesNotExist, MultipleObjectsReturned
from django.db.models import Max
from django.contrib.admin.models import LogEntry, ADDITION, CHANGE
from django.contrib.contenttypes.models import ContentType
from django.utils.text import get_text_list
from django.utils.translation import ugettext as _

from eb.models import Member, Degree, HistoryProject, OS, Skill, ProjectStage
from eb import models

import constants
import common


def load_resume(file_content, member_id=None):
    book = xlrd.open_workbook(file_contents=file_content)
    sheet = book.sheet_by_index(0)

    if member_id is None:
        member = Member()

        # 姓名
        name = sheet.cell(5, 3).value
        member.first_name = common.get_first_last_name(name)[0]
        member.last_name = common.get_first_last_name(name)[1]

        members = Member.objects.raw(u"select * from eb_member"
                                     u" where CONCAT(first_name, last_name) = %s",
                                     [member.first_name + member.last_name])
        members = list(members)
        if members:
            # 読み込んだファイルに同じ名前のメンバーが存在する場合。
            return member, members
        else:
            member_id = 0

    if member_id == 0:
        # 姓名
        member = Member()
        name = sheet.cell(5, 3).value
        member.first_name = common.get_first_last_name(name)[0]
        member.last_name = common.get_first_last_name(name)[1]
        # 基本情報読み込む
        # フリカナ
        name_jp = sheet.cell(4, 3).value
        member.first_name_ja = common.get_first_last_ja_name(name_jp)[0]
        member.last_name_ja = common.get_first_last_ja_name(name_jp)[1]
        # 性別
        sex = sheet.cell(4, 15).value
        if sex and sex in (u"男", u"女"):
            member.sex = '1' if sex == u"男" else "2"
        # 生年月日
        birthday = sheet.cell(8, 15).value
        dt = datetime.datetime(*xlrd.xldate_as_tuple(birthday, book.datemode))
        member.birthday = datetime.date(dt.year, dt.month, dt.day)
        # 最寄駅
        station = sheet.cell(9, 3).value
        member.nearest_station = station.strip() if station else None
    else:
        member = Member.objects.get(pk=member_id)
    # 国家・地域
    country = sheet.cell(6, 15).value
    member.country = country.strip() if country else None
    # 在日年数
    years = sheet.cell(10, 3).value
    if years and years.strip():
        m = re.search(ur"\d+", years)
        member.years_in_japan = int(m.group()) if m else None
    # 婚姻状況
    married = sheet.cell(10, 15).value
    if married and married.strip():
        member.is_married = '0' if married.strip() == u"未婚" else "1"
    # 日本語能力の説明
    japanese = sheet.cell(4, 27).value
    member.japanese_description = japanese.strip() if japanese else None
    # 資格の説明
    certificate = sheet.cell(7, 27).value
    member.certificate = certificate.strip() if certificate else None
    # 得意
    skill_description = sheet.cell(10, 27).value
    member.skill_description = skill_description.strip() if skill_description else None

    if member_id == 0:
        max_employee_id = Member.objects.all().aggregate(Max('employee_id'))
        member.employee_id = common.get_next_employee_id(max_employee_id.get('employee_id__max'))
        member.save()

    # 学歴読み込む
    for row in range(14, sheet.nrows):
        if sheet.cell(row, 5).value:
            period = sheet.cell(row, 5).value
            date_list = []
            for m in re.finditer(constants.REG_DATE_STR, period, re.U):
                date_list.append(common.parse_date_from_string(m.group()))
            if date_list:
                # 学歴のインスタンスを作成
                try:
                    degree = Degree.objects.get(member=member, start_date=date_list[0], end_date=date_list[1])
                except ObjectDoesNotExist:
                    degree = Degree(member=member, start_date=date_list[0], end_date=date_list[1])
                for col in range(6, sheet.ncols):
                    if sheet.cell(row, col).value:
                        degree.description = sheet.cell(row, col).value
                        break
                degree.save()
        else:
            break

    # 業務経歴を読み込む
    start_row = -1
    col_period = col_content = col_os = col_language = col_role = -1
    col_stage_def = col_stage_search = col_stage_bd = col_stage_dd = col_stage_pg = -1
    col_stage_pt = col_stage_it = col_stage_st = col_stage_maintain = col_stage_support = -1
    for row in range(19, sheet.nrows):
        if sheet.cell(row, 0).value and sheet.cell(row, 0).value == u"No.":
            for col in range(sheet.ncols):
                if sheet.cell(row, col).value == u"作業期間":
                    col_period = col
                elif sheet.cell(row, col).value == u"業務内容":
                    col_content = col
                elif sheet.cell(row, col).value == u"機種／OS":
                    col_os = col
                elif u"言語／ツール" in sheet.cell(row, col).value:
                    col_language = col
                elif sheet.cell(row, col).value == u"作業区分":
                    col_role = col
                elif sheet.cell(row, col).value == u"作業工程":
                    col_stage_def = col + 0
                    col_stage_search = col + 1
                    col_stage_bd = col + 2
                    col_stage_dd = col + 3
                    col_stage_pg = col + 4
                    col_stage_pt = col + 5
                    col_stage_it = col + 6
                    col_stage_st = col + 7
                    col_stage_maintain = col + 8
                    col_stage_support = col + 9
            start_row = row + 1
            break

    if start_row > 0:
        for row in range(start_row, sheet.nrows):
            if sheet.cell(row, col_period).value:
                # 作業期間
                date_list = []
                period = sheet.cell(row, col_period).value
                if re.search(constants.REG_DATE_STR, period, re.U):
                    for m in re.finditer(constants.REG_DATE_STR, period, re.U):
                        split1 = m.group(1)
                        split2 = m.group(2)
                        split3 = m.group(3)
                        date_list.append(common.parse_date_from_string(m.group(), split1, split2, split3))
                    else:
                        if u"現在" in period or u"现在" in period and len(date_list) == 1:
                            date_list.append(datetime.date.today())
                elif re.search(constants.REG_DATE_STR2, period, re.U):
                    for m in re.finditer(constants.REG_DATE_STR2, period, re.U):
                        split1 = m.group(1)
                        split2 = m.group(2)
                        date_list.append(common.parse_date_from_string2(m.group(), split1, split2))
                    else:
                        if u"現在" in period or u"现在" in period and len(date_list) == 1:
                            date_list.append(datetime.date.today())
                # 案件名称
                title = sheet.cell(row, col_content).value
                project_name = title.strip() if title else None
                # 業務経歴の対象を作成
                try:
                    project = HistoryProject.objects.get(name=project_name, member=member,
                                                         start_date=date_list[0], end_date=date_list[1])
                except ObjectDoesNotExist:
                    project = HistoryProject(name=project_name, member=member,
                                             start_date=date_list[0], end_date=date_list[1])

                # 作業場所
                for i in range(col_content + 1, col_os):
                    if sheet.cell(row, i).value:
                        location = sheet.cell(row, i).value
                        project.location = location.strip() if location else None
                        break

                # 案件概要
                description = sheet.cell(row + 1, col_content).value
                project.description = description.strip() if description else None
                # 機種／OS
                project_os_list = []
                str_os = sheet.cell(row, col_os).value
                if str_os:
                    os_list = [common.parse_os_lang(os) for os in str_os.split("\n")
                               if common.parse_os_lang(os)]
                    for name in os_list:
                        try:
                            os = OS.objects.get(name=name)
                        except ObjectDoesNotExist:
                            # 存在しない場合は追加する。
                            os = OS(name=name)
                            os.save()
                        project_os_list.append(os)
                # 言語／ツール ＤＢ
                project_skill_list = []
                str_languages = sheet.cell(row, col_language).value
                if str_languages:
                    lang_list = [common.parse_os_lang(lang) for lang in str_languages.split("\n")
                                 if common.parse_os_lang(lang)]
                    for lang in lang_list:
                        try:
                            skill = Skill.objects.get(name=lang)
                        except ObjectDoesNotExist:
                            skill = Skill(name=lang)
                            skill.save()
                        project_skill_list.append(skill)
                # 作業区分
                role = sheet.cell(row, col_role).value
                role = common.parse_project_role(role)
                if role:
                    project.role = role
                # 作業工程
                project_stage_list = []
                for i, col in enumerate((col_stage_def, col_stage_search, col_stage_bd,
                                         col_stage_dd, col_stage_pg, col_stage_pt,
                                         col_stage_it, col_stage_st, col_stage_maintain, col_stage_support)):
                    if sheet.cell(row, col).value:
                        try:
                            stage = ProjectStage.objects.get(name=constants.PROJECT_STAGE[i])
                        except ObjectDoesNotExist:
                            stage = ProjectStage(name=constants.PROJECT_STAGE[i])
                            stage.save()
                        project_stage_list.append(stage)

                # 履歴を保存する
                project.save()
                project.os = project_os_list
                project.skill = project_skill_list
                project.stages = project_stage_list
                project.save()

    member.save()

    return member, None


def load_section_attendance(file_content, year, month, use_id):
    """アップロードした出勤情報をDBに書き込む

    :param file_content: 出勤ファイル
    :param year: 対象年
    :param month: 対象月
    :param use_id: ユーザーID
    :return:
    """
    book = xlrd.open_workbook(file_contents=file_content)
    sheet = book.sheet_by_index(0)

    # フォーマットをチェックする。
    format_error = False
    title1_list = tuple(sheet.row_values(2)[:len(constants.FORMAT_ATTENDANCE_TITLE1)])
    title2_list = tuple(sheet.row_values(3)[:len(constants.FORMAT_ATTENDANCE_TITLE2)])
    if len(title1_list) < len(constants.FORMAT_ATTENDANCE_TITLE1) \
            or len(title2_list) < len(constants.FORMAT_ATTENDANCE_TITLE2):
        format_error = True
    elif title1_list != constants.FORMAT_ATTENDANCE_TITLE1 or title2_list != constants.FORMAT_ATTENDANCE_TITLE2:
        format_error = True

    messages = []
    if format_error:
        return format_error, messages

    for i in range(constants.POS_ATTENDANCE_START_ROW - 1, sheet.nrows):
        values = sheet.row_values(i)
        project_member_id = values[constants.POS_ATTENDANCE_COL_PROJECT_MEMBER_ID]
        # 社員番号
        member_code = values[constants.POS_ATTENDANCE_COL_MEMBER_CODE]
        member_code = member_code if member_code else None
        # 氏名
        member_name = values[constants.POS_ATTENDANCE_COL_MEMBER_NAME]
        member_name = member_name if member_name else None
        # 勤務時間
        total_hours = values[constants.POS_ATTENDANCE_COL_TOTAL_HOURS]
        # 勤務日数
        total_days = values[constants.POS_ATTENDANCE_COL_TOTAL_DAYS]
        total_days = total_days if total_days else None
        # 深夜日数
        night_days = values[constants.POS_ATTENDANCE_COL_NIGHT_DAYS]
        night_days = night_days if night_days else None
        # 客先立替金
        advances_paid_client = values[constants.POS_ATTENDANCE_COL_ADVANCES_PAID_CLIENT]
        advances_paid_client = advances_paid_client if advances_paid_client else None
        # 立替金
        advances_paid = values[constants.POS_ATTENDANCE_COL_ADVANCES_PAID]
        advances_paid = advances_paid if advances_paid else None
        # 勤務交通費
        traffic_cost = values[constants.POS_ATTENDANCE_COL_TRAFFIC_COST]
        traffic_cost = traffic_cost if traffic_cost != '' else None
        # 手当
        allowance = values[constants.POS_ATTENDANCE_COL_ALLOWANCE]
        allowance = allowance if allowance else None
        # 経費(原価)
        expenses = values[constants.POS_ATTENDANCE_COL_EXPENSES]
        expenses = expenses if expenses else None
        # 会議費
        expenses_conference = values[constants.POS_ATTENDANCE_COL_EXPENSES_CONFERENCE] or 0
        # 交際費
        expenses_entertainment = values[constants.POS_ATTENDANCE_COL_EXPENSES_ENTERTAINMENT] or 0
        # 旅費交通費
        expenses_travel = values[constants.POS_ATTENDANCE_COL_EXPENSES_TRAVEL] or 0
        # 通信費
        expenses_communication = values[constants.POS_ATTENDANCE_COL_EXPENSES_COMMUNICATION] or 0
        # 租税公課
        expenses_tax_dues = values[constants.POS_ATTENDANCE_COL_EXPENSES_TAX_DUES] or 0
        # 消耗品
        expenses_expendables = values[constants.POS_ATTENDANCE_COL_EXPENSES_EXPENDABLES] or 0

        if not project_member_id:
            if member_code or member_name:
                messages.append((project_member_id, member_code, member_name, u"ID情報が取れません。"))
            continue
        try:
            project_member = models.ProjectMember.objects.get(pk=project_member_id)
        except ObjectDoesNotExist:
            messages.append((project_member_id, member_code, member_name, u"IDによりDBからデータ取得できません。"))
            continue

        if total_hours is None or total_hours == "":
            # 空白の場合
            messages.append((project_member_id, member_code, member_name, constants.ERROR_INVALID_TOTAL_HOUR))
            continue
        if not isinstance(total_hours, float) \
                and not isinstance(total_hours, int) \
                and not isinstance(total_hours, long):
            # 数値ではない場合。
            messages.append((project_member_id, member_code, member_name, constants.ERROR_INVALID_TOTAL_HOUR))
            continue

        total_hours = common.get_attendance_total_hours(total_hours, project_member.project.attendance_type)
        if project_member.project.request_type == '03':
            prev_date = common.add_months(datetime.date(int(year), int(month), 1), -1)
            prev_attendance = project_member.get_attendance(prev_date.strftime('%Y'), prev_date.strftime('%m'))
            prev_carryover_hours = prev_attendance.carryover_hours if prev_attendance else 0
            extra_hours = 0
            price = project_member.price * (project_member.min_hours + prev_carryover_hours)
        else:
            if total_hours > float(project_member.max_hours):
                # 残業あり
                extra_hours = total_hours - float(project_member.max_hours)
                price = float(project_member.price) + extra_hours * float(project_member.plus_per_hour)
            elif total_hours < float(project_member.min_hours):
                # 欠勤あり
                extra_hours = total_hours - float(project_member.min_hours)
                price = float(project_member.price) + extra_hours * float(project_member.minus_per_hour)
            else:
                extra_hours = 0
                price = project_member.price

        attendance = project_member.get_attendance(year, month)
        has_requested = False
        if attendance and attendance.get_project_request_detail() is not None:
            # 既に出勤情報あり且つ請求書作成済み。
            has_requested = True

        changed_list = []
        if attendance:
            # 勤務交通費が空白の場合は先月のを使用する。
            if traffic_cost is None:
                traffic_cost = attendance.get_prev_traffic_cost()
            # 手当が空白の場合は先月のを使用する。
            if not allowance:
                allowance = attendance.get_prev_allowance()
            action_flag = CHANGE
            attendance.total_days = total_days if total_days else None
            attendance.night_days = night_days if night_days else None
            if not has_requested:
                # 請求書作成済みの場合は上書きしない。
                attendance.total_hours = total_hours
                attendance.extra_hours = extra_hours
                attendance.price = price
                common.get_object_changed_message(attendance, 'total_hours', total_hours, changed_list)
                common.get_object_changed_message(attendance, 'extra_hours', extra_hours, changed_list)
                common.get_object_changed_message(attendance, 'price', price, changed_list)
            attendance.advances_paid = advances_paid
            attendance.advances_paid_client = advances_paid_client
            attendance.traffic_cost = traffic_cost
            attendance.allowance = allowance
            attendance.expenses = expenses
        else:
            attendance = models.MemberAttendance(project_member=project_member,
                                                 year=year, month=month,
                                                 rate=1,
                                                 basic_price=project_member.price,
                                                 total_hours=total_hours,
                                                 extra_hours=extra_hours,
                                                 total_days=total_days if total_days else None,
                                                 night_days=night_days if night_days else None,
                                                 min_hours=project_member.min_hours,
                                                 max_hours=project_member.max_hours,
                                                 plus_per_hour=project_member.plus_per_hour,
                                                 minus_per_hour=project_member.minus_per_hour,
                                                 price=price,
                                                 advances_paid=advances_paid,
                                                 advances_paid_client=advances_paid_client,
                                                 traffic_cost=traffic_cost,
                                                 allowance=allowance,
                                                 expenses=expenses)
            action_flag = ADDITION
            common.get_object_changed_message(attendance, 'total_hours', total_hours, changed_list)
            common.get_object_changed_message(attendance, 'extra_hours', extra_hours, changed_list)
            common.get_object_changed_message(attendance, 'price', price, changed_list)
        # 経費（原価ではない）
        attendance.expenses_conference = expenses_conference
        attendance.expenses_entertainment = expenses_entertainment
        attendance.expenses_travel = expenses_travel
        attendance.expenses_communication = expenses_communication
        attendance.expenses_tax_dues = expenses_tax_dues
        attendance.expenses_expendables = expenses_expendables
        # 修正履歴
        common.get_object_changed_message(attendance, 'total_days', total_days, changed_list)
        common.get_object_changed_message(attendance, 'night_days', night_days, changed_list)
        common.get_object_changed_message(attendance, 'advances_paid', advances_paid, changed_list)
        common.get_object_changed_message(attendance, 'advances_paid_client', advances_paid_client, changed_list)
        common.get_object_changed_message(attendance, 'traffic_cost', traffic_cost, changed_list)
        common.get_object_changed_message(attendance, 'allowance', allowance, changed_list)
        common.get_object_changed_message(attendance, 'expenses', expenses, changed_list)
        common.get_object_changed_message(attendance, 'expenses_conference', expenses_conference, changed_list)
        common.get_object_changed_message(attendance, 'expenses_entertainment', expenses_entertainment, changed_list)
        common.get_object_changed_message(attendance, 'expenses_travel', expenses_travel, changed_list)
        common.get_object_changed_message(attendance, 'expenses_communication', expenses_communication, changed_list)
        common.get_object_changed_message(attendance, 'expenses_tax_dues', expenses_tax_dues, changed_list)
        common.get_object_changed_message(attendance, 'expenses_expendables', expenses_expendables, changed_list)
        if action_flag == CHANGE:
            change_message = _('Changed %s.') % get_text_list(changed_list, _('and')) if changed_list else ''
        else:
            change_message = (get_text_list(changed_list, _('and')) if changed_list else '') + _('Added.')

        if project_member.project.request_type == '03':
            attendance.carryover_hours = float(attendance.total_hours) - float(project_member.min_hours)
        attendance.save()
        # 客先立替金は精算リストに追加する。
        if attendance.advances_paid_client:
            try:
                models.MemberExpenses.objects.get(project_member=attendance.project_member,
                                                  year=attendance.year, month=attendance.month,
                                                  price=attendance.advances_paid_client)
            except ObjectDoesNotExist:
                category = models.Config.get_default_expenses_category()
                if category:
                    # 既定の精算分類が設定された場合
                    expenses = models.MemberExpenses(project_member=attendance.project_member,
                                                     year=attendance.year, month=attendance.month,
                                                     category=category, price=attendance.advances_paid_client)
                    expenses.save()
                    LogEntry.objects.log_action(user_id=use_id,
                                                content_type_id=ContentType.objects.get_for_model(expenses).pk,
                                                object_id=expenses.pk,
                                                object_repr=unicode(expenses),
                                                action_flag=ADDITION,
                                                change_message=u"【データ導入】追加されました。")
            except MultipleObjectsReturned:
                pass
        if change_message:
            LogEntry.objects.log_action(user_id=use_id,
                                        content_type_id=ContentType.objects.get_for_model(attendance).pk,
                                        object_id=attendance.pk,
                                        object_repr=unicode(attendance),
                                        action_flag=action_flag,
                                        change_message=(u" 【データ導入】" + change_message) or _('No fields changed.'))
    return format_error, messages
