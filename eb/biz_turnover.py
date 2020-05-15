# -*- coding: utf-8 -*-
"""
Created on 2016/06/02

@author: Yang Wanjun
"""
from __future__ import unicode_literals
import datetime
import StringIO
import matplotlib.pyplot as plt
from matplotlib.ticker import FuncFormatter
import pandas as pd
import numpy as np

from eb import models, biz
from utils import common

from django.db.models import Sum, Count, Q, Value
from django.db.models.functions import Concat
from django.core.exceptions import ObjectDoesNotExist
from django.db import connection
from django.contrib.humanize.templatetags import humanize


def turnover_company_year():
    """年単位の会社の売上情報を取得する。

    :return: QuerySet
    """
    turnover_year = models.ProjectRequest.objects.filter(projectrequestheading__isnull=False).\
        values('year',).\
        annotate(amount__sum=Sum('amount'),
                 turnover_amount=Sum('turnover_amount'),
                 tax_amount=Sum('tax_amount'),
                 expenses_amount=Sum('expenses_amount')).distinct()\
        .order_by('year')
    for d in turnover_year:
        cost = models.ProjectRequestDetail.objects.filter(project_request__year=d['year']).aggregate(Sum('cost'))
        d['cost_amount'] = cost.get('cost__sum', 0)

    return turnover_year


def turnover_company_year2():
    """年単位の会社の売上情報を取得する。

    :return: QuerySet
    """
    turnover_year = models.ProjectRequest.objects.filter(projectrequestheading__isnull=False).\
        values('year',).distinct().order_by('year')
    for d in turnover_year:
        queryset = models.ProjectRequest.objects.annotate(ym=Concat('year', 'month')).filter(
            projectrequestheading__isnull=False,
            ym__gte='%s04' % d['year'],
            ym__lte='%s03' % (int(d['year']) + 1)
        ).distinct()
        d['amount__sum'] = queryset.aggregate(Sum('amount')).get('amount__sum', 0)
        d['turnover_amount'] = queryset.aggregate(Sum('turnover_amount')).get('turnover_amount__sum', 0)
        d['tax_amount'] = queryset.aggregate(Sum('tax_amount')).get('tax_amount__sum', 0)
        d['expenses_amount'] = queryset.aggregate(Sum('expenses_amount')).get('expenses_amount__sum', 0)
        cost = models.ProjectRequestDetail.objects.annotate(ym=Concat('project_request__year',
                                                                      'project_request__month')).filter(
            ym__gte='%s04' % d['year'],
            ym__lte='%s03' % (int(d['year']) + 1)
        ).aggregate(Sum('cost'))
        d['cost_amount'] = cost.get('cost__sum', 0)

    return turnover_year


def turnover_company_monthly():
    """月単位の会社の売上情報を取得する。

    :return: QuerySet
    """
    turnover_monthly = models.ProjectRequest.objects.filter(projectrequestheading__isnull=False).\
        values('year', 'month').\
        annotate(amount__sum=Sum('amount'),
                 turnover_amount=Sum('turnover_amount'),
                 tax_amount=Sum('tax_amount'),
                 expenses_amount=Sum('expenses_amount')).distinct()\
        .order_by('year', 'month')
    for d in turnover_monthly:
        d['ym'] = d['year'] + d['month']
        cost = models.ProjectRequestDetail.objects.filter(project_request__year=d['year'],
                                                          project_request__month=d['month']).aggregate(Sum('cost'))
        d['cost_amount'] = cost.get('cost__sum', 0)

    return turnover_monthly


def get_turnover_sections(ym):
    """全ての部署を取得する

    メンバー売上画面にて、絞り込み条件の部署のドロップダウンに使う。
    """
    sections = models.Section.objects.public_filter(projectrequestdetail__project_request__year=ym[:4],
                                                    projectrequestdetail__project_request__month=ym[4:]).distinct()
    return sections


