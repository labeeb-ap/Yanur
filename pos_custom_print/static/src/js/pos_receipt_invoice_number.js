odoo.define('pos_receipt_invoice_number', function (require) {
    "use strict";

    var models = require('point_of_sale.models');

    models.PosModel.prototype.load_company_fields = function () {
        var self = this;
        var company_fields = ['street', 'street2', 'city', 'zip', 'state_id', 'country_id', 'phone', 'email', 'website', 'vat'];
        return this.rpc({
            model: 'res.company',
            method: 'search_read',
            fields: company_fields,
            domain: [['id', '=', this.company.id]],
        }).then(function (result) {
            if (result.length) {
                var company = result[0];
                self.company.street = company.street;
                self.company.street2 = company.street2;
                self.company.city = company.city;
                self.company.zip = company.zip;
                self.company.state_id = company.state_id[0];
                self.company.country_id = company.country_id[0];
                self.company.phone = company.phone;
                self.company.email = company.email;
                self.company.website = company.website;
                self.company.vat = company.vat;
            }
            console.log("street",self.company.street,self.company.street2)
        });
    };

    models.load_models([
        {
            model: 'res.company',
            fields: ['street', 'street2', 'city', 'zip', 'state_id', 'country_id', 'phone', 'email', 'website', 'vat'],
            loaded: function (self, companies) {
                self.load_company_fields();
            },
        },
    ]);
});
