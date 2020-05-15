import os


def main():
    path = os.path.join(os.path.dirname(__name__), 'SQL')
    with open(os.path.join(path, 'sql_win.bat'), 'w') as f_win, open(os.path.join(path, 'sql_mac.sh'), 'w') as f_mac:
        f_win.write('@echo off\n')
        f_win.write('set /P HOST="Host Name(192.168.99.100):" '
                    '|| SET "HOST=192.168.99.100"\n\n')
        f_win.write('set /P DB="Database Name(eb_sales):" || SET "DB=eb_sales"\n\n')
        f_win.write('set /P PWD="Password(root):" || SET "PWD=root"\n\n')
        f_mac.write('#!/bin/bash\n\n')
        f_mac.write('read -p "Host Name:" HOST\n')
        f_mac.write('read -p "Database Name:" DB\n')
        f_mac.write('read -p "Password:" PWD\n')
        for name in sorted(os.listdir(path)):
            if not name.lower().endswith('.sql'):
                continue
            f_win.write('mysql -h %HOST% --default-character-set=utf8 -u root -p%PWD% %DB% < {}\n'.format(name))
            f_mac.write('mysql -h $HOST -u root -p$PWD $DB < {}\n'.format(name))


if __name__ == '__main__':
    main()