def sections_turnover_monthly(ym):
    """部署別の売上を取得する。
    /eb/turnover/charts/201907.html

    :param ym: 対象年月
    :return:
    """
    turnover_details = models.ProjectRequestDetail.objects.filter(project_request__year=ym[:4],
                                                                  project_request__month=ym[4:]).\
        values('member_section').annotate(cost_amount=Sum('cost'),
                                          attendance_amount=Sum('total_price'),
                                          expenses_amount=Sum('expenses_price')).order_by('member_section').distinct()
    sections_turnover = []
    for turnover_detail in turnover_details:
        d = dict()
        d['section'] = models.Section.objects.get(pk=turnover_detail['member_section'])
        d['cost_amount'] = turnover_detail['cost_amount']
        d['attendance_amount'] = turnover_detail['attendance_amount']
        d['attendance_tex'] = int(d['attendance_amount'] * 0.08)
        d['expenses_amount'] = turnover_detail['expenses_amount']
        d['all_amount'] = d['attendance_amount'] + d['attendance_tex'] + d['expenses_amount']
        sections_turnover.append(d)
    return sections_turnover


def salesperson_turnover_monthly(ym):
    """営業員別の売上を取得する。
    /eb/turnover/charts/201907.html

    :param ym: 対象年月
    :return:
    """
    turnover_details = models.ProjectRequestDetail.objects.filter(project_request__year=ym[:4],
                                                                  project_request__month=ym[4:]).\
        values('salesperson').annotate(cost_amount=Sum('cost'),
                                       attendance_amount=Sum('total_price'),
                                       expenses_amount=Sum('expenses_price')).\
        order_by('salesperson').distinct()
    salesperson_turnover = []
    for turnover_detail in turnover_details:
        d = dict()
        try:
            salesperson = models.Salesperson.objects.get(pk=turnover_detail['salesperson'])
        except ObjectDoesNotExist:
            salesperson = None
        d['salesperson'] = salesperson
        d['cost_amount'] = turnover_detail['cost_amount']
        d['attendance_amount'] = turnover_detail['attendance_amount']
        d['attendance_tex'] = int(d['attendance_amount'] * 0.08)
        d['expenses_amount'] = turnover_detail['expenses_amount']
        d['all_amount'] = d['attendance_amount'] + d['attendance_tex'] + d['expenses_amount']
        salesperson_turnover.append(d)
    return salesperson_turnover


def clients_turnover_yearly(year, data_type=1):
    """お客様別の年間売上を取得する。

    :param year: 対象年
    :param data_type: 1の場合はxx年01月～xx年12月、2の場合はxx年04月～xx年03月
    :return:
    """
    if data_type == 1:
        ym_start = '%s01' % year
        ym_end = '%s12' % year
    else:
        ym_start = '%s04' % year
        ym_end = '%s03' % (int(year) + 1)

    turnover_details = models.ProjectRequest.objects.order_by().annotate(ym=Concat('year', 'month')).filter(
        ym__gte=ym_start,
        ym__lte=ym_end,
        projectrequestheading__client__isnull=False,
        projectrequestheading__isnull=False
    ).values('projectrequestheading__client').annotate(
        attendance_amount=Sum('turnover_amount'),
        tax_amount=Sum('tax_amount'),
        expenses_amount=Sum('expenses_amount'),
        all_amount=Sum('amount')
    ).order_by('projectrequestheading__client').distinct()
    clients_turnover = []
    for turnover_detail in turnover_details:
        d = dict()
        d['client'] = models.Client.objects.get(pk=turnover_detail['projectrequestheading__client'])
        d['attendance_amount'] = turnover_detail['attendance_amount']
        d['attendance_tex'] = turnover_detail['tax_amount']
        d['expenses_amount'] = turnover_detail['expenses_amount']
        d['all_amount'] = turnover_detail['all_amount']
        clients_turnover.append(d)
    return clients_turnover


