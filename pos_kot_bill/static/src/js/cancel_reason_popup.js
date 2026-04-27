odoo.define('pos_kot_bill.ReasonPopup', function(require) {
    'use strict';

    const {useState,useRef} = owl.hooks;
    const AbstractAwaitablePopup = require('point_of_sale.AbstractAwaitablePopup');
    const Registries = require('point_of_sale.Registries');

    class CancelReasonPopup extends AbstractAwaitablePopup {
        constructor() {
            super(...arguments);
            this.state = useState({
                inputValue: this.props.startingValue,
                customer: this.props.customer,
            });
            this.inputRef = useRef('textarea');
        }
        getPayload() {
            return this.state.inputValue
        }

        async confirm_ref() {
            const deleted_order = localStorage.getItem('deleted_order');
            var reason = this.getPayload();
            if(reason){
                var order_data = JSON.parse(deleted_order);
                var result = await this.rpc({
                        model: 'kot.canceled.order',
                        method: 'canceled_order_lines',
                        args: [order_data,reason],
                      });
                this.trigger('close-popup');
            }
        }

        _cancelAtEscape(event) {
            super._cancelAtEscape(event);
            if (event.key === 'Enter') {
                this.confirm();
            }

        }
    }

    CancelReasonPopup.template = 'CancelReasonPopup';
    CancelReasonPopup.defaultProps = {
        confirmText: 'Save',
        cancelText: 'Cancel',
        title: '',
        body: '',
        startingValue: '',
    };

    Registries.Component.add(CancelReasonPopup);

    return CancelReasonPopup;
});
