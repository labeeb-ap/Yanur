odoo.define('aspl_pos_order_sync.models', function (require) {
"use strict";

    var models = require('point_of_sale.models');
    var core = require('web.core');
    const Registries = require('point_of_sale.Registries');
    var rpc = require('web.rpc');
    var _t = core._t;
    var utils = require('web.utils');
    var round_pr = utils.round_precision;


    models.load_fields("res.users", ['based_on','can_give_discount','can_change_price','custom_security_pin',
    'discount_limit','pos_user_type','sales_persons','barcode']);

    var _super_Order = models.Order.prototype;
    models.Order = models.Order.extend({
        initialize: function(attr, options){
            _super_Order.initialize.call(this,attr,options);
        },
        set_salesman_id: function(salesman_id){
            this.set('salesman_id',salesman_id);
        },
        get_salesman_id: function(){
            return this.get('salesman_id');
        },
        set_is_modified_order:function(flag){
            this.set('flag', flag);
        },
        get_is_modified_order:function(){
            return this.get('flag');
        },
        set_pos_reference: function(pos_reference) {
            this.set('pos_reference', pos_reference)
        },
        get_pos_reference: function() {
            return this.get('pos_reference')
        },
        set_order_id: function(order_id){
            this.set('order_id', order_id);
        },
        get_order_id: function(){
            return this.get('order_id');
        },
        set_sequence:function(sequence){
            this.set('sequence',sequence);
        },
        get_sequence:function(){
            return this.get('sequence');
        },
        set_journal: function(statement_ids) {
            this.set('paymentlines', statement_ids)
        },
        get_journal: function() {
            return this.get('paymentlines');
        },
        set_amount_return: function(amount_return) {
            this.set('amount_return', amount_return);
        },
        get_amount_return: function() {
            return this.get('amount_return');
        },
        set_date_order: function(date_order) {
            this.set('date_order', date_order);
        },
        get_date_order: function() {
            return this.get('date_order');
        },
        get_change: function(paymentLine) {
            if(this.get_order_id()){
                let change = 0.0;
                if (!paymentLine) {
                    if(this.get_total_paid() > 0){
                        change = this.get_total_paid() - this.get_total_with_tax();
                    }else{
                        change = this.get_amount_return();
                    }
                }else {
                    change = -this.get_total_with_tax();
                    var orderPaymentLines  = this.pos.get_order().get_paymentlines();
                    for (let i = 0; i < orderPaymentLines.length; i++) {
                        change += orderPaymentLines[i].get_amount();
                        if (orderPaymentLines[i] === paymentLine) {
                            break;
                        }
                    }
                }
                return round_pr(Math.max(0,change), this.pos.currency.rounding);
            } else {
                return _super_Order.get_change.call(this, orderPaymentLines);
            }
        },

        export_as_JSON: function(){
            var orders = _super_Order.export_as_JSON.call(this);
            orders.salesman_id = this.get_salesman_id() || this.pos.user.id;
            orders.old_order_id = this.get_order_id();
            orders.sequence = this.get_sequence();
            orders.pos_reference = this.get_pos_reference();
            orders.cashier_id = this.pos.user.id;
            return orders;
        },
    });

    var _posModelSuper = models.PosModel;
    models.PosModel = models.PosModel.extend({
        set_cashier: function(employee){
            var self = this;
            _posModelSuper.prototype.set_cashier.apply(this, arguments);
            if(self.env.pos.user){
                let current_user = self.env.pos.user;
                employee['based_on'] = current_user['based_on'];
                employee['can_change_price'] = current_user.can_change_price;
                employee['can_give_discount'] = current_user.can_give_discount;
                employee['company_id'] = current_user.company_id;
                employee['pos_user_type'] = current_user.pos_user_type;
                employee['discount_limit'] = current_user.discount_limit;
                employee['barcode'] = current_user.barcode;
                employee['custom_security_pin'] = current_user.custom_security_pin;
                employee['sales_persons'] = current_user.sales_persons;
            }
            this.set('cashier', employee);
            this.env.pos.db.set_cashier(this.get('cashier'));

            if(self.env.pos.config.enable_order_sync && employee){
                var from = moment(new Date()).format('YYYY-MM-DD')+" 00:00:00";
                var to = moment(new Date()).format('YYYY-MM-DD HH:mm:ss');
                var domain = [['date_order','>=',from], ['date_order', '<=', to]];

                if(this.get_cashier().pos_user_type === "salesman"){
                    domain.push(['salesman_id', '=', self.get_cashier().user_id[0]]);
                }else if(this.get_cashier().pos_user_type=="cashier") {
                    if(this.get_cashier().sales_persons){
                       let user_ids = this.get_cashier().sales_persons;
                       user_ids.push(self.get_cashier().user_id[0]);
                       domain.push(['salesman_id', 'in', user_ids]);
                    } else {
                        domain.push(['salesman_id', '=', self.get_cashier().user_id[0]]);
                    }
                }

                rpc.query({model: 'pos.order',
                    method: 'search_read',
                    domain: domain,
                }, {async: false}).then(function(orders){
                    self.env.pos.db.add_orders(orders);
                    const orderFiltered = orders.filter(order => order.state == "draft");
                    self.env.pos.db.add_draft_orders(orderFiltered);
                    self.set_orderCount(orderFiltered.length);
                });
            }
        },
        set_orderCount: function(count){
            this.orderCount = count;
        },
        get_orderCount: function(count){
            return this.orderCount;
        },

        get_cashier: function(){
            return this.db.get_cashier() || this.get('cashier');
        },

        _save_to_server: function (orders, options) {
            var self = this;
            var res = _posModelSuper.prototype._save_to_server.apply(this, arguments);
            res.then(function(server_ids){
                if(server_ids.length > 0  && self.config.enable_order_sync){
                    var s_id = _.pluck(server_ids, 'id');
                    var params = {
                        model: 'pos.order',
                        method: 'search_read',
                        domain: [['id','in', s_id]],
                        fields: [],
                    }
                    rpc.query(params, {async: false}).then(function(orders){
                        if(orders.length > 0){
                            _.each(orders,function(order){
                                var exist_order = _.findWhere(self.db.get_orders_list(), {'pos_reference': order.pos_reference})
                                var exist_draft_order = _.findWhere(self.db.get_draft_orders_list(), {'pos_reference': order.pos_reference})
                                if(exist_order || exist_draft_order){
                                    _.extend(exist_order,order);
                                    _.extend(exist_draft_order,order);
                                } else{
                                    self.db.orders_list.push(order);
                                    self.db.draft_orders_list.push(order);
                                }
                                var new_order = _.sortBy(self.db.get_orders_list(), 'id').reverse();
                                var new_draft_order = _.sortBy(self.db.get_draft_orders_list(), 'id').reverse();
                                self.db.add_orders(new_order);
                                self.db.add_draft_orders(new_draft_order);
                            })
                        }
                    });
                }
            })
            return res;
        },
    });
});