def clients_turnover_yearly_area_plot(year, data_type=1):
    if data_type == 1:
        ym_start = '%s01' % year
        ym_end = '%s12' % year
    else:
        ym_start = '%s04' % year
        ym_end = '%s03' % (int(year) + 1)

    queryset = models.ProjectRequest.objects.order_by().annotate(ym=Concat('year', 'month')).filter(
        ym__gte=ym_start,
        ym__lte=ym_end,
        projectrequestheading__client__isnull=False,
        projectrequestheading__isnull=False
    ).values(
        'projectrequestheading__client__pk',
        'projectrequestheading__client__name',
        'year',
        'month',
    ).annotate(
        turnover_amount=Sum('turnover_amount'),
    ).order_by('projectrequestheading__client__name', 'year', 'month').distinct()

    df = pd.DataFrame(list(queryset))
    new_df = pd.DataFrame([], index=df.groupby(['year', 'month']).sum().index)
    for name in df.projectrequestheading__client__name.unique():
        new_df[name] = df[df.projectrequestheading__client__name == name].set_index(['year',
                                                                                     'month'])['turnover_amount']
    new_df.index = pd.to_datetime(new_df.index.map(lambda x: datetime.date(int(x[0]), int(x[1]), 1)))

    ax = plt.subplot()
    df = new_df
    # 売上上位１０社を表示する
    other_df = df.loc[:, list(df.sum().sort_values(ascending=False).index[10:])]
    other_cnt = len(other_df.columns)
    other_sum = other_df.sum(axis=1)
    df = df.loc[:, list(df.sum().sort_values(ascending=False).index[:10])]
    df['その他%d社' % other_cnt] = other_sum
    df.plot.area(ax=ax, figsize=(12, 5))

    def y_ax_format(y, p):
        if y >= 1000000:
            return '%0dM円' % (y / 1000000)
        elif y >= 1000:
            return '%0dK円' % (y / 1000)
        elif y == 0:
            return '0円'
        else:
            return y
    ax.get_yaxis().set_major_formatter(FuncFormatter(y_ax_format))
    ax.grid(alpha=0.3)
    if data_type == 1:
        ax.set_title("%s年%02d月～%s年%02d月お客様別の売上（税抜）情報" % (year, 1, year, 12))
    else:
        ax.set_title("%s年%02d月～%s年%02d月お客様別の売上（税抜）情報" % (year, 4, int(year) + 1, 3))
    img_data = StringIO.StringIO()
    handles, labels = ax.get_legend_handles_labels()
    lgd = ax.legend(handles, labels, loc='upper center', bbox_to_anchor=(0.5, -0.1), ncol=3)
    plt.savefig(img_data, format='png', bbox_extra_artists=(lgd,), bbox_inches='tight')
    img_data.seek(0)
    plt.close()
    return img_data


def client_turnover_monthly(client):
    df = pd.read_sql("select r.year"
                     "     , r.month"
                     "     , r.amount"
                     "     , r.expenses_amount"
                     "     , r.tax_amount"
                     "     , r.turnover_amount"
                     "     , (select count(1) "
                     "          from eb_projectmember pm2 "
                     "		 where pm2.id in (select project_member_id "
                     "                            from eb_projectrequestdetail d "
                     "						   where d.project_request_id=r.id)"
                     "	   ) as member_count"
                     "  from eb_projectrequest r "
                     "  join eb_projectrequestheading h on r.id = h.project_request_id"
                     "  join eb_project p on p.id = r.project_id"
                     " where h.client_id = %s" % client.pk, connection)
    grouped = df.groupby(['year', 'month'])
    sum_df = grouped.sum()
    fig, axes = plt.subplots(nrows=2, ncols=1, figsize=(11, 5))
    turnover_df = pd.DataFrame(sum_df, columns=['turnover_amount', 'tax_amount', 'expenses_amount'])
    turnover_df.rename(columns={'turnover_amount': '売上（税抜）', 'tax_amount': '税金', 'expenses_amount': '精算'}, inplace=True)
    turnover_df.plot(ax=axes[0], kind='bar', stacked=True)
    sum_df['member_count'].plot(ax=axes[1], kind='bar')

    def x_ax_format(x, p):
        index = turnover_df.index.values[x]
        return '%s/%s' % (index[0][2:], index[1])

    def y_ax_format(y, p):
        if y >= 1000000:
            return '%0dM円' % (y / 1000000)
        elif y >= 1000:
            return '%0dK円' % (y / 1000)
        elif y == 0:
            return '0円'
        else:
            return y
    axes[0].set_xlabel('売上')
    axes[0].grid(alpha=0.3)
    axes[0].get_xaxis().set_major_formatter(FuncFormatter(x_ax_format))
    axes[0].get_yaxis().set_major_formatter(FuncFormatter(y_ax_format))
    axes[1].set_xlabel('人数')
    axes[1].grid(alpha=0.3)
    axes[1].get_xaxis().set_major_formatter(FuncFormatter(x_ax_format))
    axes[1].get_yaxis().set_major_formatter(FuncFormatter(lambda x, p: '%d人' % x))
    for ax in axes:
        for tick in ax.get_xticklabels():
            tick.set_rotation(0)

    for i, v in enumerate(sum_df['amount']):
        axes[0].text(i, v, '%sK' % (humanize.intcomma(int(round(v / 1000)))), color='black', fontsize=8,
                     horizontalalignment='center', va='bottom')
    for i, v in enumerate(sum_df['member_count']):
        axes[1].text(i, v, str(v), color='black', fontsize=8, horizontalalignment='center', va='bottom')

    plt.tight_layout()

    img_data = StringIO.StringIO()
    plt.savefig(img_data, format='png')
    img_data.seek(0)
    plt.close()
    return img_data


