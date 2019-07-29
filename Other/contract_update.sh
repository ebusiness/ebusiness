#!/bin/bash

docker run --rm --link mysql:mysql -v /home/ec2-user/work/sales/ebusiness:/ebusiness yangwanjun/sales-ubuntu python /ebusiness/manage.py sync_contract