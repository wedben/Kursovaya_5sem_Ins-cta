"""
Импорт грибов и трав из Excel «Грибы_и_травы_Костромская_область.xlsx»
"""
import os
import re
import sys
import zipfile
import xml.etree.ElementTree as ET

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from database import Database
from import_excel_data import clean_text, parse_size_range

NS = 'http://schemas.openxmlformats.org/spreadsheetml/2006/main'
DEFAULT_FILE = os.path.join(
    os.path.dirname(os.path.dirname(__file__)),
    'data',
    'Грибы_и_травы_Костромская_область.xlsx',
)


def _q(tag: str) -> str:
    return f'{{{NS}}}{tag}'


def _col_index(ref: str) -> int:
    m = re.match(r'([A-Z]+)', ref)
    letters = m.group(1) if m else 'A'
    n = 0
    for c in letters:
        n = n * 26 + (ord(c) - 64)
    return n


def _cell_value(cell, shared: list) -> str:
    t = cell.attrib.get('t')
    if t == 'inlineStr':
        is_el = cell.find(_q('is'))
        if is_el is not None:
            return ''.join((n.text or '') for n in is_el.iter() if n.tag.endswith('}t'))
    v = cell.find(_q('v'))
    if v is None or v.text is None:
        return ''
    if t == 's':
        return shared[int(v.text)]
    return v.text


def read_xlsx_sheet(path: str, sheet_path: str) -> list[dict]:
    """Читает лист xlsx в список словарей {заголовок: значение}."""
    with zipfile.ZipFile(path) as z:
        shared = []
        if 'xl/sharedStrings.xml' in z.namelist():
            sroot = ET.fromstring(z.read('xl/sharedStrings.xml'))
            for si in sroot.findall(_q('si')):
                shared.append(''.join((t.text or '') for t in si.iter() if t.tag.endswith('}t')))

        root = ET.fromstring(z.read(sheet_path))
        matrix = []
        for row in root.findall('.//' + _q('row')):
            cells = {}
            for c in row.findall(_q('c')):
                ref = c.attrib.get('r', 'A1')
                cells[_col_index(ref)] = _cell_value(c, shared)
            if cells:
                maxc = max(cells)
                matrix.append([cells.get(i, '') for i in range(1, maxc + 1)])

    if not matrix:
        return []

    headers = [str(h).strip() for h in matrix[0]]
    rows = []
    for raw in matrix[1:]:
        item = {}
        for i, h in enumerate(headers):
            if not h:
                continue
            val = raw[i] if i < len(raw) else ''
            item[h] = clean_text(val) or ''
        if any(item.values()):
            rows.append(item)
    return rows


def _parse_name(name: str) -> tuple[str, str]:
    if not name:
        return '', ''
    m = re.match(r'^(.+?)\s*\(([^)]+)\)\s*$', name.strip())
    if m:
        return m.group(1).strip(), m.group(2).strip()
    return name.strip(), ''


def _size_from_text(text: str) -> tuple:
    if not text:
        return None, None, text
    size_min, size_max = parse_size_range(text)
    if size_min is not None:
        return size_min, size_max, text
    return None, None, text