def clients_turnover_monthly(year, month):
    """営業員別の売上を取得する。

    :param year: 対象年月
    :param month:
    :return:
    """
    turnover_details = models.ProjectRequest.objects.order_by().filter(year=year,
                                                                       month=month,
                                                                       projectrequestheading__client__isnull=False). \
        values('projectrequestheading__client').annotate(attendance_amount=Sum('turnover_amount'),
                                                         tax_amount=Sum('tax_amount'),
                                                         expenses_amount=Sum('expenses_amount'),
                                                         all_amount=Sum('amount')).\
        order_by('projectrequestheading__client').distinct()
    clients_turnover = []
    for turnover_detail in turnover_details:
        d = dict()
        d['client'] = models.Client.objects.get(pk=turnover_detail['projectrequestheading__client'])
        d['attendance_amount'] = turnover_detail['attendance_amount']
        d['attendance_tex'] = turnover_detail['tax_amount']
        d['expenses_amount'] = turnover_detail['expenses_amount']
        d['all_amount'] = turnover_detail['all_amount']
        clients_turnover.append(d)
    return clients_turnover


def clients_turnover_monthly_pie_plot(year, month):
    """営業員別の売上を取得する。

    :param year: 対象年月
    :param month:
    :return:
    """
    queryset = models.ProjectRequest.objects.order_by().filter(
        year=year,
        month=month,
        projectrequestheading__client__isnull=False
    ).values('projectrequestheading__client').annotate(
        turnover_amount=Sum('turnover_amount'),
    ).order_by('projectrequestheading__client').distinct()
    df = pd.DataFrame(list(queryset.values('projectrequestheading__client__pk',
                                           'projectrequestheading__client__name',
                                           'turnover_amount')))
    # df.set_index('projectrequestheading__client__name')
    # percent = 100. * df.turnover_amount / df.turnover_amount.sum()
    # labels = [name if per >= 3 else '' for name, per in zip(df.projectrequestheading__client__name, percent)]
    ax = plt.subplot()
    series = pd.Series(list(df.turnover_amount), index=df.projectrequestheading__client__name, name='')
    series = series.sort_values(ascending=False)
    other_cnt = series.iloc[11:].count()
    other_sum = series.iloc[11:].sum()
    series = series.iloc[:11]
    series.set_value('その他%d社' % other_cnt, other_sum)
    series.plot.pie(ax=ax, labels=series.index, autopct='%.1f%%', pctdistance=0.8, figsize=(7, 4.5), startangle=60)
    ax.set_title("%s年%s月 お客様別売上（税抜）分配図" % (year, month))
    plt.tight_layout()

    img_data = StringIO.StringIO()
    plt.savefig(img_data, format='png', bbox_inches='tight')
    img_data.seek(0)
    plt.close()
    return img_data


def turnover_client_monthly(client_id, ym):
    """案件別の売上を取得する。

    :param client_id: お客様
    :param ym: 対象年月
    :return:
    """
    turnover_details = models.ProjectRequest.objects.order_by().filter(year=ym[:4],
                                                                       month=ym[4:],
                                                                       projectrequestheading__client__id=client_id). \
        values('project').annotate(attendance_amount=Sum('turnover_amount'),
                                   tax_amount=Sum('tax_amount'),
                                   expenses_amount=Sum('expenses_amount'),
                                   all_amount=Sum('amount'))
    for turnover_detail in turnover_details:
        turnover_detail['project'] = models.Project.objects.get(pk=turnover_detail['project'])
    return turnover_details


