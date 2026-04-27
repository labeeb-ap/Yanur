odoo.define('cash_drawer_manager_validation.PasswordInputPopup', function(require) {
    'use strict';

    const { Gui } = require('point_of_sale.Gui');
    const {useState,useRef} = owl.hooks;
    const AbstractAwaitablePopup = require('point_of_sale.AbstractAwaitablePopup');
    const Registries = require('point_of_sale.Registries');
    const rpc = require('web.rpc');

    class PasswordInputPopup extends AbstractAwaitablePopup {
        constructor() {
            super(...arguments);
            this.state = useState({
                displayValue: '',
                realValue: '',
            });
            this.inputRef = useRef('textarea');
        }

        onInput(event) {
            const char = event.target.value.slice(-1);
            if(char==='*'){
                this.state.realValue = this.state.realValue.slice(0, -1);
                this.state.displayValue = this.state.displayValue.slice(0, -1);
            }else{
                this.state.realValue += char;
                this.state.displayValue += '*';
            }
            this.render();
        }

        getPayload() {
            return this.state.realValue;
        }

        async confirm_ref() {
            var payload = this.getPayload()
            if (payload) {
                    var manager = this.env.pos.drawer_manager.filter((obj) => obj.drawer_pin == payload);
                    if(manager.length>0){
                        var is_sale_cash_drawer = this.env.pos.config.is_sale_cash_drawer;
                        var ip_address = this.env.pos.config.ip_address;
                        var printer_name = this.env.pos.config.printer_name;
                        if (is_sale_cash_drawer){
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
                        }else{
                            this.showPopup('ErrorPopup', {
                                    title: this.env._t("Missing Configuration"),
                                    body: this.env._t("Cash Drawer Configuration is Not Set"),

                                });
                                return false;
                        }

                    }else{
                        this.showPopup('ErrorPopup', {
                                    title: this.env._t("INCORRECT"),
                                    body: this.env._t("Manager password is INCORRECT."),

                                });
                                return false;
                    }
                } else {
                    this.showPopup('ErrorPopup', {
                        title: this.env._t("Empty"),
                        body: this.env._t("Password Can't be Empty."),

                    });
                    return false;

                }
            this.trigger('close-popup', { confirmed: true, payload: this.getPayload() });
        }

        cancelPopup(){
            this.trigger('close-popup');
        }
    }
    PasswordInputPopup.template = 'PasswordInputPopup';
    PasswordInputPopup.defaultProps = {
        confirmText: 'Save',
        cancelText: 'Cancel',
        title: '',
        body: '',
        startingValue: '',
    };

    Registries.Component.add(PasswordInputPopup);

    return PasswordInputPopup;

});
