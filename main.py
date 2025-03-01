import os
import requests
import pytesseract
from pdf2image import convert_from_path

def extract_text_from_pdf(pdf_path, max_pages=3):
    """Convierte las primeras max_pages páginas de un PDF en texto usando OCR."""
    images = convert_from_path(pdf_path, first_page=1, last_page=max_pages)
    text = ""
    custom_config = r'--oem 3 --psm 6'
    for image in images:
        text += pytesseract.image_to_string(image,config=custom_config, lang='eng+spa') + "\n"
    return text

def get_prompt(tipo, text):
    """Genera el contenido dinámico del mensaje para OLLAMA según el tipo ingresado."""
    prompts = {
        "EMO": (
            f"Analiza el siguiente texto que corresponde a un expediente médico ocupacional. "
            f"Extrae solamente el nombre del paciente, el nombre del medico, el DNI del paciente (8 dígitos) y la fecha del examen. "
            f"Responde exclusivamente en este formato exacto sin agregar más texto: "
            f"'Nombre del paciente: [PACIENTE], nombre del medico:[MEDICO], DNI PACIENTE: [DNI], Fecha Examen: [FECHA]'. "
            f"Aquí tienes el texto: \n{text}"
        ),
        "GRUT": (
            f" El siguiente texto es parte de una guia de remision de unidades de transporte."
            f" identifica la placa del vehiculo, El año de fabricacion del vehiculo."
            f" Si el texto no tiene que ver con guias de remision de unidades de transporte, responde: 'El documento no es una guia de remision'. "
            f" Se muy breve en tus respuestas. Aquí tienes el texto: \n{text}"
        ),
        "Otro": (
            f" Responde: 'No puedo analizar el texto'. "
            f" Aquí tienes el texto: \n{text}"
        )
    }
    return prompts.get(tipo, prompts["Otro"])


def analyze_text_with_ollama(text, tipo):
    """Envía el texto a la API de OLLAMA y devuelve la respuesta."""
    url = "http://localhost:11434/api/chat"
    payload = {
        "model": "gemma2:2b",  # Cambia el modelo si es necesario
        "messages": [
            {"role": "user", "content": get_prompt(tipo, text)}
        ],
        "stream": False
    }
    response = requests.post(url, json=payload)
    return response.json().get("message", {}).get("content", "Error en la respuesta de OLLAMA")

def main():
    folder_path = "C:\\escaneos"
    output_file = "resultado_ollama.txt"

    tipo = input("Introduce el tipo de documento: ")

    if not os.path.exists(folder_path):
        print("La carpeta no existe.")
        return

    results = []

    for filename in os.listdir(folder_path):
        if filename.lower().endswith(".pdf"):
            pdf_path = os.path.join(folder_path, filename)
            print(f"Procesando: {filename}")

            extracted_text = extract_text_from_pdf(pdf_path)
            analysis_result = analyze_text_with_ollama(extracted_text, tipo)

            result_entry = f"Documento: {filename}\nResultado: {analysis_result}\n{'-' * 40}"
            results.append(result_entry)
            print(result_entry)

    with open(output_file, "w", encoding="utf-8") as f:
        f.write("\n".join(results))

    print(f"Resultados guardados en {output_file}")

if __name__ == "__main__":
    main()