def members_turnover_monthly(ym, q=None, o=None):
    turnover_details = models.ProjectRequestDetail.objects.filter(project_request__year=ym[:4],
                                                                  project_request__month=ym[4:])
    if q:
        turnover_details = turnover_details.filter(**q)
    if o:
        turnover_details = turnover_details.order_by(*o)

    return turnover_details


def cost_subcontractors_monthly():
    queryset = models.MemberAttendance.objects.public_filter(
        project_member__member__subcontractor__isnull=False,
        year__gte='2017',
    ).values('year', 'month').annotate(
        total_hours=Sum('total_hours'),
        ym=Concat('year', 'month'),
        member_count=Count('id'),
    ).filter(
        Q(project_member__member__bpcontract__end_date__gte=Concat('year', Value('-'), 'month', Value('-01'))) |
        Q(project_member__member__bpcontract__end_date__isnull=True),
        project_member__member__bpcontract__start_date__lte=Concat('year', Value('-'), 'month', Value('-30')),
    ).order_by('year', 'month').distinct()
    return queryset


def cost_subcontractor_members_by_month(year, month):
    first_day = common.get_first_day_from_ym(year + month)
    last_day = common.get_last_day_by_month(first_day)
    queryset = models.MemberAttendance.objects.public_filter(
        Q(project_member__member__bpcontract__end_date__gte=first_day) |
        Q(project_member__member__bpcontract__end_date__isnull=True),
        project_member__member__bpcontract__start_date__lte=last_day,
        year=year,
        month=month,
    ).order_by('project_member__member__first_name', 'project_member__member__last_name').distinct()
    return queryset


def cost_subcontractors_by_month(year, month):
    first_day = common.get_first_day_from_ym(year + month)
    last_day = common.get_last_day_by_month(first_day)
    queryset = models.MemberAttendance.objects.public_filter(
        Q(project_member__member__bpcontract__end_date__gte=first_day) |
        Q(project_member__member__bpcontract__end_date__isnull=True),
        project_member__member__bpcontract__start_date__lte=last_day,
        year=year,
        month=month,
    ).order_by('project_member__member__subcontractor').distinct().prefetch_related(
        'project_member__member__subcontractor',
    )

    subcontractors = dict()
    for member_attendance in queryset:
        cost = member_attendance.get_all_cost()
        if member_attendance.project_member.member.subcontractor in subcontractors:
            subcontractors[member_attendance.project_member.member.subcontractor] += cost
        else:
            subcontractors[member_attendance.project_member.member.subcontractor] = cost
    return subcontractors.items()


def get_bp_members_cost(year, month, company_id=None, param_dict=None, order_list=None):
    """協力会社社員ごとのコスト明細

    :param year:
    :param month:
    :param company_id:
    :param param_dict:
    :param order_list:
    :return:
    """
    df = biz.get_cost_by_month(year, month, param_dict=param_dict, order_list=order_list)
    # 出向の契約を洗い出す
    loan_df = df[df.is_loan == 1]
    for index, row in loan_df.iterrows():
        related_row = df.loc[(df.projectmember_id == row.projectmember_id) & (df.is_loan == 0)]
        if related_row.empty:
            # 完全出向の場合は何もしない。
            continue
        # # ＥＢ契約の月給を再設定する。
        # df.set_value(index, 'salary', df.loc[index]['salary'] + related_row.iloc[0].salary)
        # ＢＰ契約に値を再設定する。
        df.set_value(related_row.index[0], 'is_loan', row.is_loan)
        # df.set_value(related_row.index[0], 'salary', df.loc[index]['salary'] + related_row.iloc[0].salary)
        # df.set_value(related_row.index[0], 'allowance', df.loc[index]['allowance'] + related_row.iloc[0].allowance)
        # df.set_value(related_row.index[0], 'night_allowance', df.loc[index]['night_allowance'] + related_row.iloc[0].night_allowance)
        # df.set_value(related_row.index[0], 'expenses', df.loc[index]['expenses'] + related_row.iloc[0].expenses)
        df.set_value(related_row.index[0], 'employment_insurance', df.loc[index]['employment_insurance'] + related_row.iloc[0].employment_insurance)
        df.set_value(related_row.index[0], 'health_insurance', df.loc[index]['health_insurance'] + related_row.iloc[0].health_insurance)
        # ＥＢの出向契約は非表示
        df = df.iloc[df.index!=index]
    df = df.loc[df.member_type==4]
    if company_id:
        df = df.loc[df.company_id==int(company_id)]
    return df


