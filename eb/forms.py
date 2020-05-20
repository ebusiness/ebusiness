# coding: UTF-8
"""
Created on 2015/08/26

@author: Yang Wanjun
"""
import re
import models
import datetime
from itertools import chain

from django import forms
from django.forms.utils import flatatt
from django.forms.widgets import Widget
from django.utils.html import format_html, mark_safe
from django.core.exceptions import ObjectDoesNotExist
from django.core.urlresolvers import reverse
from django.utils.translation import ugettext_lazy as _
from django.utils.functional import cached_property

from utils import constants, common

REG_POST_CODE = r"^\d{7}$"
REG_UPPER_CAMEL = r"^([A-Z][a-z]+)+$"


class EncryptField(Widget):

    def __init__(self, attrs=None):
        super(EncryptField, self).__init__(attrs)

    def render(self, name, value, attrs=None, renderer=None):
        final_attrs = self.build_attrs(attrs)
        return format_html('<span{}>******</span>', flatatt(final_attrs))


class SearchSelect(forms.Select):
    def __init__(self, clsModel, attrs=None, choices=()):
        self.clsModel = clsModel
        super(SearchSelect, self).__init__(attrs, choices)

    def render(self, name, value, attrs=None, renderer=None):
        output = ['<div class="related-widget-wrapper">']
        html = super(SearchSelect, self).render(name, value, attrs, renderer)
        output.append(html)

        from django.contrib import admin
        related_url = reverse(
            'admin:%s_%s_changelist' % (
                self.clsModel._meta.app_label,
                self.clsModel._meta.model_name,
            ),
            current_app=admin.site.name,
        )
        output.append('<a href="%s%s" class="related-lookup selector search-label-icon" id="lookup_id_%s" title="%s">'
                      '</a>' %
                      (related_url, '?is_deleted__exact=0&is_retired__exact=0', name, _('Lookup')))
        output.append(u'<a class="related-widget-wrapper-link change-related" id="change_id_%s"'
                      u' data-href-template="/admin/eb/%s/__fk__/?_to_field=id&_popup=1" title="%s">'
                      u'  <img src="/static/admin/img/icon-changelink.svg" width="15" height="15" style="margin-top: -4px;" '
                      u'   alt="%s"/></a>' % (name, self.clsModel._meta.model_name, _("Change"), _("Change")))
        output.append('</div>')
        return mark_safe('\n'.join(output))


class CompanyForm(forms.ModelForm):
    class Meta:
        models = models.Company
        fields = '__all__'

    post_code = forms.CharField(max_length=7,
                                widget=forms.TextInput(
                                    attrs={'onKeyUp': "AjaxZip3.zip2addr(this,'','address1','address1');"}),
                                label=u"郵便番号",
                                required=False)

    def clean(self):
        cleaned_data = super(CompanyForm, self).clean()
        post_code = cleaned_data.get("post_code")
        if post_code and not re.match(REG_POST_CODE, post_code):
            self.add_error('post_code', u"正しい郵便番号を入力してください。")


class ClientForm(forms.ModelForm):
    class Meta:
        models = models.Company
        fields = '__all__'

    post_code = forms.CharField(max_length=7,
                                widget=forms.TextInput(
                                    attrs={'onKeyUp': "AjaxZip3.zip2addr(this,'','address1','address1');"}),
                                label=u"郵便番号",
                                required=False)

    def clean(self):
        cleaned_data = super(ClientForm, self).clean()
        post_code = cleaned_data.get("post_code")
        if post_code and not re.match(REG_POST_CODE, post_code):
            self.add_error('post_code', u"正しい郵便番号を入力してください。")


class SubcontractorForm(forms.ModelForm):
    class Meta:
        models = models.Subcontractor
        fields = '__all__'

    post_code = forms.CharField(max_length=7,
                                widget=forms.TextInput(
                                    attrs={'onKeyUp': "AjaxZip3.zip2addr(this,'','address1','address1');"}),
                                label=u"郵便番号",
                                required=False)

    def clean(self):
        cleaned_data = super(SubcontractorForm, self).clean()
        post_code = cleaned_data.get("post_code")
        if post_code and not re.match(REG_POST_CODE, post_code):
            self.add_error('post_code', u"正しい郵便番号を入力してください。")


class SectionForm(forms.ModelForm):

    class Meta:
        model = models.Section
        fields = '__all__'


class PositionShipForm(forms.ModelForm):
    class Meta:
        model = models.PositionShip
        fields = '__all__'

    member = forms.ModelChoiceField(queryset=models.Member.objects.public_all(),
                                    widget=SearchSelect(models.Member),
                                    label=u"名前")


