# Document OCR

Document OCR is an Odoo module that provides Optical Character Recognition (OCR) and information extraction capabilities for documents.

## Features

- Upload and process various document types (PDF, images)
- OCR processing with configurable providers
- Information extraction using LLM (Large Language Models)
- Support for vendor bill processing
- Flexible document type handling

## Installation

### Prerequisites

1. Install required Python packages:
  - dateparser

2. Configure OCR and LLM providers in Odoo settings

## Configuration

1. Go to Settings > Technical > OCR or LLM
2. Configure OCR provider settings
3. Configure LLM provider settings

## Usage

1. Navigate to Document OCR > Documents
2. Upload a document (PDF or image)
3. Select document type
4. Process document
5. Review extracted information
6. Create related records (e.g., vendor bills)

## Document Types

### Vendor Bills
- Extracts vendor information
- Identifies line items
- Processes dates and amounts
- Creates draft vendor bills

### Other Documents
- Extracts general information
- Customizable for specific needs

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
