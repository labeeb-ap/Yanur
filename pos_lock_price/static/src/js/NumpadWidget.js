odoo.define('pos_lock_price.NumpadWidget', function(require) {
    'use strict';

    const NumpadWidget = require('point_of_sale.NumpadWidget');
    const Registries = require('point_of_sale.Registries');

    const LockPriceNumpadWidget = NumpadWidget => class extends NumpadWidget {
        get hasLockPrice() {
            return this.env.pos.config.lock_price;
        }
    };

    Registries.Component.extend(NumpadWidget, LockPriceNumpadWidget);

    return NumpadWidget;
 });