class ProjectForm(forms.ModelForm):
    class Meta:
        models = models.Project
        fields = '__all__'

    def clean(self):
        cleaned_data = super(ProjectForm, self).clean()
        is_lump = cleaned_data.get("is_lump")
        lump_amount = cleaned_data.get("lump_amount")
        status = cleaned_data.get('status')
        is_reserve = cleaned_data.get('is_reserve')
        department = cleaned_data.get('department')
        if is_reserve and not department:
            self.add_error('department', u"待機案件フラグを設定したら、所属部署も設定する必要があります。")
        if is_reserve and department and not self.instance.pk:
            # 追加の場合
            if models.Project.objects.public_filter(is_reserve=True, department=department).count() > 0:
                self.add_error('is_reserve', u"当該部署の待機案件はすでに作成済みです。")
        if is_lump:
            if not lump_amount or lump_amount <= 0:
                self.add_error('lump_amount', u"一括の場合、一括金額を入力してください。")
        if status == 5 and not self.instance.can_end_project():
            self.add_error('status', u"案件終了できません、まだ作業中のメンバーがいます。")

    def _save_m2m(self):
        cleaned_data = self.cleaned_data
        exclude = self._meta.exclude
        fields = self._meta.fields
        opts = self.instance._meta
        # Note that for historical reasons we want to include also
        # private_fields here. (GenericRelation was previously a fake
        # m2m field).
        for f in chain(opts.many_to_many, opts.private_fields):
            if not hasattr(f, 'save_form_data'):
                continue
            if fields and f.name not in fields:
                continue
            if exclude and f.name in exclude:
                continue
            if f.name in cleaned_data:
                f.save_form_data(self.instance, cleaned_data[f.name])


class MemberForm(forms.ModelForm):
    class Meta:
        model = models.Member
        fields = '__all__'

    post_code = forms.CharField(max_length=7,
                                widget=forms.TextInput(
                                    attrs={'onKeyUp': "AjaxZip3.zip2addr(this,'','address1','address1');"}),
                                label=u"郵便番号",
                                required=False)

    def clean(self):
        cleaned_data = super(MemberForm, self).clean()
        member_type = cleaned_data.get("member_type")
        company = cleaned_data.get("company")
        subcontractor = cleaned_data.get("subcontractor")
        post_code = cleaned_data.get("post_code")
        first_name_en = cleaned_data.get("first_name_en")
        last_name_en = cleaned_data.get("last_name_en")
        # email = cleaned_data.get("email")
        # private_email = cleaned_data.get("private_email")
        # notify_type = cleaned_data.get("notify_type")
        # is_on_sales = cleaned_data.get("is_on_sales")
        # sales_off_reason = cleaned_data.get("sales_off_reason")
        is_retired = cleaned_data.get("is_retired")
        retired_date = cleaned_data.get("retired_date")
        today = datetime.date.today()

        if post_code and not re.match(REG_POST_CODE, post_code):
            self.add_error('post_code', u"正しい郵便番号を入力してください。")
        if member_type == 4:
            # 派遣社員の場合
            if not subcontractor:
                self.add_error('subcontractor', u"派遣社員の場合、協力会社を選択してください。")
        else:
            if not company:
                self.add_error('company', u"派遣社員以外の場合、会社を選択してください。")

        # ローマ名のチェック
        # if first_name_en and not re.match(REG_UPPER_CAMEL, first_name_en):
        #     self.add_error('first_name_en', u"先頭文字は大文字にしてください（例：Zhang）")
        # if last_name_en and not re.match(REG_UPPER_CAMEL, last_name_en):
        #     self.add_error('last_name_en', u"漢字ごとに先頭文字は大文字にしてください（例：XiaoWang）")

        if company and subcontractor:
            self.add_error('company', u"会社と協力会社が同時に選択されてはいけません。")
            self.add_error('subcontractor', u"会社と協力会社が同時に選択されてはいけません。")

        # if notify_type == 1 and not email:
        #     self.add_error('notify_type', u"メールアドレスを追加してください。")
        # elif notify_type == 2 and not private_email:
        #     self.add_error('notify_type', u"個人メールアドレスを追加してください。")
        # elif notify_type == 3 and (not email or not private_email):
        #     self.add_error('notify_type', u"メールアドレス及び個人メールアドレスを追加してください。")

        # if is_on_sales:
        #     if sales_off_reason:
        #         self.add_error('sales_off_reason', u"営業対象の場合、理由は選択しないでください！")
        # else:
        #     if sales_off_reason is None:
        #         self.add_error('sales_off_reason', u"営業対象外の場合、営業対象外理由は選択してください！")
        if is_retired:
            # 案件アサインの終了日をチェックする、終了日はまだ来てない場合は退職が設定できない。
            if self.instance.projectmember_set.filter(is_deleted=False, end_date__gt=today).count() > 0:
                self.add_error('is_retired', u"まだ終了してない案件が存在しているので、退職は設定できません！")
            if retired_date is None:
                self.add_error('retired_date', u"退職した場合、退職年月日を入力してください！")


