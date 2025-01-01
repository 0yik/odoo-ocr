import logging
from odoo import models, fields, api, _
from odoo.exceptions import UserError

_logger = logging.getLogger(__name__)


class OCRProvider(models.Model):
    _name = "ocr.provider"
    _description = "OCR Provider"

    # Language code mappings for different providers
    LANGUAGE_MAPPINGS = {
        'openocr': {
            'ara': 'ara',     # Arabic
            'bul': 'bul',     # Bulgarian
            'chs': 'chi-sim', # Chinese (Simplified)
            'cht': 'chi-tra', # Chinese (Traditional)
            'hrv': 'hrv',     # Croatian
            'cze': 'ces',     # Czech
            'dan': 'dan',     # Danish
            'dut': 'nld',     # Dutch
            'eng': 'eng',     # English
            'fin': 'fin',     # Finnish
            'fre': 'fra',     # French
            'ger': 'deu',     # German
            'gre': 'ell',     # Greek
            'hun': 'hun',     # Hungarian
            'kor': 'kor',     # Korean
            'ita': 'ita',     # Italian
            'jpn': 'jpn',     # Japanese
            'pol': 'pol',     # Polish
            'por': 'por',     # Portuguese
            'rus': 'rus',     # Russian
            'slv': 'slv',     # Slovenian
            'spa': 'spa',     # Spanish
            'swe': 'swe',     # Swedish
            'tur': 'tur',     # Turkish
        },
        'ocrspace': {
            'ara': 'ara',     # Arabic
            'bul': 'bul',     # Bulgarian
            'chi-sim': 'chs', # Chinese (Simplified)
            'chi-tra': 'cht', # Chinese (Traditional)
            'hrv': 'hrv',     # Croatian
            'ces': 'cze',     # Czech
            'dan': 'dan',     # Danish
            'nld': 'dut',     # Dutch
            'eng': 'eng',     # English
            'fin': 'fin',     # Finnish
            'fra': 'fre',     # French
            'deu': 'ger',     # German
            'ell': 'gre',     # Greek
            'hun': 'hun',     # Hungarian
            'kor': 'kor',     # Korean
            'ita': 'ita',     # Italian
            'jpn': 'jpn',     # Japanese
            'pol': 'pol',     # Polish
            'por': 'por',     # Portuguese
            'rus': 'rus',     # Russian
            'slv': 'slv',     # Slovenian
            'spa': 'spa',     # Spanish
            'swe': 'swe',     # Swedish
            'tur': 'tur',     # Turkish
        }
    }

    name = fields.Char(string="Name", required=True)
    provider_type = fields.Selection(
        [
            ("ocrspace", "ocr.space"),
            ("openocr", "open-ocr"),
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

    def _map_language_code(self, language):
        """Map language code between providers.
        
        Args:
            language (str): Source language code
            
        Returns:
            str: Mapped language code for target provider
        """
        if not language:
            return 'eng'  # Default to English
            
        # If language code exists in target provider mapping, return as is
        if language in self.LANGUAGE_MAPPINGS.get(self.provider_type, {}):
            return language
            
        # Try to find mapping from other provider
        for provider, mappings in self.LANGUAGE_MAPPINGS.items():
            if provider != self.provider_type:
                # If we find the language in another provider's mapping
                if language in mappings:
                    # Get the standard code (value) and then map it to target provider
                    standard_code = mappings[language]
                    # Find the key in target provider mapping that has this standard code as value
                    for target_code, std_code in self.LANGUAGE_MAPPINGS[target_provider].items():
                        if std_code == standard_code:
                            return target_code
                            
        return 'eng'  # Default to English if no mapping found

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
