odoo.define('aspl_pos_order_sync.ReOrderPopupSync', function(require) {
    'use strict';

    const { useState, useRef } = owl.hooks;
    const AbstractAwaitablePopup = require('point_of_sale.AbstractAwaitablePopup');
    const Registries = require('point_of_sale.Registries');
    const { useListener } = require('web.custom_hooks');

    // formerly ConfirmPopupWidget
    class ReOrderPopupSync extends AbstractAwaitablePopup {
        constructor() {
            super(...arguments);
            this.state = useState({ OrderLines : this.props.orderlines });
            this.state.OrderLines = this.props.orderlines;
            useListener('delete-popup-orderline', () => this._deletePopupOrderline(event));
        }

        getPayload() {
            return this.state.OrderLines;
        }

        cancel() {
            this.trigger('close-popup');
        }

        _deletePopupOrderline(event){
            let orderlines = this.props.orderlines;
            var removeIndex = orderlines.map(function(item) { return item.id; }).indexOf(event.detail.orderline_id);
            orderlines.splice(removeIndex, 1);
            this.state.OrderLines = orderlines;
            this.render();
        }

    }

    ReOrderPopupSync.template = 'ReOrderPopupSync';

    ReOrderPopupSync.defaultProps = {
        confirmText: 'Re-Order',
        cancelText: 'Close',
        title: '',
        body: '',
    };

    Registries.Component.add(ReOrderPopupSync);

    return ReOrderPopupSync;
});
