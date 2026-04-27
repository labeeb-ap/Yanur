odoo.define('aspl_pos_order_sync.OrderScreenButton', function(require) {
    'use strict';

    const PosComponent = require('point_of_sale.PosComponent');
    const ProductScreen = require('point_of_sale.ProductScreen');
    const { Gui } = require('point_of_sale.Gui');
    const { useListener } = require('web.custom_hooks');
    const Registries = require('point_of_sale.Registries');

    class OrderScreenButton extends PosComponent {
        constructor() {
            super(...arguments);
            useListener('click', this.onClick);
        }

        async onClick() {
              this.showScreen('OrderScreen');
        }
    }

    OrderScreenButton.template = 'OrderScreenButton';

    ProductScreen.addControlButton({
        component: OrderScreenButton,
        condition: function() {
            return this.env.pos.config.enable_order_sync;
        },
    });

    Registries.Component.add(OrderScreenButton);

    return OrderScreenButton;
});
