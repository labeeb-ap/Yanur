{
    "name": "Point of Sale Discounts in Amount",
    "summary": "Allow to apply discounts with fixed amount",
    "version": "14.1",
    "category": "Point of Sale",
    "website": "http://catalist.catalisterp.in/",
    "author": "Catalist",
    "application": False,
    "installable": True,
    "depends": ["pos_discount"],
    "data": ["views/pos_config_views.xml",
             "views/pos_templates.xml"],
    "qweb": ["static/src/xml/discount_templates.xml"],
}