class SalespersonForm(forms.ModelForm):
    class Meta:
        model = models.Salesperson
        fields = '__all__'

    post_code = forms.CharField(max_length=7,
                                widget=forms.TextInput(
                                    attrs={'onKeyUp': "AjaxZip3.zip2addr(this,'','address1','address1');"}),
                                label=u"郵便番号",
                                required=False)

    def clean(self):
        cleaned_data = super(SalespersonForm, self).clean()
        post_code = cleaned_data.get("post_code")
        first_name_en = cleaned_data.get("first_name_en")
        last_name_en = cleaned_data.get("last_name_en")
        # email = cleaned_data.get("email")
        # private_email = cleaned_data.get("private_email")
        # notify_type = cleaned_data.get("notify_type")
        is_retired = cleaned_data.get("is_retired")
        retired_date = cleaned_data.get("retired_date")
        if post_code and not re.match(REG_POST_CODE, post_code):
            self.add_error('post_code', u"正しい郵便番号を入力してください。")
        # ローマ名のチェック
        if first_name_en and not re.match(REG_UPPER_CAMEL, first_name_en):
            self.add_error('first_name_en', u"先頭文字は大文字にしてください（例：Zhang）")
        if last_name_en and not re.match(REG_UPPER_CAMEL, last_name_en):
            self.add_error('last_name_en', u"漢字ごとに先頭文字は大文字にしてください（例：XiaoWang）")

        # if notify_type == 1 and not email:
        #     self.add_error('notify_type', u"メールアドレスを追加してください。")
        # elif notify_type == 2 and not private_email:
        #     self.add_error('notify_type', u"個人メールアドレスを追加してください。")
        # elif notify_type == 3 and (not email or not private_email):
        #     self.add_error('notify_type', u"メールアドレス及び個人メールアドレスを追加してください。")
        if is_retired:
            if retired_date is None:
                self.add_error('retired_date', u"退職した場合、退職年月日を入力してください！")


class ProjectMemberForm(forms.ModelForm):
    class Meta:
        model = models.ProjectMember
        fields = '__all__'
        exclude = ['stages']

    def __init__(self, *args, **kwargs):
        self.request = kwargs.pop('request', None)
        self.encrypt_fields = ('price', 'min_hours', 'max_hours', 'plus_per_hour', 'minus_per_hour')
        self.is_encrypted = False
        super(ProjectMemberForm, self).__init__(*args, **kwargs)
        instance = kwargs.get('instance', None)
        if instance and isinstance(instance, models.ProjectMember):
            if instance.end_date < datetime.date.today():
                old_class = self.fields['end_date'].widget.attrs.get('class')
                new_class = (old_class + ' finished') if old_class else 'finished'
                self.fields['end_date'].widget.attrs.update({'class': new_class})
            if instance.status == constants.CHOICE_PROJECT_MEMBER_STATUS[0][0]:
                old_class = self.fields['status'].widget.attrs.get('class')
                new_class = (old_class + ' planning') if old_class else 'planning'
                self.fields['status'].widget.attrs.update({'class': new_class})
            if self.request and not instance.member.is_belong_to(self.request.user, datetime.date.today()):
                for name in self.encrypt_fields:
                    self.fields[name].widget = EncryptField()
                    self.fields[name].required = False
                self.is_encrypted = True
        self.fields['start_date'].widget.attrs.update({'style': 'width: 72px; min-width: 72px;'})
        self.fields['end_date'].widget.attrs.update({'style': 'width: 72px; min-width: 72px;'})
        if 'price' in self.fields:
            self.fields['price'].widget.attrs.update({
                'style': 'width: 70px;',
                'type': 'number',
                'onchange': "calc_plus_minus(this)"
            })
        if 'min_hours' in self.fields:
            self.fields['min_hours'].widget.attrs.update({
                'style': 'width: 60px;',
                'type': 'number',
                'onchange': "calc_minus_from_min_hour(this)"
            })
        if 'max_hours' in self.fields:
            self.fields['max_hours'].widget.attrs.update({
                'style': 'width: 60px;',
                'type': 'number',
                'onchange': "calc_plus_from_max_hour(this)"
            })
        if 'plus_per_hour' in self.fields:
            self.fields['plus_per_hour'].widget.attrs.update({'style': 'width: 50px;', 'type': 'number'})
        if 'minus_per_hour' in self.fields:
            self.fields['minus_per_hour'].widget.attrs.update({'style': 'width: 50px;', 'type': 'number'})
        self.fields['role'].widget.attrs.update({'style': 'width: 72px; min-width: 72px;'})

    @cached_property
    def changed_data(self):
        data = super(ProjectMemberForm, self).changed_data
        if self.is_encrypted:
            for name in self.encrypt_fields:
                if name in data:
                    data.remove(name)
        return data

    def clean(self):
        cleaned_data = super(ProjectMemberForm, self).clean()
        contract_type = cleaned_data.get('contract_type', None)
        end_date = cleaned_data.get('end_date', None)
        today = datetime.date.today()
        if not contract_type and today <= end_date:
            self.add_error('contract_type', u"契約形態を入力してください！")
        return cleaned_data

    member = forms.ModelChoiceField(queryset=models.Member.objects.public_all(),
                                    widget=SearchSelect(models.Member),
                                    label=u"名前")

    def save(self, commit=True):
        if self.instance.pk:
            is_add = False
        else:
            is_add = True
        project_member = super(ProjectMemberForm, self).save(commit)
        if is_add:
            # 案件メンバーを追加
            pass
        return project_member


