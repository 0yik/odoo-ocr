import requests
import logging
import os
from odoo import models, _
from odoo.exceptions import UserError

_logger = logging.getLogger(__name__)


class OCRSpaceProvider(models.Model):
    _inherit = "ocr.provider"

    def _process_ocrspace(self, image_data, filename=None, **kwargs):
        """Process image using OCR.space API."""
        self.ensure_one()

        if not self.api_key:
            raise UserError(
                _("Please configure OCR.space API key in provider settings")
            )

        if not self.api_endpoint:
            self.api_endpoint = "https://api.ocr.space/parse/image"

        # Get file extension from the filename
        ext = os.path.splitext(filename)[1].lstrip(".").upper() if filename else "PNG"

        headers = {"apikey": self.api_key}

        payload = {
            "language": kwargs.get("language", "eng"),
            "isOverlayRequired": False,
            "OCREngine": 1,
            "isTable": True,
            "scale": True,
            "filetype": ext,
        }

        files = {
            "file": (
                filename or f"document.{ext.lower()}",
                image_data,
                "application/octet-stream",
            )
        }

        try:
            response = requests.post(
                self.api_endpoint,
                headers=headers,
                files=files,
                data=payload,
                timeout=30,
            )
            response.raise_for_status()
            result = response.json()

            if not result.get("ParsedResults"):
                error_msg = result.get("ErrorMessage", "Unknown error occurred")
                _logger.error("OCR Error: %s", error_msg)
                raise UserError(_("OCR processing failed: %s") % error_msg)

            return {
                "success": True,
                "text": result["ParsedResults"][0].get("ParsedText", ""),
                "raw_response": result,
            }

        except requests.exceptions.RequestException as e:
            _logger.error("OCR API Request failed: %s", str(e))
            return {"success": False, "error": str(e)}
        except ValueError as e:
            _logger.error("Invalid JSON response from OCR service: %s", str(e))
            return {"success": False, "error": str(e)}
        except Exception as e:
            _logger.error("Error processing document: %s", str(e))
            return {"success": False, "error": str(e)}
