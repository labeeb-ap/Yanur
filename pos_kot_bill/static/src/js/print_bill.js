odoo.define('pos_kot_bill.print_bill', function(require) {
    "use strict";

    const PosComponent = require('point_of_sale.PosComponent');
    const ProductScreen = require('point_of_sale.ProductScreen')
    const { useListener } = require('web.custom_hooks');
    const Registries = require('point_of_sale.Registries');

    class KotBillButton extends PosComponent {
        constructor() {
            super(...arguments);
            useListener('click', this.onClick);
        }
        async onClick() {
            const order = this.env.pos.get_order();
            await this.showTempScreen('KotBillScreen');

        }
    };

    KotBillButton.template = 'KotBill'
    ProductScreen.addControlButton({
        component: KotBillButton,
        condition: function() {
            return this.env.pos.config.iface_kotbill;
        },
    });

    Registries.Component.add(KotBillButton);

    return KotBillButton;

});