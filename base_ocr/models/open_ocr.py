import requests
import logging
import base64
import os
from odoo import models, _
from odoo.exceptions import UserError

_logger = logging.getLogger(__name__)


class OpenOCRProvider(models.Model):
    _inherit = "ocr.provider"

    def _process_openocr(self, image_data, filename=None, **kwargs):
        """Process image using Open OCR API."""
        self.ensure_one()

        if not self.api_endpoint:
            self.api_endpoint = "http://localhost:9292"

        # Get mapped language code for Open OCR
        language = self._map_language_code(kwargs.get("language", "eng"))

        try:
            # Convert image data to base64
            file_b64 = base64.b64encode(image_data).decode("utf-8")

            # Prepare request payload
            payload = {
                "img_base64": file_b64,
                "engine": "tesseract",
                "engine_args": {"lang": language},
            }

            # Add PDF preprocessor if file is PDF
            if filename and filename.lower().endswith(".pdf"):
                payload["preprocessors"] = ["convert-pdf"]

            # Make request to Open OCR API
            headers = {"Content-Type": "application/json"}
            api_url = f"{self.api_endpoint}/ocr"
            _logger.info("Making request to Open OCR API: %s", api_url)

            response = requests.post(api_url, headers=headers, json=payload, timeout=30)

            _logger.info("Open OCR API Response Status: %s", response.status_code)

            response.raise_for_status()

            result = response.text

            return {"success": True, "text": result}

        except requests.exceptions.RequestException as e:
            error_msg = f"API Connection Error: {str(e)}"
            _logger.error("Open OCR API Error: %s", str(e))
            return {"success": False, "error": error_msg}
        except Exception as e:
            error_msg = str(e)
            _logger.error("Open OCR Processing Error: %s", error_msg)
            return {"success": False, "error": error_msg}
