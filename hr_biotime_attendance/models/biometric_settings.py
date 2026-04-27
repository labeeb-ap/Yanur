from odoo import api, fields, models
import json
import re
import requests
from datetime import datetime, timedelta, timezone
import logging
from dateutil import tz

_logger = logging.getLogger(__name__)


class Biometric_Settings(models.Model):
    _name = 'biometric.settings'
    _description = 'Biometric Settings'
    _rec_name = 'name'

    biotime_ip = fields.Char(String="IP Address")
    biotime_token = fields.Char(String="Token")
    Last_date = fields.Char(String="Last Updated Date")
    last_fetch_date = fields.Date('Last Fetch Date', default=lambda self: fields.Date.today(),
                                  help='To fetch values from the given date')
    last_fetch_date_time = fields.Datetime('Last Fetch Date & Time', default=lambda self: fields.Datetime.now(),
                                           help='To fetch values from the given date')
    name = fields.Char(string='Login Name')
    password = fields.Char(string='Login Password')
    company_id = fields.Many2one('res.company', string='Company', default=lambda self: self.env.company.id)

    # Login
    def biometric_login(self):
        api_key = self.biotime_token
        ip_address = self.biotime_ip
        name = self.name
        password = self.password

        url = f"{ip_address}/login"
        headers = {
            "x-api-key": api_key,
            "Content-Type": "application/json"
        }
        payload = {
            "name": name,
            "password": password
        }
        response = requests.post(url, json=payload, headers=headers)
        response.raise_for_status()
        token = response.json().get("token")
        return token

    # Get all attendance
    def get_all_attendance(self, token):
        api_key = self.biotime_token
        ip_address = self.biotime_ip
        url = f"{ip_address}/attendance"
        headers = {
            "x-api-key": api_key,
            "Authorization": f"Bearer {token}"
        }
        response = requests.get(url, headers=headers)
        response.raise_for_status()
        return response.json()

    # Get attendance by date range
    def get_attendance_by_date_range(self, token, start_date, end_date):
        api_key = self.biotime_token
        ip_address = self.biotime_ip
        url = f"{ip_address}/attendanceByDateRange"
        headers = {
            "x-api-key": api_key,
            "Authorization": f"Bearer {token}"
        }
        params = {
            "startDate": start_date,
            "endDate": end_date
        }
        response = requests.get(url, headers=headers, params=params)
        response.raise_for_status()
        return response.json()

    def parse_record_time(self, time):
        date_str = re.sub(r'\s*\(.*?\)', '', time)
        date_str = re.sub(r'GMT([+-]\d{4})', r'\1', date_str)
        dt = datetime.strptime(date_str, '%a %b %d %Y %H:%M:%S %z')

        return dt.astimezone(tz.UTC).replace(tzinfo=None)

    def create_attendance(self, time, employee_id, sn):
        values = {
            'employee_id': employee_id,
            'check_in': time,
            'user_serial_num_check_in': sn
        }
        return self.env['hr.attendance'].sudo().create(values)

    def update_attendance(self, time, sn, attendance):
        values = {
            'check_out': time,
            'user_serial_num_check_out': sn
        }
        return attendance.sudo().write(values)

    def action_get_attendance_cron(self):
        for rec in self.env['biometric.settings'].sudo().search([]):
            start_date = str(rec.last_fetch_date)
            end_date = str(fields.Date.today())

            try:
                token = rec.biometric_login()

                # Use this to fetch all attendance records.
                # all_attendance = rec.get_all_attendance(token)

                attendance_range = rec.get_attendance_by_date_range(token, start_date, end_date)
                for att in attendance_range['attendance']:
                    sn = att['userSn']
                    emp_id = att['deviceUserId']
                    employee_id = self.env['hr.employee'].sudo().search([('device_id', '=', emp_id)])
                    if not employee_id:
                        _logger.warning(f"Skipping: No employee found with device_id={emp_id}")
                        continue
                    check_out_sn = self.env['hr.attendance'].sudo().search([]).mapped('user_serial_num_check_out')
                    check_in_sn = self.env['hr.attendance'].sudo().search([]).mapped('user_serial_num_check_in')
                    if int(sn) in check_in_sn or int(sn) in check_out_sn:
                        _logger.info(f"Skipping: userSn: {sn} already exists.")
                        continue
                    dt_time = att['recordTime']
                    time = rec.parse_record_time(dt_time)
                    attendance = self.env['hr.attendance'].sudo().search(
                        [('employee_id', '=', employee_id.id), ('check_in', '!=', time), ('check_out', '=', False),
                         ('user_serial_num_check_out', '=', False), ('user_serial_num_check_in', '!=', sn)])
                    if attendance:
                        rec.update_attendance(time, sn, attendance)
                    else:
                        rec.create_attendance(time, employee_id.id, sn)
                rec.last_fetch_date = fields.Date.today()

            except requests.exceptions.RequestException as e:
                _logger.exception("API request failed: %s", str(e))

