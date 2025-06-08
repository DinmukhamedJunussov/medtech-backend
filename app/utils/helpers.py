"""
Вспомогательные функции для MedTech приложения
"""
import re
import uuid
from datetime import datetime
from typing import Optional, Dict, Any, List
from loguru import logger


def generate_session_id() -> str:
    """Генерирует уникальный ID сессии"""
    return str(uuid.uuid4())


def clean_text(text: str) -> str:
    """
    Очищает текст от лишних символов и пробелов
    
    Args:
        text: Исходный текст
        
    Returns:
        str: Очищенный текст
    """
    if not text:
        return ""
    
    # Удаляем лишние пробелы и переносы строк
    text = re.sub(r'\s+', ' ', text.strip())
    
    # Удаляем специальные символы, кроме нужных
    text = re.sub(r'[^\w\s\.,;:!?\-()%/]', '', text)
    
    return text


def extract_numbers_from_text(text: str) -> List[float]:
    """
    Извлекает все числа из текста
    
    Args:
        text: Текст для анализа
        
    Returns:
        List[float]: Список найденных чисел
    """
    pattern = r'[-+]?\d*[.,]\d+|\d+'
    matches = re.findall(pattern, text)
    
    numbers = []
    for match in matches:
        try:
            # Заменяем запятую на точку для корректного парсинга
            number = float(match.replace(',', '.'))
            numbers.append(number)
        except ValueError:
            continue
    
    return numbers


def validate_blood_parameter(value: Optional[float], param_name: str, min_val: float = 0, max_val: float = float('inf')) -> bool:
    """
    Валидирует параметр анализа крови
    
    Args:
        value: Значение параметра
        param_name: Название параметра
        min_val: Минимальное допустимое значение
        max_val: Максимальное допустимое значение
        
    Returns:
        bool: True если значение валидно
    """
    if value is None:
        return False
    
    if not isinstance(value, (int, float)):
        logger.warning(f"Invalid type for {param_name}: {type(value)}")
        return False
    
    if not (min_val <= value <= max_val):
        logger.warning(f"Value {value} for {param_name} is out of range [{min_val}, {max_val}]")
        return False
    
    return True


def format_medical_value(value: Optional[float], unit: str = "", decimal_places: int = 2) -> str:
    """
    Форматирует медицинское значение для отображения
    
    Args:
        value: Значение
        unit: Единица измерения
        decimal_places: Количество знаков после запятой
        
    Returns:
        str: Отформатированное значение
    """
    if value is None:
        return "Не определено"
    
    formatted_value = f"{value:.{decimal_places}f}"
    
    if unit:
        return f"{formatted_value} {unit}"
    
    return formatted_value


def calculate_age_from_date(birth_date: datetime) -> int:
    """
    Рассчитывает возраст по дате рождения
    
    Args:
        birth_date: Дата рождения
        
    Returns:
        int: Возраст в годах
    """
    today = datetime.now()
    age = today.year - birth_date.year
    
    # Проверяем, был ли уже день рождения в этом году
    if today.month < birth_date.month or (today.month == birth_date.month and today.day < birth_date.day):
        age -= 1
    
    return age


def sanitize_filename(filename: str) -> str:
    """
    Очищает имя файла от недопустимых символов
    
    Args:
        filename: Исходное имя файла
        
    Returns:
        str: Очищенное имя файла
    """
    # Удаляем недопустимые символы
    sanitized = re.sub(r'[<>:"/\\|?*]', '_', filename)
    
    # Ограничиваем длину
    if len(sanitized) > 255:
        name, ext = sanitized.rsplit('.', 1) if '.' in sanitized else (sanitized, '')
        max_name_length = 255 - len(ext) - 1 if ext else 255
        sanitized = f"{name[:max_name_length]}.{ext}" if ext else name[:255]
    
    return sanitized


def mask_sensitive_data(data: Dict[str, Any], sensitive_keys: List[str] = None) -> Dict[str, Any]:
    """
    Маскирует чувствительные данные в словаре
    
    Args:
        data: Исходные данные
        sensitive_keys: Список ключей для маскирования
        
    Returns:
        Dict[str, Any]: Данные с замаскированными значениями
    """
    if sensitive_keys is None:
        sensitive_keys = ['password', 'token', 'api_key', 'secret', 'phone', 'email']
    
    masked_data = data.copy()
    
    for key, value in masked_data.items():
        if any(sensitive_key in key.lower() for sensitive_key in sensitive_keys):
            if isinstance(value, str) and len(value) > 4:
                masked_data[key] = f"{value[:2]}***{value[-2:]}"
            else:
                masked_data[key] = "***"
    
    return masked_data


def get_file_extension(filename: str) -> str:
    """
    Получает расширение файла
    
    Args:
        filename: Имя файла
        
    Returns:
        str: Расширение файла (без точки)
    """
    return filename.split('.')[-1].lower() if '.' in filename else ''


def is_valid_file_type(filename: str, allowed_extensions: List[str] = None) -> bool:
    """
    Проверяет, является ли тип файла допустимым
    
    Args:
        filename: Имя файла
        allowed_extensions: Список допустимых расширений
        
    Returns:
        bool: True если тип файла допустим
    """
    if allowed_extensions is None:
        allowed_extensions = ['pdf', 'jpg', 'jpeg', 'png']
    
    extension = get_file_extension(filename)
    return extension in allowed_extensions


def truncate_text(text: str, max_length: int = 100, suffix: str = "...") -> str:
    """
    Обрезает текст до указанной длины
    
    Args:
        text: Исходный текст
        max_length: Максимальная длина
        suffix: Суффикс для обрезанного текста
        
    Returns:
        str: Обрезанный текст
    """
    if len(text) <= max_length:
        return text
    
    return text[:max_length - len(suffix)] + suffix 