class ProjectMemberFormset(forms.BaseInlineFormSet):

    def __init__(self, data=None, files=None, instance=None,
                 save_as_new=False, prefix=None, queryset=None, **kwargs):
        self.request = kwargs.pop('request', None)
        super(ProjectMemberFormset, self).__init__(data, files, instance, save_as_new, prefix, queryset, **kwargs)

    def _construct_form(self, i, **kwargs):
        kwargs.update({'request': self.request})
        form = super(ProjectMemberFormset, self)._construct_form(i, **kwargs)
        return form

    def clean(self):
        count = 0
        project_members = []
        for form in self.forms:
            try:
                if form.cleaned_data:
                    member = form.cleaned_data.get("member")
                    start_date = form.cleaned_data.get("start_date")
                    end_date = form.cleaned_data.get("end_date")
                    project_members.append((member, start_date, end_date))
                    count += 1
            except AttributeError:
                pass
        for member, start_date, end_date in project_members:
            dates = [(s, e) for m, s, e in project_members if m.pk == member.pk]
            if len(dates) > 1:
                for i, period in enumerate(dates):
                    start_date, end_date = period
                    if common.is_cross_date(dates, start_date, i):
                        raise forms.ValidationError(u"メンバー%sの開始日が重複している。" % (member.__unicode__(),))
                    if end_date and common.is_cross_date(dates, end_date, i):
                        raise forms.ValidationError(u"メンバー%sの終了日が重複している。" % (member.__unicode__(),))

    def save(self, commit=True):
        objs = super(ProjectMemberFormset, self).save(commit)
        if self.new_objects:
            try:
                project = self.new_objects[0].project
                project_members = []
                for pm in self.new_objects:
                    member = pm.member
                    company = member.get_company()
                    project_members.append({
                        'name': unicode(pm),
                        'company': company.name if company else '',
                        'start_date': pm.start_date,
                        'end_date': pm.end_date,
                    })
                group = models.MailGroup.objects.get(name=constants.MAIL_PROJECT_MEMBER_ADD)
                group.send_mail(project=project.name, project_members=project_members)
            except ObjectDoesNotExist:
                pass
            except Exception as ex:
                print ex
        return objs


# class ProjectMemberPriceForm(forms.ModelForm):
#     class Meta:
#         model = models.ProjectMemberPrice
#         fields = '__all__'
#
#     def __init__(self, *args, **kwargs):
#         self.request = kwargs.pop('request', None)
#         self.encrypt_fields = ('price', 'min_hours', 'max_hours', 'plus_per_hour', 'minus_per_hour')
#         self.is_encrypted = False
#         super(ProjectMemberPriceForm, self).__init__(*args, **kwargs)
#
#         self.fields['min_hours'].widget.attrs.update({'style': 'width: 60px;'})
#         self.fields['max_hours'].widget.attrs.update({'style': 'width: 60px;'})


class MemberAttendanceForm(forms.ModelForm):
    class Meta:
        model = models.MemberAttendance
        exclude = ('expenses_conference', 'expenses_entertainment', 'expenses_travel', 'expenses_communication', 'expenses_tax_dues', 'expenses_expendables')

    rate = forms.DecimalField(max_digits=5, decimal_places=2, initial=1,
                              widget=forms.TextInput(attrs={'style': 'width: 70px;',
                                                            'type': 'number',
                                                            'step': 0.1}),
                              label=u"率")
    total_hours = forms.DecimalField(max_digits=5, decimal_places=2,
                                     widget=forms.TextInput(
                                         attrs={'onblur': "calc_extra_hours(this)",
                                                'type': 'number',
                                                'style': 'width: 70px;',
                                                'step': 0.25}),
                                     label=u"合計時間",
                                     required=True)
    total_hours_bp = forms.DecimalField(max_digits=5, decimal_places=2,
                                        widget=forms.TextInput(
                                            attrs={'type': 'number',
                                                   'style': 'width: 70px;',
                                                   'step': 0.25}),
                                        label=u"ＢＰ作業時間",
                                        required=False)
    extra_hours = forms.DecimalField(max_digits=5, decimal_places=2, initial=0,
                                     widget=forms.TextInput(
                                         attrs={'type': 'number',
                                                'style': 'width: 70px;',
                                                'step': 0.25}),
                                     label=u"残業時間",
                                     required=True)
    carryover_hours = forms.DecimalField(max_digits=5, decimal_places=2, initial=0,
                                         widget=forms.TextInput(
                                             attrs={'type': 'number',
                                                    'style': 'width: 70px;',
                                                    'step': 0.25}),
                                         label=u"繰越時間",
                                         required=True)
    price = forms.IntegerField(initial=0,
                               widget=forms.TextInput(attrs={'style': 'width: 80px;',
                                                             'type': 'number'}),
                               label=u"価格")

    def clean(self):
        cleaned_data = super(MemberAttendanceForm, self).clean()
        project_member = cleaned_data.get("project_member")
        year = cleaned_data.get("year")
        month = cleaned_data.get("month")
        if not month:
            self.add_error('month', u"入力してください！")
        else:
            if project_member.start_date:
                if str(project_member.start_date.year) + "%02d" % (project_member.start_date.month,) > year + month:
                    self.add_error('year', u"対象年月は案件開始日以前になっています！")
                    self.add_error('month', u"対象年月は案件開始日以前になっています！")
            if project_member.end_date:
                if str(project_member.end_date.year) + "%02d" % (project_member.end_date.month,) < year + month:
                    self.add_error('year', u"対象年月は案件終了日以降になっています！")
                    self.add_error('month', u"対象年月は案件終了日以降になっています！")


