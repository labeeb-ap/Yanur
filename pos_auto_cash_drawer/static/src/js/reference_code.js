odoo.define('pos_auto_cash_drawer.ReferenceCodePopup', function(require) {
    'use strict';

    const {useState,useRef} = owl.hooks;
    const AbstractAwaitablePopup = require('point_of_sale.AbstractAwaitablePopup');
    const Registries = require('point_of_sale.Registries');

    class ReferenceCodePopup extends AbstractAwaitablePopup {
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

        async confirmPrint() {
            this.props.resolve({
                confirmed: true,
                payload: await this.getPayload(),
                print: true
            });
            this.trigger('close-popup');
        }

        _cancelAtEscape(event) {
            super._cancelAtEscape(event);
            if (event.key === 'Enter') {
                this.confirm();
            }

        }
    }

    ReferenceCodePopup.template = 'ReferenceCodePopup';
    ReferenceCodePopup.defaultProps = {
        confirmText: 'Save',
        cancelText: 'Cancel',
        title: '',
        body: '',
        startingValue: '',
    };

    Registries.Component.add(ReferenceCodePopup);

    return ReferenceCodePopup;
});
