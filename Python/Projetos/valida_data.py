def is_leap_year(year: int) -> bool:
    return (year % 4 == 0 and year % 100 != 0) or (year % 400 == 0)


def is_valid_date(date_str: str) -> bool:
    parts = date_str.split('/')
    if len(parts) != 3:
        return False

    day_str, month_str, year_str = parts
    if not (day_str.isdigit() and month_str.isdigit() and year_str.isdigit()):
        return False

    day = int(day_str)
    month = int(month_str)
    year = int(year_str)

    if year < 1:
        return False
    if month < 1 or month > 12:
        return False

    # dias por mês
    days_in_month = [31, 29 if is_leap_year(year) else 28, 31, 30, 31, 30, 31, 31, 30, 31, 30, 31]

    if day < 1 or day > days_in_month[month - 1]:
        return False

    return True


def main() -> None:
    try:
        date_input = input('Informe uma data (dd/mm/aaaa): ').strip()
    except EOFError:
        print('Entrada não fornecida.')
        return

    if is_valid_date(date_input):
        print('Data válida')
    else:
        print('Data inválida')


if __name__ == '__main__':
    main()
