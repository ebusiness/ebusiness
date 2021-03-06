# coding: utf-8
import os
import sys
import getpass
import MySQLdb
import django
from django.core.management import call_command

from contract import migrations as contract_migrations
from eb import migrations as eb_migrations
from flow import migrations as flow_migrations


os.environ.setdefault("DJANGO_SETTINGS_MODULE", "employee.settings")
django.setup()

if sys.platform == 'win32' and getpass.getuser() == 'EB097':
    user = 'root'
    password = 'root'
    host = 'localhost'
else:
    user = 'root'
    password = os.environ['MYSQL_ENV_MYSQL_ROOT_PASSWORD']
    host = os.environ['MYSQL_PORT_3306_TCP_ADDR']


def main():
    del_migration_records()
    del_migration_files()
    migrate()


def migrate():
    call_command('migrate', '--fake')
    call_command('makemigrations', 'eb')
    call_command('makemigrations', 'flow')
    call_command('makemigrations', 'contract')
    call_command('migrate', '--fake')


def del_migration_records():
    con = MySQLdb.connect(user=user, passwd=password, db='eb_sales', host=host)
    cursor = con.cursor()
    try:
        cnt = cursor.execute("delete from django_migrations")
        print 'EXEC: delete from django_migrations. %s rows deleted' % cnt
        con.commit()
    except Exception as e:
        con.roolback()
        raise e
    finally:
        cursor.close()
        con.close()


def del_migration_files():
    path_list = list()
    path_list.append(os.path.dirname(contract_migrations.__file__))
    path_list.append(os.path.dirname(flow_migrations.__file__))
    path_list.append(os.path.dirname(eb_migrations.__file__))

    for path in path_list:
        for filename in os.listdir(path):
            if filename not in ('__init__.py', '__init__.pyc'):
                file_path = os.path.join(path, filename)
                os.remove(file_path)
                print 'DEL: %s' % file_path


if __name__ == '__main__':
    main()
