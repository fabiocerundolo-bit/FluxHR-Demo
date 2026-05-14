import os, re, io, uuid, pdfplumber, docx
from sqlalchemy.orm import Session
from ..models import Candidate

class CVParserService:
    def sanitize(self, text: str) -> str:
        text = re.sub(r"(?i)(allergia|disabilità|malattia|disturbo|diagnosi|patologia|fumatore|obesità|gravidanza).*?[.\n]", "[REDATTO - DATO SANITARIO]", text)
        text = re.sub(r"(?i)(partito|sindacato|sciopero|voto|elezioni|democrazia|socialista|comunista|destra|sinistra).*?[.\n]", "[REDATTO - OPINIONE POLITICA]", text)
        text = re.sub(r"(?i)(chiesa|moschea|sinagoga|preghiera|dio|allah|buddista|cattolico|musulmano|ebraico).*?[.\n]", "[REDATTO - CREDO RELIGIOSO]", text)
        return text

    def extract_info(self, text: str):
        email = re.search(r'[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}', text)
        phone = re.search(r'(\+?39\s?)?\d{3}[-\s]?\d{7,8}', text)
        name = re.search(r'^([A-Z][a-z]+\s+[A-Z][a-z]+)', text, re.MULTILINE)
        
        skills = []
        for line in text.split('\n'):
            match = re.search(r'^([A-Za-zÀ-ÿ\s/&]+?)\s*\d+%', line.strip())
            if match: skills.append(match.group(1).strip().title())
        
        return {
            "name": name.group(1) if name else "Candidato Ignoto",
            "email": email.group(0) if email else "unknown@example.com",
            "phone": phone.group(0) if phone else "",
            "skills": list(set(skills))[:10]
        }

    def process_cv(self, contents, filename, db: Session):
        text = ""
        ext = os.path.splitext(filename)[1].lower()
        if ext == '.pdf':
            with pdfplumber.open(io.BytesIO(contents)) as pdf:
                text = "\n".join([p.extract_text() for p in pdf.pages if p.extract_text()])
        elif ext == '.docx':
            doc = docx.Document(io.BytesIO(contents))
            text = "\n".join([p.text for p in doc.paragraphs])

        clean_text = self.sanitize(text)
        data = self.extract_info(clean_text)
        
        unique_name = f"{uuid.uuid4().hex}{ext}"
        save_path = f"uploads/{unique_name}"
        os.makedirs("uploads", exist_ok=True)
        with open(save_path, "wb") as f: f.write(contents)

        candidate = Candidate(**data, cv_file_path=save_path)
        db.add(candidate)
        db.commit()
        return candidate

cv_parser = CVParserService()