import base64
import json
import logging
import os
import tempfile
from odoo import models, fields, api, _
from odoo.exceptions import UserError

_logger = logging.getLogger(__name__)


class DocumentOCR(models.Model):
    _name = "document.ocr"
    _description = "Document OCR Processing"
    _inherit = ["mail.thread", "mail.activity.mixin"]

    name = fields.Char(
        string="Name", required=True, copy=False, readonly=True, default="/"
    )
    document_file = fields.Binary(string="Document File", required=True)
    document_filename = fields.Char(string="Filename")
    file_type = fields.Selection(
        [("pdf", "PDF"), ("image", "Image")],
        string="File Type",
        compute="_compute_file_type",
        store=True,
    )
    document_type = fields.Selection(
        [("other", "Other")],
        string="Document Type",
        required=True,
        ondelete={"other": "set default"},
        default="other",
    )
    state = fields.Selection(
        [
            ("draft", "Draft"),
            ("processing", "Processing"),
            ("done", "Done"),
            ("error", "Error"),
        ],
        string="Status",
        default="draft",
        readonly=True,
        tracking=True,
    )
    related_record = fields.Reference(
        selection="_get_reference_models", string="Related Record", readonly=True
    )
    ocr_result = fields.Text(string="OCR Result", readonly=True)
    parsed_data = fields.Text(string="Parsed Data", readonly=True)
    error_message = fields.Text(string="Error Message", readonly=True)
    company_id = fields.Many2one(
        "res.company",
        string="Company",
        required=True,
        default=lambda self: self.env.company,
    )
    ocr_language = fields.Selection([
        ('ara', 'Arabic'),
        ('bul', 'Bulgarian'),
        ('chs', 'Chinese (Simplified)'),
        ('cht', 'Chinese (Traditional)'),
        ('hrv', 'Croatian'),
        ('cze', 'Czech'),
        ('dan', 'Danish'),
        ('dut', 'Dutch'),
        ('eng', 'English'),
        ('fin', 'Finnish'),
        ('fre', 'French'),
        ('ger', 'German'),
        ('gre', 'Greek'),
        ('hun', 'Hungarian'),
        ('kor', 'Korean'),
        ('ita', 'Italian'),
        ('jpn', 'Japanese'),
        ('pol', 'Polish'),
        ('por', 'Portuguese'),
        ('rus', 'Russian'),
        ('slv', 'Slovenian'),
        ('spa', 'Spanish'),
        ('swe', 'Swedish'),
        ('tur', 'Turkish'),
    ], string='OCR Language', required=True, default='eng',
        help="Language used for OCR processing. If not specified, English will be used.")
    ocr_provider_id = fields.Many2one(
        "ocr.provider",
        string="OCR Provider",
        default=lambda self: self.env["ocr.provider"].get_default_provider(),
    )
    llm_provider_id = fields.Many2one(
        "llm.provider",
        string="LLM Provider",
        default=lambda self: self.env["llm.provider"].get_default_provider()
    )

    @api.model
    def _get_reference_models(self):
        models = self.env["ir.model"].search([])
        return [(model.model, model.name) for model in models]

    def _process_data_other(self, parsed_data):
        pass

    @api.model_create_multi
    def create(self, vals_list):
        for vals in vals_list:
            if vals.get("name", "/") == "/":
                vals["name"] = self.env["ir.sequence"].next_by_code("document.ocr")
        return super().create(vals_list)

    @api.depends("document_file", "document_filename")
    def _compute_file_type(self):
        for record in self:
            if not record.document_file or not record.document_filename:
                record.file_type = False
                continue

            ext = os.path.splitext(record.document_filename)[1].lower()
            if ext in [".pdf"]:
                record.file_type = "pdf"
            elif ext in [".jpg", ".jpeg", ".png", ".gif", ".bmp", ".tiff", ".tif"]:
                record.file_type = "image"
            else:
                raise UserError(
                    _("Unsupported file type. Please upload a PDF or image file.")
                )

    def _get_prompt_template(self):
        """Get the prompt template based on document type"""
        return """You MUST respond with ONLY a JSON object containing 
        the key information from this document, no explanations or other text."""

    @api.onchange("llm_provider_id")
    def _onchange_llm_provider(self):
        if self.llm_provider_id:
            self.llm_provider_id = self.llm_provider_id.id

    def process_document(self):
        self.ensure_one()
        if not self.document_file:
            raise UserError(_("Please upload a document file first."))

        if not self.ocr_provider_id:
            raise UserError(_("Please configure an OCR provider in settings."))

        try:
            self.state = "processing"
            _logger.info("Processing document: %s", self.name)

            # Create a temporary directory
            with tempfile.TemporaryDirectory() as temp_dir:
                # Save binary data to temporary file
                binary_data = base64.b64decode(self.document_file)
                temp_input = os.path.join(temp_dir, self.document_filename)
                with open(temp_input, "wb") as f:
                    f.write(binary_data)

                # Process with OCR
                ocr_result = self._process_ocr(temp_input)
                if not ocr_result.get("ParsedResults"):
                    raise UserError(_("OCR processing failed. Please try again."))

                # Parse OCR result
                parsed_text = ocr_result["ParsedResults"][0]["ParsedText"]
                parsed_json = self._parse_text_to_json(parsed_text)

                # Store results
                self.ocr_result = parsed_text
                self.parsed_data = json.dumps(parsed_json)

                # Process according to document type
                method_name = f"_process_data_{self.document_type}"
                if hasattr(self, method_name):
                    getattr(self, method_name)(parsed_json)
                else:
                    raise UserError(
                        _("Document type %s is not implemented") % self.document_type
                    )

                self.state = "done"

        except Exception as e:
            error_msg = str(e)
            _logger.error("Error processing document: %s", error_msg)
            self.state = "error"
            self.error_message = error_msg
            raise UserError(_("Error processing document: %s") % error_msg)

    def _parse_text_to_json(self, text):
        if not self.llm_provider_id:
            raise UserError(_("Please select an LLM provider."))

        prompt = f"""{self._get_prompt_template()}

                Input text to convert:
                {text}
                """

        result = self.llm_provider_id.process_prompt(
            prompt,
            response_format={"type": "json_object"},
            temperature=0.1,
        )
        if result.get("success"):
            return result["content"]
        else:
            raise UserError(_("Error parsing document text: %s") % result.get("error"))

    def _process_ocr(self, file_path):
        """Process document with OCR provider."""
        try:
            with open(file_path, "rb") as file:
                file_data = file.read()

            # Process with OCR provider
            result = self.ocr_provider_id.process_image(
                file_data, filename=os.path.basename(file_path), language=self.ocr_language
            )

            if result.get("success"):
                return {"ParsedResults": [{"ParsedText": result["text"]}]}
            else:
                raise UserError(
                    _("OCR processing failed: %s")
                    % result.get("error", "Unknown error")
                )
        except Exception as e:
            _logger.error("OCR Error: %s", str(e))
            raise UserError(str(e))
