# payments/card_validator.py
"""
Validador de tarjetas de crédito/débito.
Implementa validación de formato, fecha de expiración y algoritmo de Luhn.
"""

import re
from datetime import datetime

class CardValidator:
    """
    Clase para validar tarjetas de crédito/débito.
    """
    #No realiza cargos reales, solo verifica que los datos sean correctos.
    # Patrones de marcas de tarjetas (expresiones regulares)
    CARD_PATTERNS = {
        'VISA': r'^4[0-9]{12}(?:[0-9]{3})?$',
        'MASTERCARD': r'^(5[1-5][0-9]{14}|2(2[2-9][0-9]{12}|[3-6][0-9]{13}|7[0-1][0-9]{12}|720[0-9]{12}))$',
        'AMERICAN_EXPRESS': r'^3[47][0-9]{13}$',
        'DISCOVER': r'^6(?:011|5[0-9]{2})[0-9]{12}$',
        'DINERS_CLUB': r'^3(?:0[0-5]|[68][0-9])[0-9]{11}$',
        'JCB': r'^(?:2131|1800|35[0-9]{3})[0-9]{11}$',
    }
    
    @classmethod
    def validate_card_number(cls, card_number):
        """
        Valida el número de tarjeta usando el algoritmo de Luhn.
        
        Parámetros:
        - card_number: str - Número de tarjeta (puede contener espacios)
        
        Retorna:
        - tuple: (es_valido, mensaje, marca)
        """
        # Limpiar el número (quitar espacios y guiones)
        cleaned = re.sub(r'[\s\-]', '', card_number)
        
        # Verificar que solo contiene dígitos
        if not cleaned.isdigit():
            return False, "El número de tarjeta solo debe contener dígitos", None
        
        # Verificar longitud mínima (13 dígitos) y máxima (19 dígitos)
        if len(cleaned) < 13:
            return False, "El número de tarjeta es demasiado corto (mínimo 13 dígitos)", None
        
        if len(cleaned) > 19:
            return False, "El número de tarjeta es demasiado largo (máximo 19 dígitos)", None
        
        # Identificar la marca
        brand = None
        for name, pattern in cls.CARD_PATTERNS.items():
            if re.match(pattern, cleaned):
                brand = name
                break
        
        if not brand:
            return False, "Marca de tarjeta no reconocida (Visa, Mastercard, Amex, Discover, Diners Club, JCB)", None
        
        # Algoritmo de Luhn (validación matemática de tarjeta)
        if not cls._luhn_checksum(cleaned):
            return False, "Número de tarjeta inválido (error de checksum)", brand
        
        return True, "Número de tarjeta válido", brand
    
    @classmethod
    def _luhn_checksum(cls, card_number):
        """
        Implementa el algoritmo de Luhn para validar números de tarjeta.
        https://en.wikipedia.org/wiki/Luhn_algorithm
        """
        total = 0
        reverse_digits = card_number[::-1]
        
        for i, digit in enumerate(reverse_digits):
            n = int(digit)
            if i % 2 == 1:  # Posiciones impares (desde la derecha, empezando en 1)
                n *= 2
                if n > 9:
                    n = n - 9
            total += n
        
        return total % 10 == 0
    
    @classmethod
    def validate_expiry_date(cls, expiry_str):
        """
        Valida la fecha de expiración (formato MM/AA o MM/YYYY).
        
        Parámetros:
        - expiry_str: str - Fecha en formato MM/AA o MM/YYYY
        
        Retorna:
        - tuple: (es_valido, mensaje, mes, año)
        """
        # Limpiar la cadena
        cleaned = re.sub(r'[\s/]', '', expiry_str)
        
        # Verificar formato
        if len(cleaned) == 4:  # MMYY
            month = int(cleaned[:2])
            year = int(cleaned[2:4]) + 2000
        elif len(cleaned) == 6:  # MMYYYY
            month = int(cleaned[:2])
            year = int(cleaned[2:6])
        else:
            return False, "Formato inválido. Use MM/AA o MM/AAAA", None, None
        
        # Validar mes (1-12)
        if month < 1 or month > 12:
            return False, "Mes inválido (debe ser entre 01 y 12)", None, None
        
        # Validar que la tarjeta no haya expirado
        now = datetime.now()
        current_year = now.year
        current_month = now.month
        
        if year < current_year:
            return False, f"La tarjeta expiró en {month:02d}/{year}", month, year
        
        if year == current_year and month < current_month:
            return False, f"La tarjeta expiró en {month:02d}/{year}", month, year
        
        return True, "Fecha de expiración válida", month, year
    
    @classmethod
    def validate_cvv(cls, cvv, brand=None):
        """
        Valida el código CVV/CVC.
        
        Parámetros:
        - cvv: str - Código de 3 o 4 dígitos
        - brand: str - Marca de la tarjeta (para validar longitud)
        
        Retorna:
        - tuple: (es_valido, mensaje)
        """
        # Limpiar
        cleaned = re.sub(r'\s', '', cvv)
        
        # Verificar que solo contiene dígitos
        if not cleaned.isdigit():
            return False, "El CVV solo debe contener dígitos"
        
        # American Express usa 4 dígitos, el resto 3
        if brand == 'AMERICAN_EXPRESS':
            if len(cleaned) != 4:
                return False, "American Express requiere CVV de 4 dígitos"
        else:
            if len(cleaned) != 3:
                return False, "El CVV debe tener 3 dígitos"
        
        return True, "CVV válido"
    
    @classmethod
    def validate_card(cls, card_number, expiry_date, cvv, cardholder_name):
        """
        Valida todos los campos de la tarjeta.
        
        Parámetros:
        - card_number: str - Número de tarjeta
        - expiry_date: str - Fecha de expiración (MM/AA)
        - cvv: str - Código de seguridad
        - cardholder_name: str - Nombre del titular
        
        Retorna:
        - tuple: (es_valido, mensaje, datos_validados)
        """
        # Validar nombre del titular
        if not cardholder_name or len(cardholder_name.strip()) < 3:
            return False, "Ingrese el nombre completo del titular", None
        
        # Validar número de tarjeta
        is_valid, msg, brand = cls.validate_card_number(card_number)
        if not is_valid:
            return False, msg, None
        
        # Validar fecha de expiración
        is_valid, msg, month, year = cls.validate_expiry_date(expiry_date)
        if not is_valid:
            return False, msg, None
        
        # Validar CVV
        is_valid, msg = cls.validate_cvv(cvv, brand)
        if not is_valid:
            return False, msg, None
        
        # Datos validados
        validated_data = {
            'brand': brand,
            'last_four': re.sub(r'[\s\-]', '', card_number)[-4:],
            'expiry_month': month,
            'expiry_year': year,
            'cardholder_name': cardholder_name.strip()
        }
        
        return True, "Tarjeta válida", validated_data