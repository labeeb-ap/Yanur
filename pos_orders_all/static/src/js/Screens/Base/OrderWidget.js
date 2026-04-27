odoo.define('pos_orders_all.OrderWidgetExtended', function(require){
	'use strict';

	const OrderWidget = require('point_of_sale.OrderWidget');
	const PosComponent = require('point_of_sale.PosComponent');
	const Registries = require('point_of_sale.Registries');
	const { Component } = owl;

	const OrderSummaryExtended = (OrderWidget) =>
		class extends OrderWidget {
			constructor() {
				super(...arguments);
			}

			get total_items(){
				let order = this.env.pos.get_order();
				let total_items    = order ? order.get_total_items() : 0;
				return total_items.toFixed(2);;
			}

			get total_orders(){
				let order = this.env.pos.get_order();
				let total_orders    = order.orderlines.length;
				var lines = order.get_orderlines();
				lines.forEach(function(lines){

				var current_tax = lines.get_tax_details()
				let keys = Object.keys(current_tax)
                let values = Object.values(current_tax)
                var detailed_tax = lines.get_product()
                var CGST_percent = "0.00"
                var CGST_amount = "0.00"
                var SGST_percent = "0.00"
                var SGST_amount = "0.00"
                var CESS_percent = "0.00"
                var CESS_amount = "0.00"
                var current_type = " "
                var type_of_gst = ["CGST","SGST","CESS"]
                for(var l=0;l<keys.length;l++){
                var gst_name = detailed_tax.pos.taxes_by_id[keys[l]].name
                    var current_gst_amt = detailed_tax.pos.taxes_by_id[keys[l]].amount
                    for(var g=0;g<=type_of_gst.length;g++){
                        current_type = gst_name.match(type_of_gst[g])
                        if(current_type == "CGST"){
                        CGST_percent = current_gst_amt
                        CGST_amount = values[l].toFixed(2)
                        }else if(current_type == "SGST"){
                        SGST_percent = current_gst_amt
                        SGST_amount = values[l].toFixed(2)
                        }else if(current_type == "CESS"){
                        CESS_percent = current_gst_amt
                        CESS_amount = values[l].toFixed(2)
                        }
                    }
                }
                lines.CGST_percent = CGST_percent
                lines.CGST_amount = CGST_amount
                lines.SGST_percent = SGST_percent
                lines.SGST_amount = SGST_amount
                lines.CESS_percent = CESS_percent
                lines.CESS_amount = CESS_amount
//                console.log(lines.CGST_percent,"CGST_percent")
//                console.log(lines.CGST_amount,"CGST_amount")
//                console.log(lines.SGST_percent,"SGST_percent")
//                console.log(lines.SGST_amount,"SGST_amount")
//				console.log("current_tax",current_tax)

				});
				return total_orders.toFixed(2);;
			}

//			get order_line_gst(){
//			    let order = this.env.pos.get_order();
//			    let order_line_gst = order.orderlines.get_tax_details()
//			    console.log("order_line_gst",order_line_gst)
//			}

	};

	Registries.Component.extend(OrderWidget, OrderSummaryExtended);

	return OrderWidget;

});