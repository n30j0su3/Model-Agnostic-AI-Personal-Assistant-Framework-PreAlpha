#!/usr/bin/env python3
import sys
from pathlib import Path
from pptx import Presentation

def generate_thumbnail_info(pptx_path):
    path = Path(pptx_path)
    if not path.exists():
        return f"Error: {pptx_path} no encontrado."

    prs = Presentation(pptx_path)
    report = f"# Slides Overview: {path.name}\n\n"
    
    for i, slide in enumerate(prs.slides):
        title = slide.shapes.title.text if slide.shapes.title else "Sin Título"
        report += f"## Slide {i+1}: {title}\n"
        # Contar elementos
        report += f"- Elementos: {len(slide.shapes)}\n"
        if slide.has_notes_slide:
            report += f"- Notas: {slide.notes_slide.notes_text_frame.text[:50]}...\n"
        report += "\n"
    
    return report

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Uso: python thumbnail.py <archivo.pptx>")
    else:
        print(generate_thumbnail_info(sys.argv[1]))