def import_mushrooms(filename: str = None, clear: bool = True) -> tuple[int, int]:
    filename = filename or DEFAULT_FILE
    sheet_path = 'xl/worksheets/sheet1.xml'
    print(f'\n🍄 Импорт грибов из {filename}...')
    rows = read_xlsx_sheet(filename, sheet_path)
    db = Database()
    conn = db.get_connection()
    cur = conn.cursor()
    if clear:
        cur.execute('TRUNCATE mushrooms RESTART IDENTITY')
        conn.commit()
    cur.close()
    conn.close()

    imported = errors = 0
    for idx, row in enumerate(rows, start=2):
        try:
            name_ru, alt = _parse_name(row.get('Название', ''))
            if not name_ru:
                errors += 1
                continue
            size_min, size_max, size_label = _size_from_text(row.get('Размер', ''))
            desc_parts = []
            if alt:
                desc_parts.append(f'Народное название: {alt}')
            if size_label and size_min is None:
                desc_parts.append(f'Размер: {size_label}')
            if row.get('Шляпка'):
                desc_parts.append(f'Шляпка: {row["Шляпка"]}')
            if row.get('Ножка'):
                desc_parts.append(f'Ножка: {row["Ножка"]}')
            if row.get('Как растёт'):
                desc_parts.append(f'Как растёт: {row["Как растёт"]}')
            if row.get('Основное применение'):
                desc_parts.append(f'Применение: {row["Основное применение"]}')

            data = {
                'name_ru': name_ru,
                'name_lat': alt or None,
                'size_min': size_min,
                'size_max': size_max,
                'color': row.get('Шляпка') or None,
                'habitat': row.get('Где растёт') or None,
                'season': row.get('Время') or None,
                'description': '; '.join(desc_parts) if desc_parts else None,
            }
            db.add_insect('mushroom', data)
            imported += 1
        except Exception as e:
            print(f'  ❌ Строка {idx}: {e}')
            errors += 1
    print(f'✅ Импортировано грибов: {imported}')
    return imported, errors


def _infer_herb_discovery_period(collect_when: str) -> str:
    """Период обнаружения по фазе (из поля «когда собирать» в исходнике)."""
    mapping = {
        'До цветения': 'весна',
        'В начале цветения': 'весна–лето',
        'В полном цвету': 'лето',
    }
    return mapping.get((collect_when or '').strip(), 'весна–лето')


def import_herbs(filename: str = None, clear: bool = True) -> tuple[int, int]:
    filename = filename or DEFAULT_FILE
    sheet_path = 'xl/worksheets/sheet2.xml'
    print(f'\n🌿 Импорт трав из {filename}...')
    rows = read_xlsx_sheet(filename, sheet_path)
    db = Database()
    conn = db.get_connection()
    cur = conn.cursor()
    if clear:
        cur.execute('TRUNCATE herbs RESTART IDENTITY')
        conn.commit()
    cur.close()
    conn.close()

    imported = errors = 0
    for idx, row in enumerate(rows, start=2):
        try:
            name_ru = (row.get('Название') or '').strip()
            if not name_ru:
                errors += 1
                continue
            size_min, size_max, height_label = _size_from_text(row.get('Высота', ''))
            desc_parts = []
            if row.get('Жизненная форма'):
                desc_parts.append(f'Жизненная форма: {row["Жизненная форма"]}')
            if height_label and size_min is None:
                desc_parts.append(f'Высота: {height_label}')
            if row.get('Лист'):
                desc_parts.append(f'Лист: {row["Лист"]}')
            if row.get('Аромат'):
                desc_parts.append(f'Аромат: {row["Аромат"]}')
            if row.get('Как сушить'):
                desc_parts.append(f'Как сушить: {row["Как сушить"]}')
            if row.get('Основное применение'):
                desc_parts.append(f'Применение: {row["Основное применение"]}')
            flower_state = (row.get('Когда собирать') or '').strip()
            if flower_state:
                desc_parts.append(f'Состояние цветов: {flower_state}')

            data = {
                'name_ru': name_ru,
                'name_lat': None,
                'size_min': size_min,
                'size_max': size_max,
                'color': row.get('Цветок') or None,
                'habitat': row.get('Где растёт') or None,
                'season': _infer_herb_discovery_period(flower_state),
                'description': '; '.join(desc_parts) if desc_parts else None,
            }
            db.add_insect('herb', data)
            imported += 1
        except Exception as e:
            print(f'  ❌ Строка {idx}: {e}')
            errors += 1
    print(f'✅ Импортировано трав: {imported}')
    return imported, errors


def main():
    print('=' * 60)
    print('📥 ИМПОРТ ГРИБОВ И ТРАВ')
    print('=' * 60)
    m_ok, m_err = import_mushrooms()
    h_ok, h_err = import_herbs()
    print('\n' + '=' * 60)
    print(f'✅ Всего: {m_ok + h_ok}, ошибок: {m_err + h_err}')
    print('=' * 60)


if __name__ == '__main__':
    main()
