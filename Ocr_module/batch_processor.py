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
            
            templates = template_dict if isinstance(template_dict, list) else [template_dict]
            # A two-page ledger spread has one physical row split across its odd
            # (left) and even (right) page - the row boundaries detected on the
            # odd page are carried over (as fractions of page height, since the
            # two sides can render at slightly different pixel heights) so the
            # even page's rows line up with the same entries instead of being
            # detected independently and potentially drifting out of alignment.
            pending_row_fractions = None
            for page_num in range(len(doc)):
                page_parity = "even" if (page_num + 1) % 2 == 0 else "odd"
                page_template = next(
                    (template for template in templates
                     if (template.get("metadata") or {}).get("pageParity", "current") == page_parity),
                    next((template for template in templates
                          if (template.get("metadata") or {}).get("pageParity", "current") == "current"),
                         templates[0])
                )
                forced_row_fractions = pending_row_fractions if page_parity == "even" else None
                page_result = self.process_pdf_page(
                    doc,
                    page_num,
                    page_template,
                    auto_align,
                    forced_row_fractions=forced_row_fractions
                )
                page_result["template_name"] = page_template.get("name")
                page_result["template_parity"] = (page_template.get("metadata") or {}).get("pageParity", "current")

                rows_used = page_result.pop("rows_used", [])
                image_height = page_result.pop("image_height", 0)
                if page_parity == "odd" and rows_used and image_height:
                    pending_row_fractions = [
                        {
                            "yFrac": row["y"] / image_height,
                            "heightFrac": row["height"] / image_height,
                            "spacingFrac": row.get("spacing", 0) / image_height
                        }
                        for row in rows_used
                    ]
                else:
                    pending_row_fractions = None

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
                        doc,
                        page_num: int,
                        template_dict: Dict[str, Any],
                        auto_align: bool = True,
                        forced_row_fractions: Optional[List[Dict[str, float]]] = None) -> Dict[str, Any]:
        """
        Process single PDF page.

        Args:
            doc: PDF document
            page_num: Page number (0-indexed)
            template_dict: Template configuration
            auto_align: Whether to auto-align template
            forced_row_fractions: Row y/height/spacing as fractions of page
                height, carried over from the paired page of a two-page
                spread, in place of detecting rows on this page.

        Returns:
            Dictionary with page results. Includes internal "rows_used" and
            "image_height" keys (in pixel space) for the caller to derive
            forced_row_fractions for a paired page - process_pdf() strips
            these before returning results.
        """
        page_result = {
            "page_number": page_num + 1,
            "success": False,
            "cells": [],
            "alignment": None,
            "rows_used": [],
            "image_height": 0,
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

            page_result["image_height"] = image.shape[0]

            forced_rows = None
            if forced_row_fractions:
                h = image.shape[0]
                forced_rows = [
                    {
                        "y": frac.get("yFrac", 0) * h,
                        "height": frac.get("heightFrac", 0) * h,
                        "spacing": frac.get("spacingFrac", 0) * h
                    }
                    for frac in forced_row_fractions
                ]

            # Auto-place template on page
            placement = self.detector.auto_place_template(
                image,
                template_dict,
                auto_align=auto_align,
                forced_rows=forced_rows
            )

            if not placement["success"]:
                page_result["error"] = "Failed to place template"
                return page_result

            # Extract cell information
            page_result["alignment"] = placement.get("alignment")
            page_result["rows_used"] = placement.get("rows", [])

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
