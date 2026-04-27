from odoo import api, fields, models
import json
import requests
from datetime import datetime, timedelta
import logging

_logger = logging.getLogger(__name__)


class HrAttendance(models.Model):
    _inherit = 'hr.attendance'

    user_serial_num_check_in = fields.Integer(sting='Serial No. CheckIn')
    user_serial_num_check_out = fields.Integer(sting='Serial No. CheckOut')
    device_user_id = fields.Char(string='Biometric Device User ID')


class HrEmployee(models.Model):
    _inherit = 'hr.employee'

    device_id = fields.Char(string='Biometric Device ID')
    employee_type = fields.Selection([('migrant', 'MIGRANT'), ('resident', 'RESIDENT')], default="resident",
                                     string="Employee Type")


class HrAttendance(models.Model):
    _name = 'biometric.daily.attendance.hr'
    _description = 'Biometric Daily Attendance'

    def _default_employee(self):
        return self.env.user.employee_id

    employee_id = fields.Many2one('hr.employee', string="Employee", default=_default_employee, required=True,
                                  ondelete='cascade', index=True)
    check_in = fields.Char(string="Check In")
    check_out = fields.Char(string="Check Out")
    entry_id = fields.Integer(string="Machine No")
    company = fields.Many2one(string="Company",related='employee_id.company_id',store=True)
    date = fields.Date(string="Current Day")
    worked_hours = fields.Char(string='Worked Hours', compute='_compute_worked_hours', store=True, readonly=True)
    department = fields.Many2one(string="Department",related='employee_id.department_id',store=True)


    # def action_get_att(self):

    def action_get_att(self):
        _logger.info("Getting attendance data...")
        base_urls = []
        company = self.env.company.id
        biometric_data = self.env['biometric.settings'].sudo().search([('company_id', '=', company)])
        if biometric_data:
            ip_addres = biometric_data.biotime_ip
            biotime_token = biometric_data.biotime_token
            last_date_str = biometric_data.Last_date if biometric_data.Last_date else datetime.now()
            current_date = datetime.now()
            if last_date_str:
                last_date = datetime.strptime(last_date_str, '%Y-%m-%d')
                one_day = timedelta(days=1)
                while last_date <= current_date:
                    url = f'http://{ip_addres}/iclock/api/transactions/?start_time={last_date}'
                    base_urls.append(url)
                    last_date += one_day

            else:
                url = f'http://{ip_addres}/iclock/api/transactions/?start_time={current_date}'
                base_urls.append(url)
            biometric_data.Last_date = current_date.strftime('%Y-%m-%d')
            headers = {
                'Content-Type': 'application/json',
                'Authorization': biotime_token
            }

            payload = {}
            files = {}

            result = []

            for base_url in base_urls:
                response = requests.request("GET", base_url, headers=headers, data=payload, files=files)

                try:
                    result += [
                        {
                            "id": item["id"],
                            "emp_code": item["emp_code"],
                            "first_name": item["first_name"],
                            "last_name": item["last_name"],
                            "punch_time": item["punch_time"],
                            "punch_state_display": item["punch_state_display"],
                            "area_alias": item["area_alias"]
                        }
                        for item in response.json()["data"]
                    ]
                except requests.exceptions.HTTPError as e:
                    _logger.error("Error retrieving attendance data: %s", e)
                except json.JSONDecodeError as e:
                    _logger.error("Error decoding JSON response: %s", e)
            # self.over_out = result
            result.sort(key=lambda x: x["id"])
            for entry in result:
                date = entry['punch_time'][:10]
                emp_id = self.env['hr.employee'].search([('device_id', '=', entry['emp_code'])])

                if emp_id:

                    # if date == current_date or date == previous_date:
                    if entry['punch_state_display'] == 'Check In':
                        attendance_vals = {
                            'employee_id': emp_id.id,
                            'company': company,
                            'date': date,
                            'check_in': entry['punch_time'],
                            'entry_id': entry['id'],
                        }


                        existing_attendance = self.env['biometric.daily.attendance.hr'].search([
                            ('entry_id', '=', entry['id']),
                        ])

                        if existing_attendance:
                            existing_attendance.write(attendance_vals)
                        else:
                            self.env['biometric.daily.attendance.hr'].create(attendance_vals)

                    elif entry['punch_state_display'] == 'Check Out':

                        attendance_vals = {
                            'check_out': entry['punch_time']
                        }
                        existing_attendance = self.env['biometric.daily.attendance.hr'].search([
                            ('employee_id', '=', emp_id.id),
                            ('date', '=', date),
                            ('entry_id', '<=', entry['id']),
                            ('check_out', '=', False)
                        ], order='check_in desc', limit=1)

                        if existing_attendance:
                            closest_check_in = self.env['biometric.daily.attendance.hr'].search([
                                ('employee_id', '=', emp_id.id),
                                ('date', '=', date),
                                ('entry_id', '<', entry['id']),
                            ], order='check_in desc', limit=1)
                            if closest_check_in:
                                existing_attendance.write(attendance_vals)

        # except requests.exceptions.HTTPError as e:
        #     _logger.error("Error retrieving attendance data: %s", e)
        #     return None
        # except json.JSONDecodeError as e:
        #     _logger.error("Error decoding JSON response: %s", e)
        #     return None

    @api.depends('check_in', 'check_out')
    def _compute_worked_hours(self):
        for attendance in self:
            if attendance.check_out and attendance.check_in:
                check_out_dt = datetime.strptime(attendance.check_out, '%Y-%m-%d %H:%M:%S')
                check_in_dt = datetime.strptime(attendance.check_in, '%Y-%m-%d %H:%M:%S')
                duration = check_out_dt - check_in_dt

                days = duration.days
                hours = duration.seconds // 3600
                minutes = (duration.seconds // 60) % 60
                seconds = duration.seconds % 60
                days_in_hrs = days * 24
                total_hours = hours + days_in_hrs
                worked_hours = "{}.{:02d}".format(total_hours, minutes)
                # print("Duration:{}:{}:{}".format(total_hours, minutes, seconds))
                # delta = check_out_dt - check_in_dt
                attendance.worked_hours = float(worked_hours)
            else:
                attendance.worked_hours = False



