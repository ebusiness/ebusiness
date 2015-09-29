# coding: UTF-8
"""
Created on 2015/09/28

@author: Yang Wanjun
"""
EXCEL_APPLICATION = "Excel.Application"
EXCEL_FORMAT_EXCEL2003 = 56

NAME_BUSINESS_PLAN = u"%02d月営業企画"
NAME_MEMBER_LIST = u"最新要員一覧"

MARK_POST_CODE = u"〒"

DOWNLOAD_REQUEST = "request"
DOWNLOAD_BUSINESS_PLAN = "business_plan"
DOWNLOAD_MEMBER_LIST = "member_list"

CHOICE_PROJECT_MEMBER_STATUS = ((1, u"提案中"),
                                (2, u"作業中"),
                                (3, u"作業終了"))
CHOICE_PROJECT_STATUS = ((1, u"提案"), (2, u"予算審査"), (3, u"予算確定"), (4, u"実施中"), (5, u"完了"))
CHOICE_SKILL_TIME = ((0, u"未経験者可"),
                     (1, u"１年以上"),
                     (2, u"２年以上"),
                     (3, u"３年以上"),
                     (5, u"５年以上"),
                     (10, u"１０年以上"))
CHOICE_DEGREE_TYPE = ((1, u"小・中学校"),
                      (2, u"高等学校"),
                      (3, u"専門学校"),
                      (4, u"高等専門学校"),
                      (5, u"短期大学"),
                      (6, u"大学学部"),
                      (7, u"大学大学院"))
CHOICE_MEMBER_TYPE = ((0, u"正社員"), (1, u"契約社員"), (3, u"派遣社員"), (4, u"個人事業主"))
CHOICE_PROJECT_ROLE = ((1, u"OP：ｵﾍﾟﾚｰﾀｰ"), (2, u"PG：ﾌﾟﾛｸﾞﾗﾏｰ"), (3, u"SP：ｼｽﾃﾑﾌﾟﾛｸﾞﾗﾏｰ"), (4, u"SE：ｼｽﾃﾑｴﾝｼﾞﾆｱ"),
                       (5, u"SL：ｻﾌﾞﾘｰﾀﾞｰ"), (6, u"L：ﾘｰﾀﾞｰ"), (7, u"M：ﾏﾈｰｼﾞｬｰ"))
CHOICE_POSITION = ((1, u"代表取締役"), (2, u"社長"), (3, u"取締役"), (4, u"部長"), (5, u"担当部長"),
                   (6, u"課長"), (7, u"担当課長"), (8, u"PM"), (9, u"リーダー"), (10, u"サブリーダー"))
CHOICE_SEX = (('1', u"男"), ('2', u"女"))
CHOICE_MARRIED = (('', u"------"), ('0', u"未婚"), ('1', u"既婚"))