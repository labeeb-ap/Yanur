odoo.define('pos_cash_drawer.PaymentScreen', function(require) {
    'use strict';

    const PaymentScreen = require('point_of_sale.PaymentScreen')
    const PosComponent = require('point_of_sale.PosComponent');
    const Registries = require('point_of_sale.Registries');
    const { Gui } = require('point_of_sale.Gui');
    const { Component } = owl;
    const rpc = require('web.rpc');
    const models = require('point_of_sale.models');
    models.load_fields('pos.config', ['is_sale_cash_drawer','ip_address','printer_name']);
    models.load_fields('pos.payment.method', ['is_reference'])

    const PaymentScreenCashDrawer = PaymentScreen =>
        class extends PaymentScreen {
            constructor() {
                super(...arguments);
            }

            async _finalizeValidation() {
                var is_sale_cash_drawer = this.env.pos.config.is_sale_cash_drawer;
                var ip_address = this.env.pos.config.ip_address;
                var printer_name = this.env.pos.config.printer_name;
                var selected_method = this.currentOrder.selected_paymentline;
                if (selected_method.payment_method.is_reference === true){
                    const { confirmed, payload } = await this.showPopup('ReferenceCodePopup');
                    if (confirmed) {
                        selected_method.cardholder_name = payload;
                    } else {
                        return; // If the popup is cancelled, do not proceed with validation
                    }
                }
                if (is_sale_cash_drawer) {
                var paymentline = this.currentOrder.selected_paymentline;
                    if (paymentline.name ==='Cash'){
                        var data = {
                                    'ip_address': ip_address,
                                    'printer_name':printer_name
                                    };
                        try {
                            const response = await rpc.query({
                                model: 'pos.config',
                                method: 'cash_drawer_open',
                                args: [data],
                            });
                            console.log(response);
                        } catch (error) {
                            console.error(error);
                        }
                    }

                }
                await super._finalizeValidation()
            }

        };

    Registries.Component.extend(PaymentScreen, PaymentScreenCashDrawer);

    return PaymentScreen;
});
