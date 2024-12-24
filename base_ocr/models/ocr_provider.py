import logging
from odoo import models, fields, api, _
from odoo.exceptions import UserError

_logger = logging.getLogger(__name__)


class OCRProvider(models.Model):
    _name = "ocr.provider"
    _description = "OCR Provider"

    name = fields.Char(string="Name", required=True)
    provider_type = fields.Selection(
        [
            ("ocrspace", "OCR.space"),
            ("openocr", "OpenOCR"),
        ],
        string="Provider Type",
        required=True,
    )
    api_key = fields.Char(string="API Key")
    api_endpoint = fields.Char(string="API Endpoint")
    active = fields.Boolean(default=True)
    company_id = fields.Many2one(
        "res.company",
        string="Company",
        required=True,
        default=lambda self: self.env.company,
    )
    is_default = fields.Boolean(string="Default Provider")

    @api.model
    def create(self, vals):
        if vals.get("is_default"):
            self.search(
                [
                    ("is_default", "=", True),
                    ("company_id", "=", vals.get("company_id", self.env.company.id)),
                ]
            ).write({"is_default": False})
        return super().create(vals)

    def write(self, vals):
        if vals.get("is_default"):
            self.search(
                [
                    ("is_default", "=", True),
                    ("company_id", "=", self.company_id.id),
                    ("id", "!=", self.id),
                ]
            ).write({"is_default": False})
        return super().write(vals)

    def process_image(self, image_data, **kwargs):
        """Process the image using the selected OCR provider"""
        self.ensure_one()

        if not self.api_key:
            raise UserError(_("API Key is required for OCR processing"))

        method_name = f"_process_{self.provider_type}"
        if hasattr(self, method_name):
            return getattr(self, method_name)(image_data, **kwargs)
        else:
            raise UserError(
                _("Provider type %s is not implemented") % self.provider_type
            )

    @api.model
    def get_default_provider(self, company_id=None):
        """Get the default OCR provider for the company"""
        if not company_id:
            company_id = self.env.company.id
        return self.search(
            [("company_id", "=", company_id), ("is_default", "=", True)], limit=1
        )
