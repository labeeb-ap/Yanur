odoo.define("pos_kot_bill.BackspaceCheck", function (require) {
    "use strict";

    const Registries = require("point_of_sale.Registries");
    const TicketScreen = require("point_of_sale.TicketScreen");
    const IndependentToOrderScreen = require('point_of_sale.IndependentToOrderScreen');
    const { useListener } = require('web.custom_hooks');
    const { posbus } = require('point_of_sale.utils');

    const TicketScreenEx = (TicketScreen) =>
        class extends TicketScreen {

            constructor() {
                super(...arguments);
            }

            async deleteOrder(order) {
                const screen = order.get_screen_data();
                if (['ProductScreen', 'PaymentScreen'].includes(screen.name) && order.get_orderlines().length > 0) {
                    const { confirmed } = await this.showPopup('ConfirmPopup', {
                        title: this.env._t('Existing orderlines'),
                        body: _.str.sprintf(
                          this.env._t('%s has a total amount of %s, are you sure you want to delete this order ?'),
                          order.name, this.getTotal(order)
                        ),
                    });
                    if (!confirmed){
                        return;
                    }else{
                        var orderLine = [];
                        var table_name = "";
                        var floor_name = "";
                        var is_kot = false;
                        order.get_orderlines().forEach(function(each){
                            if(each.kot_sent === true){
                                is_kot = true;
                            }
                            orderLine.push({ "id": each.product.id, "name": each.product.display_name, "quantity": each.quantity});
                        });
                        if(order.table){
                            table_name = order.table.name;
                            if(order.table.floor){
                                floor_name = order.table.floor.name
                            }
                        }
                        var order_data = {
                                "name" : order.name,
                                "table" : table_name,
                                "floor" : floor_name,
                                "lines" : orderLine,
                        };
                        if(is_kot===true){
                            localStorage.setItem('deleted_order', JSON.stringify(order_data));
                            const { confirmed, payload } = this.showPopup('CancelReasonPopup');
                        }
                    }
                }
                if (order) {
                    await this._canDeleteOrder(order);
                    order.destroy({ reason: 'abandon' });
                }
                posbus.trigger('order-deleted');
            }
        };
    Registries.Component.extend(TicketScreen, TicketScreenEx);
});