class UploadFileForm(forms.Form):
    file = forms.FileField()


class MemberAttendanceFormSet(forms.ModelForm):
    class Meta:
        model = models.MemberAttendance
        exclude = ('expenses_conference', 'expenses_entertainment', 'expenses_travel', 'expenses_communication', 'expenses_tax_dues', 'expenses_expendables')

    def __init__(self, *args, **kwargs):
        forms.ModelForm.__init__(self, *args, **kwargs)
        data = kwargs.get('initial', None)
        if data and isinstance(data, dict):
            pm = data.get('project_member', None)
            self.fields['project_member'].queryset = models.ProjectMember.objects.filter(pk=pm.pk)

    basic_price = forms.CharField(widget=forms.TextInput(attrs={'style': 'width: 50px; border: 0px;'
                                                                         'background-color: transparent;',
                                                                'readonly': 'readonly'}),
                                  required=False, label=u"単価")
    max_hours = forms.CharField(widget=forms.TextInput(attrs={'style': 'width: 45px; border: 0px;'
                                                                       'background-color: transparent;',
                                                              'readonly': 'readonly'}),
                                required=False, label=u"最大")
    min_hours = forms.CharField(widget=forms.TextInput(attrs={'style': 'width: 45px; border: 0px;'
                                                                       'background-color: transparent;',
                                                              'readonly': 'readonly'}),
                                required=False, label=u"最小")
    rate = forms.DecimalField(max_digits=5, decimal_places=2, initial=1,
                              widget=forms.TextInput(attrs={'style': 'width: 40px;',
                                                            'type': 'number',
                                                            'step': 0.1}),
                              label=u"率")
    total_hours = forms.DecimalField(max_digits=5, decimal_places=2,
                                     widget=forms.TextInput(
                                         attrs={'onblur': "calc_extra_hours_portal(this)",
                                                'type': 'number',
                                                'style': 'width: 60px;',
                                                'step': 0.25}),
                                     label=u"合計時間",
                                     required=True)
    total_hours_bp = forms.DecimalField(max_digits=5, decimal_places=2,
                                        widget=forms.TextInput(
                                            attrs={'type': 'number',
                                                   'style': 'width: 70px;',
                                                   'step': 0.25}),
                                        label=u"ＢＰ作業時間",
                                        required=False)
    extra_hours = forms.DecimalField(max_digits=5, decimal_places=2, initial=0,
                                     widget=forms.TextInput(
                                         attrs={'type': 'text',
                                                'style': 'width: 50px;',
                                                'step': 0.25}),
                                     label=u"残業時間",
                                     required=True)
    plus_per_hour = forms.IntegerField(widget=forms.TextInput(attrs={'onblur': "calc_price_for_plus_portal(this)",
                                                                     'style': 'width: 42px; '
                                                                              'background-color: transparent;'
                                                                              'border: 0px;',
                                                                     'readonly': 'readonly'}),
                                       label=u"増（円）")
    minus_per_hour = forms.IntegerField(widget=forms.TextInput(attrs={'onblur': "calc_price_for_minus_portal(this)",
                                                                      'style': 'width: 42px;'
                                                                               'background-color: transparent;'
                                                                               'border: 0px;',
                                                                      'readonly': 'readonly'}),
                                        label=u"減（円）")
    price = forms.IntegerField(initial=0,
                               widget=forms.TextInput(attrs={'style': 'width: 75px;',
                                                             'type': 'number'}),
                               label=u"価格")


