odoo.define('pos_kot_bill.Kitchen_Recipt_Screen', function(require) {
    'use strict';

    const PosComponent = require('point_of_sale.PosComponent');
    const Registries = require('point_of_sale.Registries');

    class Kitchen_Recipt_Screen extends PosComponent {
        constructor() {
            super(...arguments);
            this._receiptEnv = this.props.order.getOrderReceiptEnv();
        }
        willUpdateProps(nextProps) {
            this._receiptEnv = nextProps.order.getOrderReceiptEnv();
        }
        get receipt() {
            return this.receiptEnv.receipt;
        }
        get receiptEnv () {
          return this._receiptEnv;
        }
        get session() {
            return this.env.pos
        }
        get changes(){
            return this.props.changes_value;
        }
        get category(){
            return this.props.categ;
        }
        get change_type(){
            return this.props.change_type;
        }
    }
    Kitchen_Recipt_Screen.template = 'KOTRecipt';

    Registries.Component.add(Kitchen_Recipt_Screen);

    return Kitchen_Recipt_Screen

});
