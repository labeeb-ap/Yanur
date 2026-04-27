odoo.define('aspl_pos_order_sync.chrome', function (require) {
    'use strict';

    const { useState, useRef } = owl.hooks;
    const Chrome = require('point_of_sale.Chrome');
    const Registries = require('point_of_sale.Registries');
    require('bus.BusService');
    var bus = require('bus.Longpolling');
    var cross_tab = require('bus.CrossTab').prototype;
    var session = require('web.session');
    const { useListener } = require('web.custom_hooks');
    var rpc = require('web.rpc');

    const ChromeInherit = (Chrome) => class extends Chrome {
        constructor() {
            super(...arguments);
            useListener('show-orders-panel', this._showOrderPanel);
            useListener('reload-order-count', this._reloadOrderCount);
            this.state.OrderCount = 0;
            this.state.showOrderPanel = false;
        }
        async start() {
            await super.start();
            this.state.OrderCount = this.env.pos.get_orderCount();
            await this._poolData();
        }
        _showOrderPanel(){
            this.mainScreen != 'ProductScreen' ? this.showScreen('ProductScreen') : false;
            this.state.showOrderPanel = this.state.showOrderPanel ? false : true;
        }
        _poolData() {
            this.env.services['bus_service'].updateOption('order.sync',session.uid);
            this.env.services['bus_service'].onNotification(this,this._onNotification);
            this.env.services['bus_service'].startPolling();
            cross_tab._isRegistered = true;
            cross_tab._isMasterTab = true;
        }

        _onNotification(notifications){
            var self = this;
            for(let notif of notifications) {
                let previous_orders = self.env.pos.db.get_orders_list();
                if (notif[1] && notif[1].cancelled_order){
                    previous_orders = previous_orders.filter(function(obj){
                        return obj.id !== notif[1].cancelled_order[0].id;
                    });
                    self.env.pos.db.add_orders(previous_orders);
                    const orderFiltered = previous_orders.filter(order => order.state == "draft");
                    self.env.pos.db.add_draft_orders(orderFiltered);
                    this.state.OrderCount = orderFiltered.length;
                    this.render();
                }else if(notif[1] && notif[1].new_pos_order){
                    previous_orders.push(notif[1].new_pos_order[0]);
                    var obj = {};
                    for ( var i=0, len=previous_orders.length; i < len; i++ ){
                        obj[previous_orders[i]['id']] = previous_orders[i];
                    }
                    previous_orders = new Array();
                    for ( var key in obj ){
                       previous_orders.push(obj[key]);
                    }
                    previous_orders.sort(function(a, b) {
                      return b.id - a.id;
                    });
                    self.env.pos.db.add_orders(previous_orders);
                    const orderFiltered = previous_orders.filter(order => order.state == "draft");
                    self.env.pos.db.add_draft_orders(orderFiltered);
                    this.state.OrderCount = orderFiltered.length;
                    this.render();
                }
            }
        }
        _reloadOrderCount(event){
            this.state.OrderCount = event.detail.orders_count;
        }
    }
    Registries.Component.extend(Chrome, ChromeInherit);

    return Chrome;
});