class MemberAttendanceFormSetHourlyPay(forms.ModelForm):
    class Meta:
        model = models.MemberAttendance
        fields = ['project_member', 'year', 'month', 'total_hours', 'extra_hours', 'price', 'carryover_hours', 'comment']

    total_hours = forms.DecimalField(max_digits=5, decimal_places=2,
                                     widget=forms.TextInput(
                                         attrs={'onblur': "calc_hourly_pay(this)",
                                                'type': 'number',
                                                'style': 'width: 80px;',
                                                'text-align': 'right',
                                                'step': 0.25}),
                                     label=u"合計時間",
                                     required=True)
    total_hours_bp = forms.DecimalField(max_digits=5, decimal_places=2,
                                        widget=forms.TextInput(
                                            attrs={'type': 'number',
                                                   'style': 'width: 70px;',
                                                   'text-align': 'right',
                                                   'step': 0.25}),
                                        label=u"ＢＰ作業時間",
                                        required=False)
    extra_hours = forms.DecimalField(max_digits=5, decimal_places=2, initial=0,
                                     widget=forms.TextInput(
                                         attrs={'type': 'number',
                                                'style': 'width: 50px;border: 0px;background-color: transparent;',
                                                'readonly': 'readonly',
                                                'text-align': 'right',
                                                'step': 0.25},),
                                     label=u"残業時間",
                                     required=True)
    carryover_hours = forms.DecimalField(max_digits=5, decimal_places=2, initial=0,
                                         widget=forms.TextInput(
                                             attrs={'type': 'number',
                                                    'style': 'width: 55px;',
                                                    'text-align': 'right',
                                                    'step': 0.25}, ),
                                         label=u"繰越時間")
    price = forms.IntegerField(initial=0,
                               widget=forms.TextInput(attrs={'style': 'width: 75px;',
                                                             'text-align': 'right',
                                                             'type': 'number'}),
                               label=u"価格")
    hourly_pay = forms.IntegerField(initial=0,
                                    widget=forms.TextInput(attrs={'readonly': 'readonly',
                                                                  'style': 'width: 50px;'
                                                                           'background-color: transparent;'
                                                                           'border: 0px;',
                                                                           'text-align': 'right',
                                                                  }),
                                    label=u"時給",
                                    required=False)

    def __init__(self, *args, **kwargs):
        forms.ModelForm.__init__(self, *args, **kwargs)
        data = kwargs.get('initial', None)
        if data and isinstance(data, dict):
            pm = data.get('project_member', None)
            self.fields['project_member'].queryset = models.ProjectMember.objects.filter(pk=pm.pk)


class BpMemberOrderInfoForm(forms.ModelForm):
    class Meta:
        model = models.BpMemberOrderInfo
        fields = '__all__'


class BpMemberOrderInfoFormSet(forms.ModelForm):
    class Meta:
        model = models.BpMemberOrderInfo
        fields = '__all__'

    min_hours = forms.DecimalField(max_digits=5, decimal_places=2, initial=160,
                                   widget=forms.TextInput(attrs={'style': 'width: 60px;',
                                                                 'type': 'number'}),
                                   label=u"基準時間", required=True)
    max_hours = forms.DecimalField(max_digits=5, decimal_places=2, initial=180,
                                   widget=forms.TextInput(attrs={'style': 'width: 60px;',
                                                                 'type': 'number'}),
                                   label=u"最大時間", required=True)
    plus_per_hour = forms.IntegerField(widget=forms.TextInput(attrs={'style': 'width: 60px;',
                                                                     'type': 'number'}),
                                       label=u"増（円）")
    minus_per_hour = forms.IntegerField(widget=forms.TextInput(attrs={'style': 'width: 60px;',
                                                                      'type': 'number'}),
                                        label=u"減（円）")
    cost = forms.IntegerField(initial=0,
                              widget=forms.TextInput(attrs={'style': 'width: 70px;',
                                                            'type': 'number'}),
                              label=u"コスト")


