odoo.define('aspl_pos_order_sync.PopupProductLines', function(require) {
    'use strict';

    const PosComponent = require('point_of_sale.PosComponent');
    const ProductScreen = require('point_of_sale.ProductScreen');
    const { useListener } = require('web.custom_hooks');
    const Registries = require('point_of_sale.Registries');
    const { useState, useRef } = owl.hooks;

    class PopupProductLines extends PosComponent {
        constructor() {
            super(...arguments);
            this.state = useState({ productQty : this.props.line.qty });
        }

        clickMinus(){
            if(this.props.line.qty == 1){
                return
            }else{
                this.props.line.qty -= 1
                this.state.productQty = this.props.line.qty;
            return this.props.line.qty;
            }
        }
        clickPlus(){
            this.props.line.qty += 1;
            this.state.productQty = this.props.line.qty;
            return this.props.line.qty;
        }

    }

    PopupProductLines.template = 'PopupProductLines';

    Registries.Component.add(PopupProductLines);

    return PopupProductLines;
});
