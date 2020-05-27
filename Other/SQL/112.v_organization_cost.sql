CREATE OR REPLACE VIEW v_organization_cost AS
select distinct m.id as member_id
     , m.employee_id
     , m.first_name
     , m.last_name
     , msp1.id as membersectionperiod_id
     , case p.is_reserve
           when 1 then p.department_id
           else (select s1.id from eb_section s1 where s1.id = msp1.division_id) 
       end as division_id
     , case p.is_reserve
           when 1 then (select s1.name from eb_section s1 where s1.id = p.department_id) 
           else (select s1.name from eb_section s1 where s1.id = msp1.division_id) 
       end as division_name
     , (select s1.id from eb_section s1 where s1.id = msp1.section_id) as section_id
     , (select s1.name from eb_section s1 where s1.id = msp1.section_id) as section_name
     , (select s1.id from eb_section s1 where s1.id = msp1.subsection_id) as subsection_id
     , (select s1.name from eb_section s1 where s1.id = msp1.subsection_id) as subsection_name
     , msp2.salesperson_id
     , (select concat(s1.first_name, ' ', s1.last_name) from eb_salesperson s1 where s1.id = msp2.salesperson_id) as salesperson_name
     , pm.id as projectmember_id
     , p.id as project_id
     , p.name as project_name
     , p.nearest_station
     , p.is_reserve
     , p.is_lump
     , c1.id as client_id
     , c1.name as client_name
     , c.company_id
     , case c.content_type_id
           when 7 then (select name from eb_company where id = c.company_id)
           else (select name from eb_subcontractor where id = c.company_id)
       end as company_name
     , c.endowment_insurance
     , c.member_type
     , case c.member_type
           when 1 then '正社員'
           when 2 then '契約社員'
           when 3 then '個人事業者'
           when 4 then '他社技術者'
           when 5 then 'パート'
           when 6 then 'アルバイト'
           when 7 then '正社員（試用期間）'
           else c.member_type
       end as member_type_name
     , c.contract_type
     , c.cost
     , c.is_hourly_pay
     , c.is_fixed_cost
     , IFNULL(bp_h.allowance_time_min, c.allowance_time_min) as min_hours
     , c.allowance_time_max as max_hours
     , c.allowance_absenteeism as minus_per_hour
     , c.allowance_overtime as plus_per_hour
     , c.is_loan
     , IF(p.is_lump = 1 and prd.id is null, (select min(t1.id) from eb_projectrequest t1 where t1.project_id = p.id and concat(t1.year, t1.month) = get_ym()), IFNULL(prd.id, 0)) as projectrequestdetail_id
     , IF(ma.id is null, IFNULL(prev_ma.traffic_cost, 0), 0) as prev_traffic_cost           -- 先月の勤務交通費
     , IF(ma.id is null, IFNULL(prev_ma.allowance, 0), 0) as prev_allowance                 -- 先月の手当
     , ma.id as memberattendance_id
     , IFNULL(ma.total_hours, 0) as total_hours
     , ma.total_hours_bp
     , case
           when c.is_hourly_pay or c.is_fixed_cost then 0
           when ma.id is null then 0
           when ma.total_hours_bp = 0 then 0
           else get_overtime(ifnull(ma.total_hours_bp, IFNULL(ma.total_hours, 0)), IFNULL(bp_h.allowance_time_min, c.allowance_time_min), c.allowance_time_max, c.is_hourly_pay, c.is_fixed_cost, p.is_reserve)
       end as extra_hours
     , IFNULL(ma.total_days, 0) as total_days
     , IFNULL(ma.night_days, 0) as night_days
     , ma.paid_vacation_days
     , IFNULL(ma.advances_paid_client, 0) as advances_paid_client
     , IFNULL(ma.advances_paid, 0) as advances_paid
     , IF(c.member_type = 4, 0, IFNULL(ma.traffic_cost, 0)) as traffic_cost
     , case 
           when p.is_lump = 1 and prd.id is null and pm.id = (select min(s1.id) from eb_projectmember s1 where s1.project_id = p.id and s1.is_deleted = 0 and s1.status = 2)
               then ifnull((select t1.amount from eb_projectrequest t1 where t1.project_id = p.id and concat(t1.year, t1.month) = get_ym()), 0)         -- 要員アサインした一括案件の場合、売上は１つの要員に表示され、ほかに０にする。
           when p.is_lump = 1 and prd.id is null then 0
           else IFNULL(prd.total_price + prd.expenses_price + prd.total_price * prh.tax_rate, 0) 
       end as all_price             -- 売上（税込）
     , case
           when p.is_lump = 1 and prd.id is null and pm.id = (select min(s1.id) from eb_projectmember s1 where s1.project_id = p.id and s1.is_deleted = 0 and s1.status = 2)
               then ifnull((select t1.turnover_amount from eb_projectrequest t1 where t1.project_id = p.id and concat(t1.year, t1.month) = get_ym()), 0)    -- 要員アサインした一括案件の場合
           when p.is_lump = 1 and prd.id is null then 0
           else IFNULL(prd.total_price, 0) 
       end as total_price           -- 売上（税抜）
     , case
           when p.is_lump = 1 and prd.id is null and pm.id = (select min(s1.id) from eb_projectmember s1 where s1.project_id = p.id and s1.is_deleted = 0 and s1.status = 2)
               then ifnull((select t1.expenses_amount from eb_projectrequest t1 where t1.project_id = p.id and concat(t1.year, t1.month) = get_ym()), 0)    -- 要員アサインした一括案件の場合
           when p.is_lump = 1 and prd.id is null then 0
           else IFNULL(prd.expenses_price, 0) 
       end as expenses_price        -- 売上（経費）
     , case
           when p.is_lump = 1 and prd.id is null and pm.id = (select min(s1.id) from eb_projectmember s1 where s1.project_id = p.id and s1.is_deleted = 0 and s1.status = 2)
               then ifnull((select t1.tax_amount from eb_projectrequest t1 where t1.project_id = p.id and concat(t1.year, t1.month) = get_ym()), 0)     -- 要員アサインした一括案件の場合
           when p.is_lump = 1 and prd.id is null then 0
           else IFNULL(prd.total_price * prh.tax_rate, 0) 
       end as tax_price
     , IFNULL(IF(c.is_hourly_pay = 0, c.cost, c.cost * get_attendance_total_hours(ifnull(ma.total_hours_bp, IFNULL(ma.total_hours, 0))) + c.allowance_other), 0) as salary
     , IFNULL(ma.allowance, 0) as allowance
     , get_night_allowance(ma.night_days) as night_allowance
     , get_overtime_cost(ifnull(ma.total_hours_bp, IFNULL(ma.total_hours, 0)), IFNULL(bp_h.allowance_time_min, c.allowance_time_min), c.allowance_time_max, c.is_hourly_pay, c.is_fixed_cost, p.is_reserve, c.allowance_absenteeism, c.allowance_overtime) as overtime_cost
     , case c.member_type
           when 4 then get_bp_expenses(pm.id, ma.year, ma.month)
           else IFNULL(ma.expenses, 0) 
       end as expenses
     , get_employment_insurance(
           c.member_type,
           IFNULL(IF(c.is_hourly_pay = 0, c.cost, c.cost * get_attendance_total_hours(ifnull(ma.total_hours_bp, IFNULL(ma.total_hours, 0)))), 0),
           IFNULL(ma.allowance, 0),
           get_night_allowance(ma.night_days),
           get_overtime_cost(ifnull(ma.total_hours_bp, IFNULL(ma.total_hours, 0)), IFNULL(bp_h.allowance_time_min, c.allowance_time_min), c.allowance_time_max, c.is_hourly_pay, c.is_fixed_cost, p.is_reserve, c.allowance_absenteeism, c.allowance_overtime),
           IFNULL(ma.traffic_cost, 0)
       ) as employment_insurance
     , case 
           when c.member_type <> 4 then get_health_insurance(
               c.endowment_insurance,
               IFNULL(IF(c.is_hourly_pay = 0, c.cost, c.cost * get_attendance_total_hours(ifnull(ma.total_hours_bp, IFNULL(ma.total_hours, 0)))), 0),
               IFNULL(ma.allowance, 0),
               get_night_allowance(ma.night_days),
               get_overtime_cost(ifnull(ma.total_hours_bp, IFNULL(ma.total_hours, 0)), IFNULL(bp_h.allowance_time_min, c.allowance_time_min), c.allowance_time_max, c.is_hourly_pay, c.is_fixed_cost, p.is_reserve, c.allowance_absenteeism, c.allowance_overtime),
               IFNULL(ma.traffic_cost, 0),
               m.id,
               get_ym()
           )
           else 0
       end as health_insurance 
     , IFNULL(ma.expenses_conference, 0) as expenses_conference             -- 会議費
     , IFNULL(ma.expenses_entertainment, 0) as expenses_entertainment       -- 交際費
     , IFNULL(ma.expenses_travel, 0) as expenses_travel                     -- 旅費交通費
     , IFNULL(ma.expenses_communication, 0) as expenses_communication       -- 通信費
     , IFNULL(ma.expenses_tax_dues, 0) as expenses_tax_dues                 -- 租税公課
     , IFNULL(ma.expenses_expendables, 0) as expenses_expendables           -- 消耗品
  from eb_member m
  left join eb_membersectionperiod msp1 on msp1.member_id = m.id 
                                       and msp1.is_deleted = 0 
                                       and extract(year_month from(msp1.start_date)) <= get_ym()
                                       and (extract(year_month from(msp1.end_date)) >= get_ym() or msp1.end_date is null)
                                       and msp1.id = (
                                           select id
                                             from eb_membersectionperiod s1
                                            where s1.member_id = m.id
                                              and s1.is_deleted = 0 
                                              and extract(year_month from(s1.start_date)) <= get_ym()
                                              and (extract(year_month from(s1.end_date)) >= get_ym() or s1.end_date is null)
                                            order by s1.start_date desc
                                            limit 1
                                       )
  left join eb_membersalespersonperiod msp2 on msp2.member_id = m.id 
                                           and msp2.is_deleted = 0 
                                           and extract(year_month from(msp2.start_date)) <= get_ym()
                                           and (extract(year_month from(msp2.end_date)) >= get_ym() or msp2.end_date is null)
  join eb_projectmember pm on pm.member_id = m.id and pm.is_deleted = 0 
                          and pm.status = 2 
                          and extract(year_month from(pm.start_date)) <= get_ym()
                          and (extract(year_month from(pm.end_date)) >= get_ym() or pm.end_date is null)
  left join eb_projectmember prev_pm on prev_pm.member_id = m.id and prev_pm.is_deleted = 0 
                          and prev_pm.status = 2
                          and extract(year_month from(prev_pm.start_date)) <= DATE_FORMAT(STR_TO_DATE(concat(get_ym(), '01'), '%Y%m%d') - INTERVAL 1 MONTH, '%Y%m')
                          and (extract(year_month from(prev_pm.end_date)) >= DATE_FORMAT(STR_TO_DATE(concat(get_ym(), '01'), '%Y%m%d') - INTERVAL 1 MONTH, '%Y%m') or prev_pm.end_date is null)
                          and not exists(select 1 from eb_project s1 where s1.id = prev_pm.project_id and s1.is_reserve = 1)
                          -- 前月の案件が二つ以上存在する場合の対策、一つしか取得するように。
                          and prev_pm.id = (
                              select min(prev_pm1.id)
                                from eb_projectmember prev_pm1
                               where prev_pm1.member_id = m.id and prev_pm1.is_deleted = 0 
                                 and prev_pm1.status = 2
                                 and extract(year_month from(prev_pm1.start_date)) <= DATE_FORMAT(STR_TO_DATE(concat(get_ym(), '01'), '%Y%m%d') - INTERVAL 1 MONTH, '%Y%m')
                                 and (extract(year_month from(prev_pm1.end_date)) >= DATE_FORMAT(STR_TO_DATE(concat(get_ym(), '01'), '%Y%m%d') - INTERVAL 1 MONTH, '%Y%m') or prev_pm1.end_date is null)
                                 and not exists(select 1 from eb_project s1 where s1.id = prev_pm1.project_id and s1.is_reserve = 1)
                          )
  join eb_project p on p.id = pm.project_id
  join eb_client c1 on c1.id = p.client_id
  left join eb_memberattendance ma on ma.project_member_id = pm.id and concat(ma.year, ma.month) = get_ym()
  left join eb_memberattendance prev_ma on prev_ma.project_member_id = prev_pm.id
                                       and concat(prev_ma.year, prev_ma.month) = DATE_FORMAT(STR_TO_DATE(concat(get_ym(), '01'), '%Y%m%d') - INTERVAL 1 MONTH, '%Y%m')
  left join eb_projectrequestdetail prd on prd.project_member_id = pm.id and concat(prd.year, prd.month) = get_ym()
  left join eb_projectrequest pr on pr.id = prd.project_request_id and concat(pr.year, pr.month) = get_ym()
  left join eb_projectrequestheading prh on prh.project_request_id = pr.id
  left join v_contract c on c.member_id = m.id 
                        and c.is_old = 0 and extract(year_month from(c.start_date)) <= get_ym()
                        and (extract(year_month from(c.end_date)) >= get_ym() or c.end_date is null)
  left join eb_bpmemberorder bp_o on bp_o.project_member_id = pm.id and bp_o.is_deleted = 0 and bp_o.year = ma.year and bp_o.month = ma.month
  left join eb_bpmemberorderheading bp_h on bp_h.bp_order_id = bp_o.id
 where m.is_deleted = 0