class MemberSectionPeriodForm(forms.ModelForm):

    class Meta:
        model = models.MemberSectionPeriod
        fields = '__all__'

    def __init__(self, *args, **kwargs):
        forms.ModelForm.__init__(self, *args, **kwargs)
        instance = kwargs.get('instance', None)
        if instance and not instance.pk:
            self.fields['division'].queryset = models.Section.objects.public_filter(is_on_sales=True, org_type='01')
            self.fields['section'].queryset = models.Section.objects.public_filter(
                is_on_sales=True, org_type='02',
            )
            if instance.section:
                self.fields['subsection'].queryset = models.Section.objects.public_filter(
                    is_on_sales=True, org_type='03',
                    parent__pk=instance.section.pk
                )
            else:
                self.fields['subsection'].queryset = models.Section.objects.public_filter(
                    is_on_sales=True, org_type='03',
                )
        elif instance and instance.pk:
            self.fields['division'].queryset = models.Section.objects.public_filter(is_on_sales=True, org_type='01')
            self.fields['section'].queryset = models.Section.objects.public_filter(org_type='02')
            if instance.section:
                self.fields['subsection'].queryset = models.Section.objects.public_filter(
                    org_type='03',
                    parent__pk=instance.section.pk
                )
            else:
                self.fields['subsection'].queryset = models.Section.objects.public_filter(org_type='03')
        else:
            self.fields['division'].queryset = models.Section.objects.public_filter(is_on_sales=True, org_type='01')
            self.fields['section'].queryset = models.Section.objects.public_filter(is_on_sales=True, org_type='02')
            self.fields['subsection'].queryset = models.Section.objects.public_filter(is_on_sales=True, org_type='03')
        self.fields['division'].widget.attrs.update({'onchange': 'setSubOrganizations(this)'})
        self.fields['section'].widget.attrs.update({'onchange': 'setSubOrganizations(this)'})

    def clean(self):
        cleaned_data = super(MemberSectionPeriodForm, self).clean()
        start_date = cleaned_data.get("start_date")
        end_date = cleaned_data.get("end_date")
        division = cleaned_data.get('division')
        section = cleaned_data.get('section')
        subsection = cleaned_data.get('subsection')
        if not division and not section and not subsection:
            self.add_error('division', u"事業部を選択してください。")
        if end_date and end_date <= start_date:
            self.add_error('end_date', u"終了日は開始日以降に設定してください。")
        if 'section' in self.changed_data and self.instance.pk:
            self.add_error('section', u"部署を変更できません、変更したい場合は新しい部署とその期間を追加してください。")
        if section and division:
            if not section.parent or section.parent.pk != division.pk:
                self.add_error('section',
                               u"指定された「%s」は「%s」に所属していません。" % (section.name, division.name))
        if section and subsection:
            if not subsection.parent or subsection.parent.pk != section.pk:
                self.add_error('subsection',
                               u"指定された「%s」は「%s」に所属していません。" % (subsection.name, section.name))


class MemberSalespersonPeriodForm(forms.ModelForm):

    class Meta:
        model = models.MemberSalespersonPeriod
        fields = '__all__'

    def __init__(self, *args, **kwargs):
        self.request = kwargs.pop('request', None)
        forms.ModelForm.__init__(self, *args, **kwargs)
        self.fields['salesperson'].queryset = models.Salesperson.objects.public_all()

    def clean(self):
        cleaned_data = super(MemberSalespersonPeriodForm, self).clean()
        start_date = cleaned_data.get("start_date")
        end_date = cleaned_data.get("end_date")
        if end_date and end_date <= start_date:
            self.add_error('end_date', u"終了日は開始日以降に設定してください。")
        if 'salesperson' in self.changed_data and self.instance.pk:
            self.add_error('salesperson',
                           u"営業員を変更できません、変更したい場合は新しい営業員とその期間を追加してください。")


class MemberSectionPeriodFormset(forms.BaseInlineFormSet):
    def clean(self):
        count = 0
        dates = []
        for form in self.forms:
            try:
                if form.cleaned_data:
                    start_date = form.cleaned_data.get("start_date")
                    end_date = form.cleaned_data.get("end_date")
                    if start_date:
                        dates.append((start_date, end_date))
                        count += 1
            except AttributeError:
                pass
        if count < 1:
            raise forms.ValidationError(u'部署期間を少なくとも１つ追加してください。')
        elif count > 1:
            dates.sort(key=lambda date: date[0])
            for i, period in enumerate(dates):
                start_date, end_date = period
                if common.is_cross_date(dates, start_date, i):
                    raise forms.ValidationError(u"部署期間の開始日が重複している。")
                if end_date and common.is_cross_date(dates, end_date, i):
                    raise forms.ValidationError(u"部署期間の終了日が重複している。")


class MemberSalespersonPeriodFormset(forms.BaseInlineFormSet):

    def __init__(self, data=None, files=None, instance=None,
                 save_as_new=False, prefix=None, queryset=None, **kwargs):
        self.request = kwargs.pop('request', None)
        super(MemberSalespersonPeriodFormset, self).__init__(data, files, instance, save_as_new, prefix, queryset, **kwargs)

    def _construct_form(self, i, **kwargs):
        kwargs.update({'request': self.request})
        form = super(MemberSalespersonPeriodFormset, self)._construct_form(i, **kwargs)
        return form

    def clean(self):
        count = 0
        dates = []
        for form in self.forms:
            try:
                if form.cleaned_data:
                    start_date = form.cleaned_data.get("start_date")
                    end_date = form.cleaned_data.get("end_date")
                    dates.append((start_date, end_date))
                    count += 1
            except AttributeError:
                pass
        if count < 1:
            raise forms.ValidationError(u'営業員期間を少なくとも１つ追加してください。')
        elif count > 1:
            dates.sort(key=lambda date: date[0])
            for i, period in enumerate(dates):
                start_date, end_date = period
                if common.is_cross_date(dates, start_date, i):
                    raise forms.ValidationError(u"営業員期間の開始日が重複している。")
                if end_date and common.is_cross_date(dates, end_date, i):
                    raise forms.ValidationError(u"営業員期間の終了日が重複している。")


