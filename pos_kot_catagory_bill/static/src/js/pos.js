odoo.define('pos_kot_catagory_bill.pos', function(require) {
    "use strict";

    var models = require('point_of_sale.models');

    var _super_order = models.Order.prototype;
    models.Order = models.Order.extend({
        compute_Changes: function(categories) {
            var current_res = this.kot_bill_build_line_resume();
            var old_res = this.kot_bill_saved_resume || {};
            var add_categ_dict = {};
            var rem_categ_dict = {};
            var p_key, note;

            for (p_key in current_res) {
                for (note in current_res[p_key]['qties']) {
                    var curr = current_res[p_key];
                    var old = old_res[p_key] || {};
                    var pid = curr.pid;
                    var pos_categ_id = this.pos.db.get_product_by_id(pid).pos_categ_id
                    var found = p_key in old_res && note in old_res[p_key]['qties'];

                    if (!found) {
                        if (pos_categ_id && pos_categ_id[1] in add_categ_dict) {
                            add_categ_dict[pos_categ_id[1]].push({
                                'id': pid,
                                'name': this.pos.db.get_product_by_id(pid).display_name,
                                'name_wrapped': curr.product_name_wrapped,
                                'note': note,
                                'qty': curr['qties'][note],
                            });
                        } else {
                            var add = []
                            add.push({
                                'id': pid,
                                'name': this.pos.db.get_product_by_id(pid).display_name,
                                'name_wrapped': curr.product_name_wrapped,
                                'note': note,
                                'qty': curr['qties'][note],
                            });
                            if (pos_categ_id == false) {
                                add_categ_dict['Undefined'] = add;
                            } else {
                                add_categ_dict[this.pos.db.get_product_by_id(pid).pos_categ_id[1]] = add;
                            }
                        }
                    } else if (old['qties'][note] < curr['qties'][note]) {
                        if (pos_categ_id && pos_categ_id[1] in add_categ_dict) {
                            add_categ_dict[pos_categ_id[1]].push({
                                'id': pid,
                                'name': this.pos.db.get_product_by_id(pid).display_name,
                                'name_wrapped': curr.product_name_wrapped,
                                'note': note,
                                'qty': curr['qties'][note] - old['qties'][note],
                            });
                        } else {
                            var add = []
                            add.push({
                                'id': pid,
                                'name': this.pos.db.get_product_by_id(pid).display_name,
                                'name_wrapped': curr.product_name_wrapped,
                                'note': note,
                                'qty': curr['qties'][note] - old['qties'][note],
                            });
                            if (pos_categ_id == false) {
                                add_categ_dict['Undefined'] = add;
                            } else {
                                add_categ_dict[this.pos.db.get_product_by_id(pid).pos_categ_id[1]] = add;
                            }
                        }
                    } else if (old['qties'][note] > curr['qties'][note]) {
                        if (pos_categ_id && pos_categ_id[1] in rem_categ_dict) {
                            rem_categ_dict[pos_categ_id[1]].push({
                                'id': pid,
                                'name': this.pos.db.get_product_by_id(pid).display_name,
                                'name_wrapped': curr.product_name_wrapped,
                                'note': note,
                                'qty': old['qties'][note] - curr['qties'][note],
                            });
                        } else {
                            var rem = []
                            rem.push({
                                'id': pid,
                                'name': this.pos.db.get_product_by_id(pid).display_name,
                                'name_wrapped': curr.product_name_wrapped,
                                'note': note,
                                'qty': old['qties'][note] - curr['qties'][note],
                            });
                            if (pos_categ_id == false) {
                                rem_categ_dict['Undefined'] = add;
                            } else {
                                rem_categ_dict[this.pos.db.get_product_by_id(pid).pos_categ_id[1]] = rem;
                            }
                        }
                    }
                }
            }
            for (p_key in old_res) {
                for (note in old_res[p_key]['qties']) {

                    var found = p_key in current_res && note in current_res[p_key]['qties'];
                    if (!found) {
                        var old = old_res[p_key];
                        var pid = old.pid;
                        var pos_categ_id = this.pos.db.get_product_by_id(pid).pos_categ_id
                        if (pos_categ_id && pos_categ_id in rem_categ_dict) {
                            rem_categ_dict[this.pos.db.get_product_by_id(pid).pos_categ_id[1]].push({
                                'id': pid,
                                'name': this.pos.db.get_product_by_id(pid).display_name,
                                'name_wrapped': old.product_name_wrapped,
                                'note': note,
                                'qty': old['qties'][note],
                            });
                        } else {
                            var rem = []
                            rem.push({
                                'id': pid,
                                'name': this.pos.db.get_product_by_id(pid).display_name,
                                'name_wrapped': old.product_name_wrapped,
                                'note': note,
                                'qty': old['qties'][note],
                            });
                            if (pos_categ_id == false) {
                                rem_categ_dict['Undefined'] = add;
                            } else {
                                rem_categ_dict[this.pos.db.get_product_by_id(pid).pos_categ_id[1]] = rem;
                            }
                        }
                    }
                }
            }

            var d = new Date();
            var hours = '' + d.getHours();
            hours = hours.length < 2 ? ('0' + hours) : hours;
            var minutes = '' + d.getMinutes();
            minutes = minutes.length < 2 ? ('0' + minutes) : minutes;

            if (jQuery.isEmptyObject(add_categ_dict)) {
                var add_product = [];
            } else {
                var add_product = [add_categ_dict];
            }
            if (jQuery.isEmptyObject(rem_categ_dict)) {
                var rem_product = [];
            } else {
                var rem_product = [rem_categ_dict];
            }
            return {
                'new': add_product,
                'cancelled': rem_product,
                'time': {
                    'hours': hours,
                    'minutes': minutes,
                },
                'old_res': old_res,
            };
        },

    });

});