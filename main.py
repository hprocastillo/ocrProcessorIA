import os
import re
import requests
import pytesseract
from pdf2image import convert_from_path


def extract_text_from_pdf(pdf_path, max_pages=3):
    """Convierte las primeras 3 páginas de un PDF en texto usando OCR."""
    images = convert_from_path(pdf_path, first_page=1, last_page=max_pages)
    text = ""
    custom_config = r'--oem 3 --psm 6'
    for image in images:
        text += pytesseract.image_to_string(image, config=custom_config, lang='eng+spa') + "\n"
    return text

def get_prompt(tipo, text):
    """Genera el contenido dinámico del mensaje para OLLAMA según el tipo de documento ingresado por el usuario."""
    prompts = {
        "EMO": (
            f"Analiza el siguiente texto que corresponde a un expediente médico ocupacional o certificado de salud."
            f"Extrae solo el documento de identidad o dni del paciente (8 dígitos) y la fecha del examen medico."
            f"Responde exclusivamente en este formato exacto sin agregar más texto:"
            f"'DNI PACIENTE: [DNI], Fecha Examen: [FECHA]'."
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


def parse_ollama_result(result):
    """Extrae el DNI y la fecha del examen del resultado de OLLAMA.
    Se asume que el resultado sigue el formato:'DNI PACIENTE: [DNI], Fecha Examen: [FECHA]' """
    dni_match = re.search(r'DNI PACIENTE:\s*([0-9]{8})', result)
    fecha_match = re.search(r'Fecha Examen:\s*([\w/\-]+)', result)
    dni = dni_match.group(1) if dni_match else "sin_dni"
    fecha = fecha_match.group(1) if fecha_match else "sin_fecha"
    return dni, fecha


def main():
    folder_path = "C:\\escaneos"
    output_file = "resultado_ollama.txt"

    tipo = input("Introduce el tipo de documento: ").strip()

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

            # Si es un expediente médico, extraemos DNI y Fecha para renombrar el archivo
            if tipo.upper() == "EMO":
                dni, fecha = parse_ollama_result(analysis_result)

                # Saneamos la fecha para que no contenga caracteres inválidos para Windows
                # Ejemplo: reemplazar '/' por '-'
                fecha_limpia = fecha.replace("/", "-").replace("\\", "-")

                # Construir el nuevo nombre: ej. "emo_dni_fecha.pdf"
                new_filename = f"emo_{dni}_{fecha_limpia}.pdf"
                new_pdf_path = os.path.join(folder_path, new_filename)
                try:
                    os.rename(pdf_path, new_pdf_path)
                    print(f"Archivo renombrado a: {new_filename}")
                    filename = new_filename  # Actualizamos el nombre para el reporte
                except Exception as e:
                    print(f"Error al renombrar {filename}: {e}")

            result_entry = f"Documento: {filename}\nResultado: {analysis_result}\n{'-' * 40}"
            results.append(result_entry)
            print(result_entry)

    with open(output_file, "w", encoding="utf-8") as f:
        f.write("\n".join(results))

    print(f"Resultados guardados en {output_file}")

if __name__ == "__main__":
    main()