class MemberSalesOffPeriodFormset(forms.BaseInlineFormSet):

    def clean(self):
        count = 0
        dates = []
        for form in self.forms:
            try:
                if form.cleaned_data:
                    start_date = form.cleaned_data.get("start_date")
                    end_date = form.cleaned_data.get("end_date")
                    dates.append((start_date, end_date))
                    count += 1
            except AttributeError:
                pass
        if count > 1:
            dates.sort(key=lambda date: date[0])
            for i, period in enumerate(dates):
                start_date, end_date = period
                if common.is_cross_date(dates, start_date, i):
                    raise forms.ValidationError(u"営業対象外期間の開始日が重複している。")
                if end_date and common.is_cross_date(dates, end_date, i):
                    raise forms.ValidationError(u"営業対象外期間の終了日が重複している。")


class BatchCarbonCopyForm(forms.ModelForm):
    class Meta:
        model = models.BatchCarbonCopy
        fields = '__all__'

    member = forms.ModelChoiceField(queryset=models.Member.objects.public_all(),
                                    widget=SearchSelect(models.Member),
                                    label=u"名前", required=False)

    def clean(self):
        cleaned_data = super(BatchCarbonCopyForm, self).clean()
        member = cleaned_data.get("member")
        salesperson = cleaned_data.get("salesperson")
        if member and not member.email:
            self.add_error('member', u"メールアドレスが設定されていません。")
        if salesperson and not salesperson.email:
            self.add_error('salesperson', u"メールアドレスが設定されていません。")


class ConfigForm(forms.ModelForm):
    class Meta:
        model = models.Config
        fields = '__all__'

    def __init__(self, *args, **kwargs):
        super(ConfigForm, self).__init__(*args, **kwargs)
        instance = kwargs.get('instance', None)
        if instance and isinstance(instance, models.Config):
            if instance.name == 'theme':
                self.fields['value'] = forms.ChoiceField(constants.CHOICE_THEME, required=True, label=u"設定値")
            elif instance.name == 'bp_attendance_type':
                self.fields['value'] = forms.ChoiceField(constants.CHOICE_ATTENDANCE_TYPE, required=True, label=u"設定値")
            elif instance.name and instance.name.find('mail_body') > 0:
                self.fields['value'] = forms.CharField(widget=forms.Textarea(attrs={'style': 'width: 610px;'}),
                                                       required=True, label=u"設定値")
            elif instance.group and instance.group in ('contract', 'bp_order'):
                self.fields['value'] = forms.CharField(widget=forms.Textarea(attrs={'style': 'width: 610px;'}),
                                                       required=True, label=u"設定値")


class MailGroupForm(forms.ModelForm):
    class Meta:
        model = models.MailGroup
        fields = '__all__'


class MailCcListForm(forms.ModelForm):
    class Meta:
        model = models.MailCcList
        fields = '__all__'

    member = forms.ModelChoiceField(queryset=models.Member.objects.public_all(),
                                    widget=SearchSelect(models.Member),
                                    label=u"名前", required=False)

    def clean(self):
        cleaned_data = super(MailCcListForm, self).clean()
        member = cleaned_data.get("member")
        if member and not member.email:
            self.add_error('member', u"メールアドレスが設定されていません。")


class MailTemplateForm(forms.ModelForm):
    class Meta:
        model = models.MailTemplate
        fields = '__all__'

    def __init__(self, *args, **kwargs):
        super(MailTemplateForm, self).__init__(*args, **kwargs)
        self.fields['mail_title'].widget.attrs.update({'style': 'width: 500px;'})


class SubcontractorMemberForm(forms.ModelForm):
    class Meta:
        model = models.SubcontractorMember
        fields = '__all__'


class SubcontractorBankInfoForm(forms.ModelForm):
    class Meta:
        model = models.SubcontractorBankInfo
        fields = '__all__'

    def __init__(self, *args, **kwargs):
        super(SubcontractorBankInfoForm, self).__init__(*args, **kwargs)
        self.fields['branch_no'].widget.attrs.update({'style': 'width: 80px;'})
        self.fields['branch_name'].widget.attrs.update({'style': 'width: 80px;'})
        self.fields['account_number'].widget.attrs.update({'style': 'width: 100px;'})
        self.fields['account_holder'].widget.attrs.update({'style': 'width: 120px;'})


class ProjectRequestForm(forms.ModelForm):

    class Meta:
        model = models.ProjectRequest
        fields = ('request_name', 'turnover_amount', 'tax_amount', 'expenses_amount', 'amount')


class ProjectRequestHeadingForm(forms.ModelForm):

    class Meta:
        model = models.ProjectRequestHeading
        fields = ('work_period_start', 'work_period_end', 'publish_date')


class ProjectRequestDetailForm(forms.ModelForm):

    class Meta:
        model = models.ProjectRequestDetail
        fields = ('basic_price', 'total_price',)
