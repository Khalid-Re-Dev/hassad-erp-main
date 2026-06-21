"""
Barcode and QR Code Adapter
Handles barcode generation, scanning, and product label creation
"""
from typing import Optional
from io import BytesIO
from PIL import Image

try:
    import barcode
    from barcode.writer import ImageWriter
    BARCODE_AVAILABLE = True
except ImportError:
    BARCODE_AVAILABLE = False

try:
    import qrcode
    QRCODE_AVAILABLE = True
except ImportError:
    QRCODE_AVAILABLE = False


class BarcodeAdapter:
    """
    Adapter for barcode and QR code generation
    """
    
    @staticmethod
    def generate_barcode(
        code: str,
        barcode_type: str = 'code128',
        output_format: str = 'PNG'
    ) -> Image.Image:
        """
        Generate barcode image
        
        Args:
            code: Barcode data
            barcode_type: Barcode type (code128, ean13, etc.)
            output_format: Output format (PNG, SVG)
        
        Returns:
            PIL Image object
        
        Example:
            >>> img = BarcodeAdapter.generate_barcode("123456789012", "ean13")
        """
        if not BARCODE_AVAILABLE:
            raise ImportError(
                "python-barcode not installed. Install with: pip install python-barcode"
            )
        
        # Get barcode class
        barcode_class = barcode.get_barcode_class(barcode_type)
        
        # Generate barcode
        writer = ImageWriter()
        barcode_instance = barcode_class(code, writer=writer)
        
        # Render to image
        buffer = BytesIO()
        barcode_instance.write(buffer)
        buffer.seek(0)
        
        return Image.open(buffer)
    
    @staticmethod
    def generate_qr(
        data: str,
        size: int = 10,
        border: int = 4
    ) -> Image.Image:
        """
        Generate QR code image
        
        Args:
            data: QR code data
            size: Box size (pixels per box)
            border: Border size (boxes)
        
        Returns:
            PIL Image object
        
        Example:
            >>> img = BarcodeAdapter.generate_qr("https://example.com/invoice/123")
        """
        if not QRCODE_AVAILABLE:
            raise ImportError(
                "qrcode not installed. Install with: pip install qrcode[pil]"
            )
        
        qr = qrcode.QRCode(
            version=1,
            error_correction=qrcode.constants.ERROR_CORRECT_L,
            box_size=size,
            border=border,
        )
        qr.add_data(data)
        qr.make(fit=True)
        
        return qr.make_image(fill_color="black", back_color="white")
    
    @staticmethod
    def generate_product_label(
        product_id: str,
        sku: str,
        name: str,
        price: str,
        barcode_type: str = 'code128'
    ) -> Image.Image:
        """
        Generate product label with barcode
        
        Args:
            product_id: Product ID
            sku: Product SKU
            name: Product name
            price: Product price
            barcode_type: Barcode type
        
        Returns:
            PIL Image with product label
        
        Example:
            >>> label = BarcodeAdapter.generate_product_label(
            ...     "123", "PROD-001", "Sample Product", "99.99 SAR"
            ... )
        """
        # Generate barcode
        barcode_img = BarcodeAdapter.generate_barcode(sku, barcode_type)
        
        # Create label image
        label_width = 400
        label_height = 250
        label = Image.new('RGB', (label_width, label_height), color='white')
        
        # Paste barcode
        barcode_resized = barcode_img.resize((350, 100))
        label.paste(barcode_resized, (25, 50))
        
        # Add text (simplified - would use PIL ImageDraw in production)
        # TODO: Add product name and price text using ImageDraw
        
        return label
    
    @staticmethod
    def decode_barcode(image: Image.Image) -> Optional[str]:
        """
        Decode barcode from image
        
        Placeholder for barcode scanning functionality
        Requires pyzbar or similar library
        
        Args:
            image: PIL Image containing barcode
        
        Returns:
            Decoded barcode data or None
        """
        # TODO: Implement barcode decoding with pyzbar
        # This is a placeholder for future implementation
        raise NotImplementedError(
            "Barcode decoding not yet implemented. "
            "Install pyzbar: pip install pyzbar"
        )
