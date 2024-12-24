from odoo import models, fields, api


class VendorBill(models.Model):
    _inherit = "document.ocr"

    document_type = fields.Selection(
        selection_add=[("vendor_bill", "Vendor Bill")],
        ondelete={"vendor_bill": "cascade"},
        string="Document Type",
        required=True,
    )

    def _get_prompt_template(self):
        """Get the prompt template based on document type"""
        result = super()._get_prompt_template()
        if self.document_type == "vendor_bill":
            return """
                    You MUST respond with ONLY a JSON object in this EXACT format, no explanations or other text:
                    {
                        "vendor_name": "string",
                        "invoice_number": "string",
                        "date": "YYYY-MM-DD",
                        "line_items": [
                            {
                                "product": "string",
                                "description": "string",
                                "quantity": number,
                                "price": number,
                                "subtotal": number
                            }
                        ],
                        "total": number,
                        "total_tax": number,
                        "total_discount": number
                    }
                    """
        return result

    def _parse_date(self, date_str):
        """Parse date string to YYYY-MM-DD format using dateparser."""
        if not date_str:
            return False

        try:
            import dateparser

            parsed_date = dateparser.parse(
                date_str,
                settings={
                    "PREFER_DAY_OF_MONTH": "first",
                    "PREFER_DATES_FROM": "past",
                    "RETURN_AS_TIMEZONE_AWARE": False,
                    "DATE_ORDER": "DMY",
                },
            )
            if parsed_date:
                return fields.Date.to_string(parsed_date.date())
        except Exception as e:
            _logger.warning("Date parsing failed for %s: %s", date_str, str(e))

        return fields.Date.today()

    def _process_data_vendor_bill(self, parsed_data):
        """Create vendor bill from parsed data"""
        # Find or create vendor
        partner = self.env["res.partner"].search(
            [("name", "ilike", parsed_data.get("vendor_name"))], limit=1
        )

        if not partner:
            partner = self.env["res.partner"].create(
                {
                    "name": parsed_data.get("vendor_name"),
                    "company_type": "company",
                    "is_company": True,
                }
            )

        lines = []
        # Add regular product lines with no tax
        for item in parsed_data.get("line_items", []):
            product = self.env["product.product"].search(
                [("name", "ilike", item.get("product"))], limit=1
            )

            if not product:
                product = self.env["product.product"].create(
                    {
                        "name": item.get("product"),
                        "type": "service",
                        "purchase_ok": True,
                    }
                )

            lines.append(
                (
                    0,
                    0,
                    {
                        "product_id": product.id,
                        "name": item.get("description") or product.name,
                        "quantity": item.get("quantity", 1.0),
                        "price_unit": item.get("price", 0.0),
                        "tax_ids": [(5, 0, 0)],  # Clear all taxes
                    },
                )
            )

        # Add tax line if present
        if parsed_data.get("total_tax"):
            tax_product = self.env["product.product"].search(
                [("name", "=", "Tax")], limit=1
            ) or self.env["product.product"].create(
                {
                    "name": "Tax",
                    "type": "service",
                    "purchase_ok": True,
                }
            )

            lines.append(
                (
                    0,
                    0,
                    {
                        "product_id": tax_product.id,
                        "name": "Tax",
                        "quantity": 1.0,
                        "price_unit": parsed_data.get("total_tax", 0.0),
                        "tax_ids": [(5, 0, 0)],  # No tax on tax line
                    },
                )
            )

        # Add discount line if present
        if parsed_data.get("total_discount"):
            discount_product = self.env["product.product"].search(
                [("name", "=", "Discount")], limit=1
            ) or self.env["product.product"].create(
                {
                    "name": "Discount",
                    "type": "service",
                    "purchase_ok": True,
                }
            )

            lines.append(
                (
                    0,
                    0,
                    {
                        "product_id": discount_product.id,
                        "name": "Discount",
                        "quantity": 1.0,
                        "price_unit": -abs(
                            parsed_data.get("total_discount", 0.0)
                        ),  # Always make discount negative
                        "tax_ids": [(5, 0, 0)],  # No tax on discount line
                    },
                )
            )

        # Create the vendor bill with parsed date
        bill = self.env["account.move"].create(
            {
                "move_type": "in_invoice",
                "partner_id": partner.id,
                "invoice_date": self._parse_date(parsed_data.get("date")),
                "ref": parsed_data.get("invoice_number"),
                "invoice_line_ids": lines,
            }
        )

        # Set the related record
        self.related_record = bill
