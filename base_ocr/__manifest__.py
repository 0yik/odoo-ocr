{
    "name": "Base OCR",
    "version": "18.0.1.0.0",
    "category": "Tools",
    "summary": "Base module for OCR providers integration",
    "sequence": 1,
    "description": """
        Base OCR Provider Integration
        ===========================
        This module provides the base structure for integrating various OCR providers.
        Currently supported providers:
        - OCR.space
        
        This module serves as a foundation for other OCR-related modules.
    """,
    "author": "Anang Aji Rahmawan",
    "website": "https://github.com/0yik",
    "depends": ["base"],
    "data": [
        "security/ir.model.access.csv",
        "views/ocr_provider_views.xml",
    ],
    "installable": True,
    "application": False,
    "auto_install": False,
}
