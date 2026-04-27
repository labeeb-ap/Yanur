odoo.define('pos_kot_bill.KotBillScreen', function (require) {
    'use strict';

    const ReceiptScreen = require('point_of_sale.ReceiptScreen');
    const Registries = require('point_of_sale.Registries');

    const KotBillScreen = (ReceiptScreen) => {
        class KotBillScreen extends ReceiptScreen {
            confirm() {
                this.currentOrder.kot_bill_saved_resume = this.currentOrder.kot_bill_build_line_resume()
                this.currentOrder.orderlines.each(function(line) {
                    line.kot_set_dirty(true);
                });
                this.props.resolve({ confirmed: true, payload: null });
                this.trigger('close-temp-screen');
            }
            whenClosing() {
                this.trigger('close-temp-screen');
            }
            get receipt() {
                return this.currentOrder.getOrderReceiptEnv().receipt;
            }
            get changes(){
                return this.currentOrder.compute_Changes();
            }
            /**
             * @override
             */
          async printReceiptKot() {

              var order = this.currentOrder;
              var new_ord = order.compute_Changes().new;
              if (!new_ord.length) {
                    this.showPopup('ErrorPopup', {
                        title: this.env._t('No New Order'),
                        body: this.env._t('No pending orders found.'),
                    });
                    return;
                }

              var data = {
                'receipt_number': order.name,
                'table':order.table ? order.table.name : null,
                'session':order.pos_session_id,
                'floor': order.pos.floor ? order.pos.floor.name : null,
                'employee_name': order.employee ? order.employee.name : null,
                'employee_role': order.employee.role ? order.employee.role : null,
                'orderlines': [],
              };
              for (const [key, value] of Object.entries(new_ord[0])) {
                  var product_cat = key;
                  if (Array.isArray(value)) {
                    value.forEach(item => {
                      var product_name = item.name;
                      var note = item.note;
                      var quantity = item.qty;
                      var categ_id = null;
                      order.orderlines.each(function(ol) {
                        ol.kot_qty = ol.quantity;
                        ol.kot_sent = true;
                        if (ol.product.display_name === product_name) {
                          categ_id = ol.product.pos_categ_id[0];
                        }
                      });
                      data.orderlines.push([product_name, quantity, product_cat, note || '',categ_id]);
                    });
                  }
                }


              var result = await this.rpc({
                model: 'pos.config',
                method: 'current_kot_print',
                args: [data],
              });

              this.currentOrder.kot_bill_saved_resume = this.currentOrder.kot_bill_build_line_resume()
                this.currentOrder.orderlines.each(function(line) {
                    line.kot_set_dirty(true);
                });
                this.props.resolve({ confirmed: true, payload: null });
               this.showPopup('ConfirmPopup', {
                    title: this.env._t('Success'),
                    body: this.env._t('KOT printed successfully.'),
                });
            }

        }
        KotBillScreen.template = 'KotBillScreen';
        return KotBillScreen;
    };

    Registries.Component.addByExtending(KotBillScreen, ReceiptScreen);

    return KotBillScreen;
});
