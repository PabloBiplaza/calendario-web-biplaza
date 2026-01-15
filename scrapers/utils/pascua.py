"""
Cálculo de la fecha de Pascua usando el algoritmo de Butcher/Meeus
(mejora del algoritmo de Gauss)
"""

from datetime import date, timedelta


def calcular_pascua(year: int) -> date:
    """
    Calcula la fecha del Domingo de Pascua para un año dado.
    
    Usa el algoritmo de Butcher/Meeus, válido para años 1583-4099.
    
    Args:
        year: Año para calcular Pascua
        
    Returns:
        datetime.date del Domingo de Pascua
        
    Referencias:
        - https://es.wikipedia.org/wiki/Computus
        - Butcher, S. (1876). "Ecclesiastical Calendar"
    """
    
    # Algoritmo de Butcher/Meeus
    a = year % 19
    b = year // 100
    c = year % 100
    d = b // 4
    e = b % 4
    f = (b + 8) // 25
    g = (b - f + 1) // 3
    h = (19 * a + b - d - g + 15) % 30
    i = c // 4
    k = c % 4
    l = (32 + 2 * e + 2 * i - h - k) % 7
    m = (a + 11 * h + 22 * l) // 451
    
    mes = (h + l - 7 * m + 114) // 31
    dia = ((h + l - 7 * m + 114) % 31) + 1
    
    return date(year, mes, dia)


def calcular_jueves_santo(year: int) -> date:
    """Calcula Jueves Santo (3 días antes de Pascua)"""
    pascua = calcular_pascua(year)
    return pascua - timedelta(days=3)


def calcular_viernes_santo(year: int) -> date:
    """Calcula Viernes Santo (2 días antes de Pascua)"""
    pascua = calcular_pascua(year)
    return pascua - timedelta(days=2)


def calcular_lunes_pascua(year: int) -> date:
    """Calcula Lunes de Pascua (1 día después de Pascua)"""
    pascua = calcular_pascua(year)
    return pascua + timedelta(days=1)


def calcular_corpus_christi(year: int) -> date:
    """Calcula Corpus Christi (60 días después de Pascua)"""
    pascua = calcular_pascua(year)
    return pascua + timedelta(days=60)


if __name__ == "__main__":
    # Test con años conocidos
    años_test = {
        2024: (3, 31),  # 31 marzo 2024
        2025: (4, 20),  # 20 abril 2025
        2026: (4, 5),   # 5 abril 2026
        2027: (3, 28),  # 28 marzo 2027
    }
    
    print("🧪 Test del algoritmo de Pascua\n")
    
    for year, (mes_esperado, dia_esperado) in años_test.items():
        pascua = calcular_pascua(year)
        jueves = calcular_jueves_santo(year)
        viernes = calcular_viernes_santo(year)
        lunes = calcular_lunes_pascua(year)
        
        correcto = pascua.month == mes_esperado and pascua.day == dia_esperado
        emoji = "✅" if correcto else "❌"
        
        print(f"{emoji} {year}:")
        print(f"   Domingo de Pascua: {pascua} (esperado: {year}-{mes_esperado:02d}-{dia_esperado:02d})")
        print(f"   Jueves Santo: {jueves}")
        print(f"   Viernes Santo: {viernes}")
        print(f"   Lunes de Pascua: {lunes}")
        print()