def get_bp_cost_by_subcontractor(year, month):
    """協力会社ごとのコスト合計

    :param year:
    :param month:
    :return:
    """

    def get_org(c):
        if pd.isnull(c['division_id']):
            return c['section_id']
        else:
            return c['division_id']

    df = get_bp_members_cost(year, month)
    # 協力会社の関連部署数取得する。
    df['organization_count'] = df.apply(get_org, axis=1)
    df_org_count = df.groupby(['company_id']).organization_count.nunique().to_frame().reset_index()
    # 協力会社ごとにグループする。
    s = df.groupby(['company_id', 'company_name'])['total_cost'].sum()
    df = pd.DataFrame(s.values, index=s.index, columns=['total_cost'])
    df.reset_index(inplace=True)
    df.company_id = df.company_id.astype(int)
    df = pd.merge(df, df_org_count, how='left', on = ['company_id'])
    # 請求数
    df_request_count = get_subcontractor_request_count(year, month)
    df = pd.merge(df, df_request_count, how='left', on = ['company_id'])
    df.requested_count = df.requested_count.fillna(0).astype(int)
    df.is_sent = df.is_sent.fillna(0).astype(int)
    # 請求書作成作成済みフラグ
    df['is_requested'] = np.where(df.organization_count == df.requested_count, 1, 0)
    return df


def get_subcontractor_request_count(year, month):
    df = pd.read_sql("select subcontractor_id as company_id, count(1) as requested_count, max(is_sent) as is_sent "
                     "  from eb_subcontractorrequest where year = %s and month = %s "
                     " group by subcontractor_id" % (year, month), connection)
    df.requested_count.astype(int)
    df.is_sent.astype(int)
    return df


def get_members_turnover(year, month, param_dict=None, order_list=None):
    """指定年月の請求売上を取得する。

    :param year:
    :param month:
    :param param_dict:
    :param order_list:
    :return:
    """
    days = common.get_business_days(year, month)
    df = pd.read_sql("call sp_organization_turnover('%s%s', %s)" % (year, month, len(days)), connection)
    # 出向の契約を洗い出す
    loan_df = df[df.is_loan == 1]
    for index, row in loan_df.iterrows():
        related_row = df.loc[(df.projectmember_id == row.projectmember_id) & (df.is_loan == 0)]
        if related_row.empty:
            # 完全出向の場合は何もしない。
            continue
        # # ＥＢ契約の月給を再設定する。
        # df.set_value(index, 'salary', df.loc[index]['salary'] + related_row.iloc[0].salary)
        # ＢＰ契約に値を再設定する。
        df.set_value(related_row.index[0], 'is_loan', row.is_loan)
        df.set_value(related_row.index[0], 'salary', df.loc[index]['salary'] + related_row.iloc[0].salary)
        df.set_value(related_row.index[0], 'allowance', df.loc[index]['allowance'] + related_row.iloc[0].allowance)
        df.set_value(related_row.index[0], 'night_allowance', df.loc[index]['night_allowance'] + related_row.iloc[0].night_allowance)
        df.set_value(related_row.index[0], 'expenses', df.loc[index]['expenses'] + related_row.iloc[0].expenses)
        df.set_value(related_row.index[0], 'employment_insurance', df.loc[index]['employment_insurance'] + related_row.iloc[0].employment_insurance)
        df.set_value(related_row.index[0], 'health_insurance', df.loc[index]['health_insurance'] + related_row.iloc[0].health_insurance)
        # ＥＢの出向契約は非表示
        df = df.iloc[df.index!=index]
    # 重複した請求情報を削除
    df = df.drop_duplicates(subset=['projectrequestdetail_id', 'projectrequest_id'])

    # 原価合計を計算する。
    df['total_cost'] = df['salary'] + df['allowance'] + df['night_allowance'] + df['overtime_cost'] + df[
        'traffic_cost'] + df['expenses'] + df['employment_insurance'] + df['health_insurance']
    # 利益
    df['profit'] = df['total_price'] - df['total_cost']
    df['profit_rate'] = df['profit'] / df['total_price'] * 100
    # 税込
    df['all_price'] = df['total_price'] + df['expenses_price'] + df['tax_price']
    if param_dict and isinstance(param_dict, dict):
        for k, v in param_dict.items():
            if k == 'organization_id':
                organization = models.Section.objects.get(pk=v)
                org_pk_list = common.get_organization_children(organization)
                df = df[(df.division_id.isin(org_pk_list)) | (df.section_id.isin(org_pk_list)) | (
                df.subsection_id.isin(org_pk_list))]
            elif k.endswith('_id'):
                df = df[df[k] == int(v)]
            else:
                df = df[df[k].str.contains(v, na=False)]
    if order_list:
        name = order_list[0].strip('-')
        ascending = not order_list[0].startswith('-')
        df = df.sort_values(by=name, ascending=ascending)
    return df


