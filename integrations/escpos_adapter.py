"""
ESC/POS Printer Adapter
Wrapper for python-escpos library with Arabic rendering support
"""
from typing import Optional
from PIL import Image

try:
    from escpos.printer import Usb, Serial, Network, File
    ESCPOS_AVAILABLE = True
except ImportError:
    ESCPOS_AVAILABLE = False


class EscposAdapter:
    """
    Adapter for ESC/POS thermal printers
    Supports USB, Serial, Network, and File output
    """
    
    def __init__(
        self,
        printer_type: str = "file",
        device_path: Optional[str] = None,
        **kwargs
    ):
        """
        Initialize ESC/POS printer
        
        Args:
            printer_type: Type of printer (usb, serial, network, file)
            device_path: Device path or file path
            **kwargs: Additional printer-specific arguments
        """
        if not ESCPOS_AVAILABLE:
            raise ImportError(
                "python-escpos not installed. Install with: pip install python-escpos"
            )
        
        self.printer_type = printer_type
        self.device_path = device_path or "/tmp/receipt.txt"
        self.printer = None
        
        self._initialize_printer(**kwargs)
    
    def _initialize_printer(self, **kwargs):
        """Initialize printer based on type"""
        if self.printer_type == "usb":
            # USB printer (requires vendor_id and product_id)
            vendor_id = kwargs.get('vendor_id', 0x04b8)
            product_id = kwargs.get('product_id', 0x0e15)
            self.printer = Usb(vendor_id, product_id)
        
        elif self.printer_type == "serial":
            # Serial printer
            self.printer = Serial(devfile=self.device_path)
        
        elif self.printer_type == "network":
            # Network printer (requires host and port)
            host = kwargs.get('host', '192.168.1.100')
            port = kwargs.get('port', 9100)
            self.printer = Network(host, port)
        
        else:
            # File output (for testing)
            self.printer = File(self.device_path)
    
    def print_text(self, text: str, font: str = 'a', align: str = 'left'):
        """
        Print plain text
        
        Args:
            text: Text to print
            font: Font type ('a' or 'b')
            align: Text alignment ('left', 'center', 'right')
        """
        if not self.printer:
            raise RuntimeError("Printer not initialized")
        
        self.printer.set_with_default(font=font, align=align)
        self.printer.text(text + '\n')
    
    def print_image(self, image: Image.Image, impl: str = 'bitImageColumn'):
        """
        Print image (for Arabic text rendering)
        
        Args:
            image: PIL Image object
            impl: Implementation method for image printing
        """
        if not self.printer:
            raise RuntimeError("Printer not initialized")
        
        # Convert to black and white
        image = image.convert('1')
        
        # Print image
        self.printer.image(image, impl=impl)
    
    def print_barcode(self, code: str, barcode_type: str = 'CODE128'):
        """
        Print barcode
        
        Args:
            code: Barcode data
            barcode_type: Barcode type (CODE128, EAN13, etc.)
        """
        if not self.printer:
            raise RuntimeError("Printer not initialized")
        
        self.printer.barcode(code, barcode_type)
    
    def print_qr(self, data: str, size: int = 6):
        """
        Print QR code
        
        Args:
            data: QR code data
            size: QR code size (1-16)
        """
        if not self.printer:
            raise RuntimeError("Printer not initialized")
        
        self.printer.qr(data, size=size)
    
    def cut_paper(self, mode: str = 'FULL'):
        """
        Cut paper
        
        Args:
            mode: Cut mode ('FULL' or 'PART')
        """
        if not self.printer:
            raise RuntimeError("Printer not initialized")
        
        self.printer.cut(mode=mode)
    
    def close(self):
        """Close printer connection"""
        if self.printer:
            self.printer.close()
    
    def __enter__(self):
        """Context manager entry"""
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        """Context manager exit"""
        self.close()


class MockEscposAdapter(EscposAdapter):
    """
    Mock ESC/POS adapter for testing
    Captures print commands without actual printing
    """
    
    def __init__(self):
        """Initialize mock adapter"""
        self.printed_text = []
        self.printed_images = []
        self.printed_barcodes = []
        self.printed_qr = []
        self.paper_cut = False
    
    def _initialize_printer(self, **kwargs):
        """Skip printer initialization"""
        pass
    
    def print_text(self, text: str, font: str = 'a', align: str = 'left'):
        """Capture text"""
        self.printed_text.append({
            'text': text,
            'font': font,
            'align': align
        })
    
    def print_image(self, image: Image.Image, impl: str = 'bitImageColumn'):
        """Capture image"""
        self.printed_images.append(image)
    
    def print_barcode(self, code: str, barcode_type: str = 'CODE128'):
        """Capture barcode"""
        self.printed_barcodes.append({
            'code': code,
            'type': barcode_type
        })
    
    def print_qr(self, data: str, size: int = 6):
        """Capture QR code"""
        self.printed_qr.append({
            'data': data,
            'size': size
        })
    
    def cut_paper(self, mode: str = 'FULL'):
        """Capture paper cut"""
        self.paper_cut = True
    
    def close(self):
        """No-op for mock"""
        pass
