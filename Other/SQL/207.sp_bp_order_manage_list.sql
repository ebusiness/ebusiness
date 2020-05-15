delimiter //

DROP PROCEDURE IF EXISTS sp_bp_order_manage_list //

CREATE PROCEDURE sp_bp_order_manage_list(
    in_year char(4),
    in_month char(2)
)
BEGIN

select distinct m.id as member_id
     , m.employee_id
     , concat(m.first_name, ' ', m.last_name) as full_name
     , department.name as department_name
     , s.name as company_name
     , '0' as endowment_insurance
     , '他社技術者' as member_type_name
     , pm.project_id
     , p.name as project_name
     , p.is_lump
     , p.nearest_station
     , cli.name as client_name
     , c.allowance_time_min as min_hours
     , c.allowance_time_max as max_hours
     , (c.allowance_base + c.allowance_other) as base_amount
     , cfg.value as attendance_type
     , ma.id as attendance_id
     , ma.total_hours as real_total_hours
     , ma.total_days as real_total_days
     , srd.id as request_detail_id
     , srd.min_hours as real_min_hours
     , srd.max_hours as real_max_hours
     , srd.total_price as real_turnover_amount
     , cfg.value as real_attendance_type
  from eb_member m
  join eb_bp_contract c on c.is_deleted = 0
                       and c.member_id = m.id
                       and c.start_date <= last_day(concat(in_year, '-', in_month, '-01'))
                       and ifnull(c.end_date, '9999-12-31') >= concat(in_year, '-', in_month, '-01')
  join eb_subcontractor s on s.id = c.company_id
  left join eb_membersectionperiod msp on msp.is_deleted = 0
                                      and msp.member_id = m.id
                                      and msp.start_date <= last_day(concat(in_year, '-', in_month, '-01'))
                                      and ifnull(msp.end_date, '9999-12-31') >= concat(in_year, '-', in_month, '-01')
  left join eb_section department on department.is_deleted = 0
                                 and department.id = msp.section_id
  left join eb_projectmember pm on pm.is_deleted = 0
                               and pm.status = 2
                               and pm.member_id = m.id
                               and pm.start_date <= last_day(concat(in_year, '-', in_month, '-01'))
                               and ifnull(pm.end_date, '9999-12-31') >= concat(in_year, '-', in_month, '-01')
  left join eb_project p on p.is_deleted = 0
                        and p.is_reserve = 0
                        and p.id = pm.project_id
  left join eb_client cli on cli.id = p.client_id
  left join mst_config cfg on cfg.group = 'system' and cfg.name = 'bp_attendance_type'
  left join eb_memberattendance ma on ma.is_deleted = 0
                                  and ma.project_member_id = pm.id
                                  and ma.year = in_year
                                  and ma.month = in_month
  left join eb_subcontractorrequestdetail srd on srd.project_member_id = pm.id
                                             and exists (
                                                 select 1 from eb_subcontractorrequest s1
                                                  where s1.id = srd.subcontractor_request_id
                                                    and s1.year = in_year
                                                    and s1.month = in_month
                                             )
;

END