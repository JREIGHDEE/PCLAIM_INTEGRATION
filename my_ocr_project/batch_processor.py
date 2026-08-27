"""
Batch PDF processing with template automation.
"""

import cv2
import fitz
import numpy as np
import os
import tempfile
import json
from typing import List, Dict, Any, Optional
from dataclasses import asdict
from template_engine import (
    TemplateEngine, TemplateAutoDetector, generate_cells,
    Cell, RowTemplate, GridLine
)


class BatchProcessor:
    """Process multiple PDF pages using templates."""
    
    def __init__(self, ocr_function=None):
        """
        Initialize batch processor.
        
        Args:
            ocr_function: Function to call for OCR (receives image numpy array)
        """
        self.ocr_function = ocr_function
        self.detector = TemplateAutoDetector()
    
    def process_pdf(self,
                   pdf_path: str,
                   template_dict: Dict[str, Any],
                   output_path: Optional[str] = None,
                   auto_align: bool = True) -> Dict[str, Any]:
        """
        Process entire PDF with template.
        
        Args:
            pdf_path: Path to PDF file
            template_dict: Template configuration
            output_path: Where to save results (optional)
            auto_align: Whether to auto-align template on each page
        
        Returns:
            Dictionary with results for each page
        """
        results = {
            "success": False,
            "pdf_path": pdf_path,
            "pages": [],
            "total_pages": 0,
            "error": None
        }
        
        try:
            doc = fitz.open(pdf_path)
            results["total_pages"] = len(doc)
            
            for page_num in range(len(doc)):
                page_result = self.process_pdf_page(
                    doc,
                    page_num,
                    template_dict,
                    auto_align
                )
                results["pages"].append(page_result)
            
            doc.close()
            
            # Save results if requested
            if output_path:
                with open(output_path, 'w', encoding='utf-8') as f:
                    # Convert for JSON serialization
                    json_results = {
                        "success": results["success"],
                        "pdf_path": results["pdf_path"],
                        "total_pages": results["total_pages"],
                        "pages": results["pages"]
                    }
                    json.dump(json_results, f, indent=2)
            
            results["success"] = True
        
        except Exception as e:
            results["error"] = str(e)
            if 'doc' in locals():
                doc.close()
        
        return results
    
    def process_pdf_page(self,
                        doc: fitz.Document,
                        page_num: int,
                        template_dict: Dict[str, Any],
                        auto_align: bool = True) -> Dict[str, Any]:
        """
        Process single PDF page.
        
        Args:
            doc: PDF document
            page_num: Page number (0-indexed)
            template_dict: Template configuration
            auto_align: Whether to auto-align template
        
        Returns:
            Dictionary with page results
        """
        page_result = {
            "page_number": page_num + 1,
            "success": False,
            "cells": [],
            "alignment": None,
            "error": None
        }
        
        try:
            # Render page to image
            page = doc[page_num]
            pix = page.get_pixmap(matrix=fitz.Matrix(2, 2))
            
            # Convert to numpy array
            img_data = np.frombuffer(pix.samples, dtype=np.uint8)
            img_data = img_data.reshape((pix.height, pix.width, pix.n))
            
            # Convert to BGR if RGB
            if pix.n == 3:
                image = cv2.cvtColor(img_data, cv2.COLOR_RGB2BGR)
            elif pix.n == 4:
                image = cv2.cvtColor(img_data, cv2.COLOR_RGBA2BGR)
            else:
                image = img_data
            
            # Auto-place template on page
            placement = self.detector.auto_place_template(
                image,
                template_dict,
                auto_align=auto_align
            )
            
            if not placement["success"]:
                page_result["error"] = "Failed to place template"
                return page_result
            
            # Extract cell information
            page_result["alignment"] = placement.get("alignment")
            
            # Reconstruct cells for OCR
            for cell_data in placement.get("cells", []):
                cell = Cell(
                    row=cell_data["row"],
                    column=cell_data["column"],
                    x1=cell_data["x1"],
                    y1=cell_data["y1"],
                    x2=cell_data["x2"],
                    y2=cell_data["y2"]
                )
                
                # Extract crop
                crop_img = self._extract_cell_image(image, cell)
                
                cell_result = {
                    "row": cell.row,
                    "column": cell.column,
                    "x": cell.x1,
                    "y": cell.y1,
                    "width": cell.x2 - cell.x1,
                    "height": cell.y2 - cell.y1,
                    "text": "",
                    "confidence": 0
                }
                
                # OCR if function provided
                if self.ocr_function and crop_img is not None:
                    ocr_result = self.ocr_function(crop_img)
                    if ocr_result:
                        cell_result["text"] = ocr_result.get("text", "")
                        cell_result["confidence"] = ocr_result.get("confidence", 0)
                
                page_result["cells"].append(cell_result)
            
            page_result["success"] = True
        
        except Exception as e:
            page_result["error"] = str(e)
        
        return page_result
    
    def _extract_cell_image(self, image: np.ndarray, cell: Cell) -> Optional[np.ndarray]:
        """Extract cell image from page."""
        if image is None or image.size == 0:
            return None
        
        h, w = image.shape[:2]
        x1 = max(0, int(cell.x1))
        y1 = max(0, int(cell.y1))
        x2 = min(w, int(cell.x2))
        y2 = min(h, int(cell.y2))
        
        if x2 <= x1 or y2 <= y1:
            return None
        
        return image[y1:y2, x1:x2].copy()
