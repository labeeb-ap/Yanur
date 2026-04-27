odoo.define('aspl_pos_order_sync.NumpadWidget', function (require) {
    'use strict';

    const NumpadWidget = require('point_of_sale.NumpadWidget');
    const Registries = require('point_of_sale.Registries');

    const NumpadWidgetInh = (NumpadWidget) =>
        class extends NumpadWidget {
            constructor() {
                super(...arguments);
            }

            changeMode(mode) {
                if (!this.hasPriceControlRights && mode === 'price') {
                    return;
                }
                if (!this.hasManualDiscount && mode === 'discount') {
                    return;
                }
                if(this.env.pos.config.enable_operation_restrict){
                    if (!this.env.pos.user.can_change_price && mode === 'price') {
                        return;
                    }
                    if (!this.env.pos.user.can_give_discount && mode === 'discount') {
                        return;
                    }
                }
                this.trigger('set-numpad-mode', { mode });
            }

        };

    Registries.Component.extend(NumpadWidget, NumpadWidgetInh);

    return NumpadWidget;
});
