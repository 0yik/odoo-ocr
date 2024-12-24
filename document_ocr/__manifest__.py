{
    "name": "Document OCR",
    "version": "18.0.1.0.0",
    "category": "Document Management",
    "summary": "OCR Processing for Documents",
    "sequence": 10,
    "description": """
        Process documents using OCR technology and extract information.
        Features:
        - Upload documents (PDF, images)
        - OCR processing
        - Information extraction
        - Vendor bill creation
    """,
    "author": "Anang Aji Rahmawan",
    "website": "https://github.com/0yik",
    "depends": ["base", "mail", "account", "product", "base_ocr", "base_llm"],
    "data": [
        "security/ir.model.access.csv",
        "data/document_ocr_data.xml",
        "views/document_ocr_views.xml",
    ],
    "external_dependencies": {
        "python": ["dateparser"],
    },
    "installable": True,
    "application": True,
    "auto_install": False,
}
