odoo.define("pos_kot_bill.modelsorderline", function (require) {
  "use strict";

  var models = require("point_of_sale.models");

  var _super_orderline = models.Orderline.prototype;

  models.Orderline = models.Orderline.extend({
    initialize: function (attr, options) {
      _super_orderline.initialize.call(this, attr, options);
      this.kot_qty = 0;
      this.kot_sent = false;
    },
    set_kot_qty: function (kot_qty) {
      this.kot_qty = kot_qty;
      this.trigger("change", this);
    },
    set_kot_sent: function (kot_sent) {
      this.kot_sent = kot_sent;
      this.trigger("change", this);
    },
    get_kot_sent: function (kot_sent) {
      return this.kot_sent;
    },
    get_kot_qty: function (kot_qty) {
      return this.kot_qty;
    },
    can_be_merged_with: function (orderline) {
      if (orderline.get_kot_qty() !== this.get_kot_qty()) {
        return false;
      }
      if (orderline.get_kot_sent() !== this.get_kot_sent()) {
        return false;
      }
      return _super_orderline.can_be_merged_with.apply(this, arguments);
    },
    clone: function () {
      var orderline = _super_orderline.clone.call(this);
      orderline.kot_qty = this.kot_qty;
      orderline.kot_sent = this.kot_sent;
      return orderline;
    },
    export_as_JSON: function () {
      var json = _super_orderline.export_as_JSON.call(this);
      json.kot_qty = this.kot_qty;
      json.kot_sent = this.kot_sent;
      return json;
    },
    init_from_JSON: function (json) {
      _super_orderline.init_from_JSON.apply(this, arguments);
      this.kot_qty = json.kot_qty;
      this.kot_sent = json.kot_sent;
    },
  });
});