def get_clients_turnover(year, month):
    df = get_members_turnover(year, month)
    df = df.groupby(['client_id', 'client_name']).sum()
    df.reset_index(inplace=True)
    df['profit_rate'] = df['profit'] / df['total_price'] * 100
    df['per'] = df.total_price / df.total_price.max() * 100
    df = df.sort_values(by='client_name', ascending=True)
    return df


def get_client_turnover(year, month, client):
    df = get_members_turnover(year, month)
    df = df.loc[df.client_id == client.pk]
    df = df.groupby(['project_id', 'project_name']).sum()
    df.reset_index(inplace=True)
    df['profit_rate'] = df['profit'] / df['total_price'] * 100
    df = df.sort_values(by='project_name', ascending=True)
    return df


def get_business_owner_cost(year, month): #, param_dict=None
    # df = biz.get_cost_by_month(year, month, param_dict)
    # return df
    pd.read_sql("SELECT @get_ym:=%s%s" % (year, month), connection)
    df = pd.read_sql('''
        SELECT * FROM v_organization_cost s
        WHERE s.member_type = '3'
        order by s.is_lump, s.employee_id
    ''', connection)
    
    # 原価合計を計算する。
    df['total_cost'] = df['salary'] + df['allowance'] + df['night_allowance'] + df['overtime_cost'] + df[
        'traffic_cost'] + df['expenses'] + df['employment_insurance'] + df['health_insurance']
    # 粗利
    df['profit'] = df['total_price'] - df['total_cost']
    # 経費合計
    df['expenses_total'] = df['expenses_conference'] + df['expenses_entertainment'] + df['expenses_travel'] + df[
        'expenses_communication'] + df['expenses_tax_dues'] + df['expenses_expendables']
    # 営業利益
    df['income'] = df['total_price'] - df['total_cost'] - df['expenses_total']
    df.project_id = df.project_id.fillna(0).astype(int)

    return df


def get_bundle_project(subcontractor_id, year, month):
    sql = '''
        SELECT 
            scrd.total_price,
            scrd.project_id,
            sc.name as sub_contractor_name,
            p.name as project_name
        FROM `eb_subcontractorrequestdetail` scrd
        LEFT JOIN `eb_subcontractorrequest` scr on scrd.`subcontractor_request_id` = scr.id
        LEFT JOIN `eb_subcontractor` sc on scr.subcontractor_id = sc.id
        LEFT JOIN `eb_project` p on scrd.project_id = p.id
        WHERE scr.`year` =%s
            AND scr.`month`=%s
            AND scr.`subcontractor_id`=%s
            AND scrd.`project_member_id` IS NULL
    '''
    df = pd.read_sql(sql % (year, month, subcontractor_id), connection)
    return df


def get_bp_order_manage_list(year, month):
    with connection.cursor() as cursor:
        cursor.callproc('sp_bp_order_manage_list', (year, month))
        results = common.dictfetchall(cursor)
    return results
