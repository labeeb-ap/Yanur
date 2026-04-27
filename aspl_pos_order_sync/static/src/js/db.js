odoo.define('aspl_pos_order_sync.db', function (require) {
    "use strict";

    var DB = require('point_of_sale.DB');
    var core = require('web.core');
    var rpc = require('web.rpc');
    var _t = core._t;

    DB.include({
        init: function(options){
            this._super.apply(this, arguments);
            this.order_write_date = null;
            this.order_sorted = [];
            this.orders_list = [];
            this.draft_orders_list = [];
            this.orders_list_by_id = {};
            this.order_search_string = "";
        },

        get_serial_lot_product(pack_lot_ids){
            var self = this;
            let draftPackLotLines;
            return new Promise(function (resolve, reject) {
                rpc.query({
                    model: 'pos.pack.operation.lot',
                    method: 'search_read',
                    fields: ['id','lot_name'],
                    domain: [['id', 'in', pack_lot_ids]],
                }).then(function (lot_serial_res) {
                    const modifiedPackLotLines = {};
                    var newPackLotLines = lot_serial_res;
                    draftPackLotLines = { modifiedPackLotLines, newPackLotLines };
                    resolve(draftPackLotLines);
                })
            });
        },

        add_orders : function(orders){
            var updated_count = 0;
            var new_write_date = '';
            this.orders_list = orders
            for(var i = 0, len = orders.length; i < len; i++){
                var order = orders[i];
                let localTime =  moment.utc(order['date_order']).toDate();
                order['date_order'] =   moment(localTime).format('YYYY-MM-DD hh:mm:ss')
                if (    this.order_write_date &&
                        this.orders_list_by_id[order.id] &&
                        new Date(this.order_write_date).getTime() + 1000 >=
                        new Date(order.write_date).getTime() ) {
                    continue;
                } else if ( new_write_date < order.write_date ) {
                    new_write_date  = order.write_date;
                }
                if (!this.orders_list_by_id[order.id]) {
                    this.order_sorted.push(order.id);
                }
                this.orders_list_by_id[order.id] = order;
                updated_count += 1;
            }
            this.order_write_date = new_write_date || this.order_write_date;
            if (updated_count){
                this.order_search_string = "";
                for (var id in this.orders_list_by_id) {
                    var order = this.orders_list_by_id[id];
                    this.order_search_string += this._order_search_string(order);
                }
            }
            return updated_count;
        },
        get_orders_list_by_id: function(id){
            return this.orders_list_by_id[id];
        },
        get_orders_list: function(){
            return this.orders_list;
        },
        add_draft_orders:function(draft_orders){
            this.draft_orders_list = draft_orders;
        },
        get_draft_orders_list: function(){
            return this.draft_orders_list;
        },
        _order_search_string: function(order){
            var str =  order.name;
            if(order.pos_reference){
                str += '|' + order.pos_reference;
            }
            if(order.partner_id.length > 0){
                str += '|' + order.partner_id[1];
            }
            if(order.salesman_id && order.salesman_id.length > 0){
                str += '|' + order.salesman_id[1];
            }
            str = '' + order.id + ':' + str.replace(':','') + '\n';
            return str;
        },

        search_orders: function(query){
            try {
                query = query.replace(/[\[\]\(\)\+\*\?\.\-\!\&\^\$\|\~\_\{\}\:\,\\\/]/g,'.');
                query = query.replace(' ','.+');
                var re = RegExp("([0-9]+):.*?"+query,"gi");
            }catch(e){
                return [];
            }
            var results = [];
            var r;
            for(var i = 0; i < this.limit; i++){
                r = re.exec(this.order_search_string);
                if(r){
                    var id = Number(r[1]);
                    results.push(this.get_orders_list_by_id(id));
                }else{
                    break;
                }
            }
            return results;
        },
    });
});