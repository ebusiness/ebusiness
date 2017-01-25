# coding: UTF-8
"""
Created on 2017/01/20

@author: Yang Wanjun
"""
import os
import xlrd

from eb import models

from django.core.management.base import BaseCommand
from django.conf import settings
from django.db import connection


class Command(BaseCommand):

    def handle(self, *args, **options):
        self.stdout.write(u"Start...")
        tables = self.read_data()
        for table in tables:
            for row in table.Rows:
                if not table.is_data_exist(row):
                    table.insert_row(row)
        self.stdout.write(u"End...")

    def get_data_file(self):
        return os.path.join(settings.MEDIA_ROOT, 'test_data.xlsx')


    def read_data(self):
        file_path = self.get_data_file()
        if not os.path.exists(file_path):
            self.stdout.write(u"(%s) not exist!" % (file_path,))
            return None

        book = xlrd.open_workbook(file_path)
        sheet = book.sheet_by_index(0)

        table_name = None
        tables = []
        for r in range(sheet.nrows):
            text = sheet.cell_value(r, 0)
            if text and (text.startswith('eb_') or text.startswith('mst_')):
                table_name = text
            else:
                continue

            table = Table(table_name)
            tables.append(table)
            col_id_list = sheet.row_values(r + 2, start_colx=1)
            # 項目ＩＤを取得
            col_count = 1
            for col_id in col_id_list:
                if col_id:
                    column = Column(col_id)
                    table.Columns.append(column)
                    col_count += 1
            # 項目の値を取得する。
            row_index = r + 4
            while row_index < sheet.nrows and sheet.cell_value(row_index, 1) and sheet.cell_value(row_index, 1) != u"0件":
                data_list = sheet.row_values(row_index, start_colx=1, end_colx=col_count)
                row_data = []
                for data in data_list:
                    if data == 'NULL':
                        row_data.append(data)
                    elif data == 'False':
                        row_data.append(0)
                    elif data == 'True':
                        row_data.append(1)
                    else:
                        row_data.append("'" + data + "'")
                table.Rows.append(row_data)
                row_index += 1
        return tables


class Table:
    def __init__(self, name):
        self.name = name
        self.Columns = []
        self.Rows = []

    def is_data_exist(self, row):
        with connection.cursor() as cursor:
            sql = "SELECT count(*) FROM %s WHERE id = %s" % (self.name, row[0])
            cursor.execute(sql)
            cnt = cursor.fetchone()[0]
            if cnt > 0:
                return True
            else:
                return False

    def to_insert_sql(self, row):
        col_id_list = [col.name for col in self.Columns]
        sql = 'INSERT INTO %s (%s) VALUES (%s)' % (self.name, ', '.join(col_id_list), ', '.join(row))

        return sql

    def insert_row(self, row):
        sql = self.to_insert_sql(row)
        with connection.cursor() as cursor:
            try:
                cursor.execute(sql)
            except:
                print 'ERROR', sql


class Column:
    def __init__(self, name):
        self.name = name
