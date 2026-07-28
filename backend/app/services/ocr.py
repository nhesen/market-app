import re
from dataclasses import dataclass

PATTERNS=(r"\b\d{2}[./-]\d{2}[./-]\d{4}\b",r"\b\d{2}[./-]\d{2}[./-]\d{2}\b",r"\b\d{4}-\d{2}-\d{2}\b")
@dataclass
class OCRResult:
    candidates:list[str];engine:str;simulated:bool;requires_confirmation:bool=True

def extract_date_candidates(text:str)->list[str]:
    found=[]
    for pattern in PATTERNS:
        for value in re.findall(pattern,text):
            if value not in found: found.append(value)
    return found

def process_demo_text(text:str)->OCRResult:
    """Deterministic fallback used when PaddleOCR/EasyOCR is unavailable; always labelled simulated."""
    return OCRResult(candidates=extract_date_candidates(text),engine="deterministic-demo",simulated=True)

def process_image_bytes(data:bytes)->OCRResult:
    """Uses EasyOCR when installed; otherwise returns an explicit manual-entry fallback."""
    try:
        import cv2,numpy as np,easyocr
        image=cv2.imdecode(np.frombuffer(data,np.uint8),cv2.IMREAD_COLOR)
        if image is None:return OCRResult([],"unreadable-image",False)
        gray=cv2.cvtColor(image,cv2.COLOR_BGR2GRAY);gray=cv2.createCLAHE(2.0,(8,8)).apply(gray)
        reader=easyocr.Reader(["en"],gpu=False);text=" ".join(reader.readtext(gray,detail=0))
        return OCRResult(extract_date_candidates(text),"easyocr",False)
    except ImportError:return OCRResult([],"manual-fallback",True)
    except Exception:return OCRResult([],"ocr-error-manual-fallback",True)
