# Base OCR

Base module for integrating Optical Character Recognition (OCR) services in Odoo.

## Features

- Flexible OCR provider management
- Support for multiple OCR services
- Configurable OCR settings
- Easy integration with other modules

## Configuration

1. Go to Settings > Technical > OCR
2. Configure OCR provider settings
   - API keys
   - Endpoints
   - Default provider

## Usage

### OCR Provider Model

The module provides `ocr.provider` model with these features:
- Provider type selection
- API configuration
- Default provider setting
- Company-specific settings

### Process Images

```python
# Get default provider
provider = env["ocr.provider"].get_default_provider()

# Process image
result = provider.process_image(image_data, filename="document.pdf")
if result["success"]:
    text = result["text"]
else:
    error = result["error"]
```

### Extend Provider Types

1. Create new provider model inheriting `ocr.provider`
2. Implement `_process_[provider_type]` method
3. Add provider type to selection field

Example:
```python
class CustomProvider(models.Model):
    _inherit = "ocr.provider"

    def _process_custom(self, image_data, **kwargs):
        # Implement custom OCR processing
        return {
            "success": True,
            "text": "Extracted text",
        }
```

## Contributing

1. Fork the repository
2. Create a feature branch
3. Commit your changes
4. Push to the branch
5. Create a Pull Request

## Support

For support, please:
1. Check existing issues
2. Create a new issue with detailed information
3. Contact the maintainers