union all
select null as member_id
     , null as employee_id
     , null as first_name
     , null as last_name
     , null as membersectionperiod_id
     , s.id as division_id
     , s.name division_name
     , null as section_id
     , null as section_name
     , null as subsection_id
     , null as subsection_name
     , null as salesperson_id
     , null as salesperson_name
     , null as projectmember_id
     , p.id as project_id
     , p.name as project_name
     , p.nearest_station
     , p.is_reserve
     , p.is_lump
     , c1.id as client_id
     , c1.name as client_name
     , null as company_id
     , null as company_name
     , null as endowment_insurance
     , null as member_type
     , null as member_type_name
     , null as contract_type
     , 0 as cost
     , 0 as is_hourly_pay
     , 0 as is_fixed_cost
     , 0 as min_hours
     , 0 as max_hours
     , 0 as minus_per_hour
     , 0 as plus_per_hour
     , 0 as is_loan
     , pr.id as projectrequestdetail_id
     , 0 as prev_traffic_cost
     , 0 as prev_allowance
     , null as memberattendance_id
     , 0 as total_hours
     , 0 as total_hours_bp
     , 0 as extra_hours
     , 0 as total_days
     , 0 as night_days
     , null as paid_vacation_days
     , 0 as advances_paid_client
     , 0 as advances_paid
     , 0 as traffic_cost
     , pr.amount as all_price
     , pr.turnover_amount as total_price
     , pr.expenses_amount as expenses_price
     , pr.tax_amount as tax_price
     , 0 as salary
     , 0 as allowance
     , 0 as night_allowance
     , 0 as overtime_cost
     , 0 as expenses
     , 0 as employment_insurance
     , 0 as health_insurance 
     , 0 as expenses_conference     -- 会議費
     , 0 as expenses_entertainment  -- 交際費
     , 0 as expenses_travel         -- 旅費交通費
     , 0 as expenses_communication  -- 通信費
     , 0 as expenses_tax_dues       -- 租税公課
     , 0 as expenses_expendables    -- 消耗品
  from eb_project p
  join eb_section s on p.department_id = s.id
  join eb_client c1 on c1.id = p.client_id
  join eb_projectrequest pr on pr.project_id = p.id
 where p.is_lump = 1
   and p.is_deleted = 0
   and concat(pr.year, pr.month) = get_ym()
   and not exists(select 1 from eb_projectmember pm where pm.project_id = p.id and pm.is_deleted = 0)
