from odoo import fields, models,api
import requests
from io import BytesIO
import base64
import tempfile
import pytz
from datetime import datetime
from reportlab.pdfgen import canvas
import os

# from selenium import webdriver
# from selenium.webdriver.common.keys import Keys
# from selenium.webdriver.common.action_chains import ActionChain



class PosConfig(models.Model):
    _inherit = 'pos.config'

    iface_kotbill = fields.Boolean(string='Kitchen Order Printing', help='Enables Kitchen Order Printing in the Point of Sale')
    fileout = fields.Binary('File')
    fileout_filename = fields.Char('Filename')
    ip_address = fields.Char(string='IP Address')

    @staticmethod
    def create_pdf(receipt_number, floor,table, employee_name,products):
        # Create a new PDF file
        pdf_file = tempfile.NamedTemporaryFile(delete=False)
        pdf_path = pdf_file.name
        brunei_timezone = pytz.timezone('Asia/Brunei')
        current_date_time = datetime.now(brunei_timezone)
        current_time = current_date_time.strftime('%d-%m-%Y %H:%M:%S')
 
        if floor == None:
            floor = "Ground"

        # Generate the receipt using ReportLab
        c = canvas.Canvas(pdf_path)
        c.setFont("Helvetica", 25)
        c.drawString(100, 800, "Receipt Number: {}".format(receipt_number))
        c.drawString(100, 750, "Time: {}".format(current_time))
        c.setFont("Helvetica-Bold", 30)
        c.drawString(100, 700, "Table: {}".format(table))
        c.setFont("Helvetica", 25)
        c.drawString(100, 650, "Floor: {}".format(floor))
        c.drawString(100, 600, "Employee Name: {}".format(employee_name))
        y = 550
        for product, quantity, note in products:
            c.setFont("Helvetica-Bold", 20)
            c.drawString(110, y, "- {}: {}".format(product, quantity))
            c.drawString(110, y - 25, "{}".format(note))
            y -= 50  # Move down to the next line

        c.save()

        # Return the path to the new PDF file
        return pdf_path

    @api.model
    def current_kot_print(self, data):
        # Get the receipt information
        receipt_number = data['receipt_number']
        floor = data['floor']
        table = data['table']
        session = data['session']
        employee_name = data['employee_name']
        orderlines = data['orderlines']
        category_dict = {}
        parent_category_dict = {}
        printer_dict = {}
        printer_name = 0
        for item in orderlines:
            product = item[0]
            quantity = item[1]
            pos_category_name = item[2]
            note = item[3]
            category_id = item[4]

            pdt_categ_id = self.env['pos.category'].search([('id', '=', category_id)])
            items = self.env['pos.printer'].search([('category_ids', 'in', category_id)])
            parent_cat = pdt_categ_id.parent_id.name
            for item in items:
                printer_dict[parent_cat] = item.printer_name
                receipt_printer = item.billing_printer

            if parent_cat in parent_category_dict:
                parent_category_dict[parent_cat].append((product, quantity,note))
            else:
                parent_category_dict[parent_cat] = [(product, quantity,note)]

        for parent_cat, products in parent_category_dict.items():
            if parent_cat in printer_dict:
                printer_name = printer_dict[parent_cat]
            else:
                printer_name = 0

            if (printer_name != 0):
                for count in range(2):
                    pdf_path = self.create_pdf(receipt_number, floor, table, employee_name,products)
                    pos_session = self.env['pos.session'].browse(session)
                    # url = "http://%s/print/from-pdf", % pos_config.ip_address
                    url = "http://{}/print/from-pdf".format(pos_session.config_id.ip_address)
                    files = [('PdfFile', ('Odoo1111.pdf', open(pdf_path, 'rb'), 'application/pdf'))]
                    if count == 0:
                        payload = {'PrinterPath': printer_name, 'Copies': '1'}
                    else:
                        payload = {'PrinterPath': receipt_printer, 'Copies': '1'}
                    headers = {}

                    response = requests.request("POST", url, headers=headers, data=payload, files=files)

        return {'result': 'success'}




