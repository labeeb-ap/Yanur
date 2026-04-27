odoo.define("cash_drawer_manager_validation.CashDrawerButton", function (require) {
    "use strict";

    const PosComponent = require("point_of_sale.PosComponent");
    const ProductScreen = require("point_of_sale.ProductScreen");
    const {useListener} = require("web.custom_hooks");
    const Registries = require("point_of_sale.Registries");
    const { Gui } = require('point_of_sale.Gui');
    const { Component } = owl;
    const rpc = require('web.rpc');
    const models = require('point_of_sale.models');
    models.load_models({
		model: 'cash.drawer.settings',
		fields: ['employee','drawer_pin'],
		domain: null,
		loaded: function(self, drawer_manager) {
			self.drawer_manager = drawer_manager;
		},
	});

    class CashDrawerButton extends PosComponent {
        constructor() {
            super(...arguments);
            useListener("click", this.onClick);
        }
        async onClick() {
            const {
                        confirmed,
                        payload
                    } = await this.showPopup('PasswordInputPopup', {
                        title: this.env._t('Enter Password'),
                    });
        }
    }
    CashDrawerButton.template = "CashDrawerButton";

    ProductScreen.addControlButton({
        component: CashDrawerButton,
        condition: function () {
            return true;
        },
    });

    Registries.Component.add(CashDrawerButton);

    return CashDrawerButton;
});
