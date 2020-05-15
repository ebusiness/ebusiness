#!/bin/bash

read -p "Host Name:" HOST
read -p "Database Name:" DB
read -p "Password:" PWD
mysql -h $HOST -u root -p$PWD $DB < 001.get_days.sql
mysql -h $HOST -u root -p$PWD $DB < 001.get_ym.sql
mysql -h $HOST -u root -p$PWD $DB < 002.get_attendance_total_hours.sql
mysql -h $HOST -u root -p$PWD $DB < 003.get_employment_insurance.sql
mysql -h $HOST -u root -p$PWD $DB < 004.get_health_insurance.sql
mysql -h $HOST -u root -p$PWD $DB < 005.get_night_allowance.sql
mysql -h $HOST -u root -p$PWD $DB < 006.get_overtime.sql
mysql -h $HOST -u root -p$PWD $DB < 007.get_overtime_cost.sql
mysql -h $HOST -u root -p$PWD $DB < 008.get_member_status_by_month.sql
mysql -h $HOST -u root -p$PWD $DB < 009.get_member_status_today.sql
mysql -h $HOST -u root -p$PWD $DB < 010.get_member_release_date.sql
mysql -h $HOST -u root -p$PWD $DB < 011.get_bp_expenses.sql
mysql -h $HOST -u root -p$PWD $DB < 012.get_salary.sql
mysql -h $HOST -u root -p$PWD $DB < 013.get_department.sql
mysql -h $HOST -u root -p$PWD $DB < 014.get_min_hours.sql
mysql -h $HOST -u root -p$PWD $DB < 101.v_interval_dates.sql
mysql -h $HOST -u root -p$PWD $DB < 102.v_turnover_dates.sql
mysql -h $HOST -u root -p$PWD $DB < 111.v_contract.sql
mysql -h $HOST -u root -p$PWD $DB < 112.v_organization_cost.sql
mysql -h $HOST -u root -p$PWD $DB < 113.v_organization_turnover.sql
mysql -h $HOST -u root -p$PWD $DB < 114.v_sales_member.sql
mysql -h $HOST -u root -p$PWD $DB < 115.v_release_list.sql
mysql -h $HOST -u root -p$PWD $DB < 116.v_salesperson_status.sql
mysql -h $HOST -u root -p$PWD $DB < 117.v_status_monthly.sql
mysql -h $HOST -u root -p$PWD $DB < 118.v_latest_bp_contract.sql
mysql -h $HOST -u root -p$PWD $DB < 119.v_member_insurance_level.sql
mysql -h $HOST -u root -p$PWD $DB < 120.v_member_insurance.sql
mysql -h $HOST -u root -p$PWD $DB < 121.v_dispatch_member.sql
mysql -h $HOST -u root -p$PWD $DB < 122.v_member_without_contract.sql
mysql -h $HOST -u root -p$PWD $DB < 123.v_client_request.sql
mysql -h $HOST -u root -p$PWD $DB < 124.v_bp_request.sql
mysql -h $HOST -u root -p$PWD $DB < 201.sp_organization_cost.sql
mysql -h $HOST -u root -p$PWD $DB < 202.sp_organization_turnover.sql
mysql -h $HOST -u root -p$PWD $DB < 203.sp_sales_member.sql
mysql -h $HOST -u root -p$PWD $DB < 204.sp_dispatch_members.sql
mysql -h $HOST -u root -p$PWD $DB < 205.sp_divisions_turnover_by_month.sql
mysql -h $HOST -u root -p$PWD $DB < 206.sp_division_turnover_by_month.sql
mysql -h $HOST -u root -p$PWD $DB < 207.sp_bp_order_manage_list.sql
mysql -h $HOST -u root -p$PWD $DB < set_ym.sql