UNION ALL
-- ＢＰの一括契約
select null as member_id
     , null as employee_id
     , null as first_name
     , null as last_name
     , null as membersectionperiod_id
     , IF(s.org_type = '01', s.id, null) as division_id
     , IF(s.org_type = '01', s.name, null) as division_name
     , IF(s.org_type = '02', s.id, null) as section_id
     , IF(s.org_type = '02', s.name, null) as section_name
     , IF(s.org_type = '03', s.id, null) as subsection_id
     , IF(s.org_type = '03', s.id, null) as subsection_name
     , null as salesperson_id
     , null as salesperson_name
     , null as projectmember_id
     , p.id as project_id
     , p.name as project_name
     , p.nearest_station
     , 0 as is_reserve
     , 1 as is_lump
     , null as client_id
     , null as client_name
     , sc.id as company_id
     , sc.name as company_name
     , null as endowment_insurance
     , 4 as member_type
     , '他者技術者' as member_type_name
     , lc.contract_type
     , lc.allowance_base as cost
     , 0 as is_hourly_pay
     , 1 as is_fixed_cost
     , 0 as min_hours
     , 0 as max_hours
     , 0 as minus_per_hour
     , 0 as plus_per_hour
     , 0 as is_loan
     , null as projectrequestdetail_id
     , 0 as prev_traffic_cost
     , 0 as prev_allowance
     , null as memberattendance_id
     , 0 as total_hours
     , 0 as total_hours_bp
     , 0 as extra_hours
     , 0 as total_days
     , 0 as night_days
     , null as paid_vacation_days
     , 0 as advances_paid_client
     , 0 as advances_paid
     , 0 as traffic_cost
     , 0 as all_price
     , 0 as total_price
     , 0 as expenses_price
     , 0 as tax_price
     , lc.allowance_base as salary
     , 0 as allowance
     , 0 as night_allowance
     , 0 as overtime_cost
     , 0 as expenses
     , 0 as employment_insurance
     , 0 as health_insurance 
     , 0 as expenses_conference     -- 会議費
     , 0 as expenses_entertainment  -- 交際費
     , 0 as expenses_travel         -- 旅費交通費
     , 0 as expenses_communication  -- 通信費
     , 0 as expenses_tax_dues       -- 租税公課
     , 0 as expenses_expendables    -- 消耗品
  from eb_bp_lump_contract lc
  left join eb_project p on p.id = lc.project_id
  left join eb_section s on s.id = p.department_id
  left join eb_subcontractor sc on sc.id = lc.company_id
  left join eb_bplumporder lo on lc.id = lo.contract_id
 where lc.is_deleted = 0
   and lc.status <> '04'
   and extract(year_month from(lc.end_date)) = get_ym()
