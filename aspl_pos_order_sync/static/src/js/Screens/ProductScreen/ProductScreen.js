odoo.define('aspl_pos_order_sync.ProductScreen', function (require) {
    'use strict';

    const ProductScreen = require('point_of_sale.ProductScreen');
    const Registries = require('point_of_sale.Registries');
    const { useListener } = require('web.custom_hooks');
    const { useState, useRef } = owl.hooks;
    var rpc = require('web.rpc');

    const ProductScreenInherit = (ProductScreen) =>
        class extends ProductScreen {
            constructor() {
                super(...arguments);
                useListener('close-draft-screen', this.closeScreen);
            }

            closeScreen(){
                this.trigger('show-orders-panel');
            }

            async _onClickPay() {
                if(this.env.pos.user.pos_user_type === "salesman" && this.env.pos.config.enable_order_sync){
                    let currentOrder = this.env.pos.get_order();
                    var order_str =  currentOrder.get_is_modified_order() ? " Modify " : " Create Draft ";
                    const { confirmed } = await this.showPopup('CreateDraftOrderPopup', {
                        title: this.env._t('Draft Order'),
                        body: this.env._t('Do You Want To' + order_str +'Order?'),
                    });
                    if (confirmed){
                        this.env.pos.get_order().set_salesman_id(this.env.pos.user.id);
                        this.env.pos.push_orders(this.env.pos.get_order(), {'draft':true});
                        this.showScreen('ReceiptScreen');
                    }
                }else{
                    this.showScreen('PaymentScreen');
                }
            }

            async _setValue(val) {
                var discount_limit = this.env.pos.user.discount_limit;
                var managers = this.env.pos.config.pos_managers_ids;
                if(this.env.pos.config.enable_operation_restrict){
                    if(this.state.numpadMode === 'discount'){
                        if(val > discount_limit){
                            if(_.contains(managers,this.env.pos.user.id)){
                                this.currentOrder.get_selected_orderline().set_discount(val);
                                return;
                            }
                            if(managers.length > 0){
                                const { confirmed,payload: enteredPin } = await this.showPopup('AuthenticationPopup', {
                                    title: this.env._t('Authentication'),
                                });
                                if(confirmed){
                                    const userFiltered = this.env.pos.users.filter(user => managers.includes(user.id));
                                    var result_find = _.find(userFiltered, function (user) {
                                        return user.custom_security_pin === enteredPin || user.barcode === enteredPin;
                                    });
                                    if(result_find){
                                        this.currentOrder.get_selected_orderline().set_discount(val);
                                        return;
                                    }else{
                                        alert('Please Enter correct PIN/Barcode!');
                                        return;
                                    }
                                }
                            }else{
                                alert('Please Contact Your Manager!!')
                                return;
                            }
                        }
                    }
                }
                super._setValue(val);
            }

            quick_delete(order_id){
                var self = this;
                var order_to_be_remove = self.env.pos.db.get_orders_list_by_id(order_id);
                if (order_to_be_remove) {
                    var params = {
                        model: 'pos.order',
                        method: 'unlink',
                        args: [order_to_be_remove.id],
                    }
                    rpc.query(params, {async: false}).then(function(result){});
                }
                var orders_list = self.env.pos.db.get_orders_list();
                orders_list = _.without(orders_list, _.findWhere(orders_list, { id: order_to_be_remove.id }));
                var orderFiltered = orders_list.filter(order => order.state == "draft");
                self.env.pos.db.add_orders(orders_list);
                self.env.pos.db.add_draft_orders(orderFiltered);
                this.trigger('reload-order-count',{ orders_count:orderFiltered.length});
                self.render();
            }

            async quick_pay(order_id){
                var self = this;
                var result = self.env.pos.db.get_orders_list_by_id(order_id);
                if(result && result.lines.length > 0){
                    var selectedOrder = this.env.pos.get_order();
                    selectedOrder.destroy();
                    var selectedOrder = this.env.pos.get_order();
                    if (result.partner_id && result.partner_id[0]) {
                        var partner = self.env.pos.db.get_partner_by_id(result.partner_id[0])
                        if(partner){
                            selectedOrder.set_client(partner);
                        }
                    }
                    selectedOrder.set_pos_reference(result.pos_reference);
                    selectedOrder.set_order_id(order_id);
                    selectedOrder.server_id = result.id;

                    selectedOrder.set_sequence(result.name);
                    if(result.salesman_id && result.salesman_id[0]){
                        selectedOrder.set_salesman_id(result.salesman_id[0]);
                    }
                    var order_lines = await self.get_orderlines_from_order(result.lines);
                    if(order_lines && order_lines.length > 0){
                        let draftPackLotLines = {};
                        for(var i=0; i< order_lines.length;i++){
                            var line = order_lines[i];
                            var product = self.env.pos.db.get_product_by_id(Number(line.product_id[0]));
                            if(line.pack_lot_ids && line.pack_lot_ids.length > 0){
                                draftPackLotLines = await self.env.pos.db.get_serial_lot_product(line.pack_lot_ids);
                                selectedOrder.add_product(product, {
                                    draftPackLotLines,
                                    quantity: line.qty,
                                    discount: line.discount,
                                    price: line.price_unit,
                                });
                            } else {
                                selectedOrder.add_product(product, {
                                    quantity: line.qty,
                                    discount: line.discount,
                                    price: line.price_unit,
                                });
                            }
                        }
                        self.trigger('show-orders-panel');
                        self.showScreen('PaymentScreen',{'order_id':order_id});
                    }
                }
            }

            get_orderlines_from_order(line_ids){
                return this.rpc({
                    model: 'pos.order.line',
                    method: 'search_read',
                    domain: [['id', 'in', line_ids]],
                })
            }
        };

    Registries.Component.extend(ProductScreen, ProductScreenInherit);

    return ProductScreen;
});
