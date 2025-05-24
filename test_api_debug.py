import sys
sys.path.append('src')

# Импортируем функции напрямую
from services.helper import extract_text_pages, detect_lab_type, extract_cbc_values

# Читаем тот же файл, что и API
with open('../docs/Махутова.pdf', 'rb') as f:
    pdf_bytes = f.read()

# Выполняем те же шаги, что и в API
pages = extract_text_pages(pdf_bytes)
print(f"Извлечено страниц: {len(pages)}")

lab_type = detect_lab_type(pages)
print(f"Тип лаборатории: {lab_type}")

# Вызываем функцию извлечения данных
cbc_data = extract_cbc_values(pages)
print(f"\nРезультат extract_cbc_values:")
for key, value in cbc_data.items():
    print(f"  {key}: {value}")

# Проверяем, какие процентные значения найдены
percent_fields = ['neutrophils_percent', 'lymphocytes_percent', 'monocytes_percent', 'eosinophils_percent', 'basophils_percent']
print(f"\nПроцентные значения:")
for field in percent_fields:
    value = cbc_data.get(field)
    status = "✓" if value is not None else "✗"
    print(f"  {status} {field}: {value}") 