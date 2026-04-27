odoo.define('pos_kot_bill.models', function(require) {
    "use strict";

    var models = require('point_of_sale.models');

    var _super_orderline = models.Orderline.prototype;
    models.Orderline = models.Orderline.extend({
        initialize: function() {
            _super_orderline.initialize.apply(this, arguments);
            if (typeof this.ap_printed === 'undefined') {
                this.ap_printed = false;
            }
            if (typeof this.ap_quantity === 'undefined') {
                this.ap_quantity = false;
            }
        },
        init_from_JSON: function(json) {
            _super_orderline.init_from_JSON.apply(this, arguments);
            this.ap_printed = json.ap_printed;
            this.ap_quantity = json.ap_quantity;
        },
        export_as_JSON: function() {
            var json = _super_orderline.export_as_JSON.apply(this, arguments);
            json.ap_printed = this.ap_printed;
            json.ap_quantity = this.ap_quantity;
            return json;
        },
        kot_set_dirty: function(dirty) {
            this.ap_printed = dirty;
            this.ap_quantity = false;
            this.trigger('change', this);
        },

    });



    var _super_order = models.Order.prototype;
    models.Order = models.Order.extend({

        kotPrintChanges: function() {
            if (changes['new'].length > 0 && changes['cancelled'].length > 0) {
                return false;
            }
            return true;
        },

        kot_bill_build_line_resume: function() {
            var resume = {};
            this.orderlines.each(function(line) {
                if (line.mp_skip) {
                    return;
                }
                var qty = Number(line.get_quantity());
                var note = line.get_note();
                var product_id = line.get_product().id;
                var product_name = line.get_full_product_name();
                var p_key = product_id + " - " + product_name;
                var product_resume = p_key in resume ? resume[p_key] : {
                    pid: product_id,
                    product_name_wrapped: line.generate_wrapped_product_name(),
                    qties: {},
                };
                if (note in product_resume['qties']) product_resume['qties'][note] += qty;
                else product_resume['qties'][note] = qty;
                resume[p_key] = product_resume;

            });
            return resume;
        },
        export_as_JSON: function() {
            var json = _super_order.export_as_JSON.apply(this, arguments);
            json.multiprint_resume = JSON.stringify(this.kot_bill_saved_resume);
            return json;
        },
        init_from_JSON: function(json) {
            _super_order.init_from_JSON.apply(this, arguments);
            this.kot_bill_saved_resume = json.multiprint_resume && JSON.parse(json.multiprint_resume);
        },
        saveChanges: function() {
            this.saved_resume = this.build_line_resume();
            this.kot_bill_saved_resume = this.kot_bill_build_line_resume();
            this.orderlines.each(function(line) {
                line.set_dirty(false);
            });
            this.trigger('change', this);
        },
        compute_Changes: function() {
            var current_res = this.kot_bill_build_line_resume();
            var old_res = this.kot_bill_saved_resume || {};
            var json = this.export_as_JSON();
            var add = [];
            var rem = [];
            var p_key, note;

            for (p_key in current_res) {
                for (note in current_res[p_key]['qties']) {
                    var curr = current_res[p_key];
                    var old = old_res[p_key] || {};
                    var pid = curr.pid;
                    var found = p_key in old_res && note in old_res[p_key]['qties'];

                    if (!found) {
                        add.push({
                            'id': pid,
                            'name': this.pos.db.get_product_by_id(pid).display_name,
                            'name_wrapped': curr.product_name_wrapped,
                            'note': note,
                            'qty': curr['qties'][note],
                        });
                    } else if (old['qties'][note] < curr['qties'][note]) {
                        add.push({
                            'id': pid,
                            'name': this.pos.db.get_product_by_id(pid).display_name,
                            'name_wrapped': curr.product_name_wrapped,
                            'note': note,
                            'qty': curr['qties'][note] - old['qties'][note],
                        });
                    } else if (old['qties'][note] > curr['qties'][note]) {
                        rem.push({
                            'id': pid,
                            'name': this.pos.db.get_product_by_id(pid).display_name,
                            'name_wrapped': curr.product_name_wrapped,
                            'note': note,
                            'qty': old['qties'][note] - curr['qties'][note],
                        });
                    }
                }
            }

            for (p_key in old_res) {
                for (note in old_res[p_key]['qties']) {
                    var found = p_key in current_res && note in current_res[p_key]['qties'];
                    if (!found) {
                        var old = old_res[p_key];
                        var pid = old.pid;
                        rem.push({
                            'id': pid,
                            'name': this.pos.db.get_product_by_id(pid).display_name,
                            'name_wrapped': old.product_name_wrapped,
                            'note': note,
                            'qty': old['qties'][note],
                        });
                    }
                }
            }

            var d = new Date();
            var hours = '' + d.getHours();
            hours = hours.length < 2 ? ('0' + hours) : hours;
            var minutes = '' + d.getMinutes();
            minutes = minutes.length < 2 ? ('0' + minutes) : minutes;

            return {
                'new': add,
                'cancelled': rem,
                'time': {
                    'hours': hours,
                    'minutes': minutes,
                },
            };
        },

    });
});