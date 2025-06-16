import re


async def compress_text(text):
    max_length = 2000
    return text[:max_length] if len(text) > max_length else text


def escape_markdown_v2(text):
    """Экранирует специальные символы для MarkdownV2 и форматирует список тем"""
    escape_chars = r"_*[]()~`>#+-=|{}.!"

    # Если передан список кортежей (id, title, url), форматируем в MarkdownV2
    if isinstance(text, list):
        formatted_text = []
        for topic in text:
            topic_id = str(topic.get("id", ""))
            title = topic.get("title", "")
            url = topic.get("url", "")
            if url:
                formatted_text.append(f" {topic_id}.\n {title}\n({url})\n")
            else:
                formatted_text.append(f" {topic_id}.\n {title}\n")

        text = "".join(formatted_text)

    # Экранируем специальные символы ля MarkdownV2
    return re.sub(f"([{re.escape(escape_chars)}])", r"\\\1", text)

def convert_to_telegram_markdown(text):
    """
    Конвертирует текст в Markdown V2 формат для Telegram с учетом правил экранирования.

    Правила форматирования в Telegram Markdown V2:
    - *bold* - жирный текст (в исходном тексте может быть **bold**)
    - _italic_ - курсив
    - __underline__ - подчеркнутый текст
    - ~strikethrough~ - зачеркнутый текст (в исходном тексте может быть ~~text~~)
    - ||spoiler|| - спойлер
    - `code` - моноширинный шрифт
    - ```code block``` - блок кода
    - [text](url) - ссылка

    Дополнительные преобразования:
    - Заголовки (#, ##, ###) преобразуются в жирный текст

    Правила экранирования:
    1. Внутри блоков кода все символы '`' и '\' должны быть экранированы с помощью '\'
    2. Внутри круглых скобок ссылок (...) все символы ')' и '\' должны быть экранированы с помощью '\'
    3. В обычном тексте все специальные символы должны быть экранированы

    Args:
        text (str): Исходный текст

    Returns:
        str: Текст в Markdown V2 формате для Telegram
    """
    # Предварительная обработка: заменяем двойные маркеры на одинарные
    # Например, **жирный текст** -> *жирный текст*

    # Заменяем **текст** на *текст* (жирный)
    text = re.sub(r'\*\*(.*?)\*\*', r'*\1*', text)

    # Заменяем ~~текст~~ на ~текст~ (зачеркнутый)
    text = re.sub(r'~~(.*?)~~', r'~\1~', text)

    # Обработка заголовков - преобразование в жирный текст
    # Например, # Заголовок -> *Заголовок*
    lines = []
    for line in text.split('\n'):
        # Проверяем, является ли строка заголовком (начинается с #)
        header_match = re.match(r'^(#{1,6})\s+(.+)$', line.strip())
        if header_match:
            # Извлекаем текст заголовка
            header_text = header_match.group(2)
            # Преобразуем в жирный текст
            lines.append(f'*{header_text}*')
        else:
            lines.append(line)

    text = '\n'.join(lines)

    lines = text.split('\n')
    result_lines = []

    in_code_block = False
    code_block_lines = []

    # Обрабатываем текст построчно
    for line in lines:
        # Проверка блока кода
        if line.strip().startswith('```') and not in_code_block:
            in_code_block = True
            result_lines.append('```')
            # Если после ``` есть еще текст, сохраняем его
            if line.strip()[3:].strip():
                code_block_lines.append(line.strip()[3:].strip())
            continue
        elif line.strip().startswith('```') and in_code_block:
            in_code_block = False
            # Обработка содержимого блока кода
            for code_line in code_block_lines:
                # Экранируем только ` и \ внутри блока кода
                escaped_line = ''
                for char in code_line:
                    if char in ['`', '\\']:
                        escaped_line += '\\' + char
                    else:
                        escaped_line += char
                result_lines.append(escaped_line)

            code_block_lines = []
            result_lines.append('```')
            continue

        # Сохраняем строки внутри блока кода
        if in_code_block:
            # Для первой строки убираем лишние пробелы в начале
            if not code_block_lines:
                code_block_lines.append(line.lstrip())
            else:
                code_block_lines.append(line)
            continue

        # Обработка обычного текста
        processed_line = ''

        # Определяем все области форматирования в строке
        formatting_regions = []

        # Проверяем все возможные форматирования в строке
        # Жирный текст (одинарные звездочки)
        bold_positions = []
        for match in re.finditer(r'\*(.*?)\*', line):
            start, end = match.span()
            bold_positions.append((start, end))
            formatting_regions.append((start, start + 1, "format_start"))  # Начало формата
            formatting_regions.append((end - 1, end, "format_end"))  # Конец формата

        # Курсив (одинарное подчеркивание)
        italic_positions = []
        for match in re.finditer(r'_(.*?)_', line):
            start, end = match.span()
            # Проверяем, что это не часть слова (например, not_a_format)
            prev_char = line[start - 1] if start > 0 else ' '
            next_char = line[end] if end < len(line) else ' '
            if not (prev_char.isalnum() and next_char.isalnum()):
                italic_positions.append((start, end))
                formatting_regions.append((start, start + 1, "format_start"))
                formatting_regions.append((end - 1, end, "format_end"))

        # Зачеркнутый текст (одинарная тильда)
        strike_positions = []
        for match in re.finditer(r'~(.*?)~', line):
            start, end = match.span()
            strike_positions.append((start, end))
            formatting_regions.append((start, start + 1, "format_start"))
            formatting_regions.append((end - 1, end, "format_end"))

        # Спойлер
        spoiler_positions = []
        for match in re.finditer(r'\|\|(.*?)\|\|', line):
            start, end = match.span()
            spoiler_positions.append((start, end))
            formatting_regions.append((start, start + 2, "format_start"))
            formatting_regions.append((end - 2, end, "format_end"))

        # Код встроенный
        code_positions = []
        for match in re.finditer(r'`(.*?)`', line):
            start, end = match.span()
            code_positions.append((start, end))
            formatting_regions.append((start, start + 1, "code_start"))
            formatting_regions.append((end - 1, end, "code_end"))

        # Ссылки
        link_positions = []
        for match in re.finditer(r'\[(.*?)\]\((.*?)\)', line):
            start, end = match.span()
            text_end = line.find(']', start)
            url_start = text_end + 1
            link_positions.append((start, end))
            formatting_regions.append((start, start + 1, "link_text_start"))
            formatting_regions.append((text_end, text_end + 1, "link_text_end"))
            formatting_regions.append((url_start, url_start + 1, "link_url_start"))
            # Внутри URL экранируем только ) и \
            for j in range(url_start + 1, end - 1):
                if line[j] in [')', '\\']:
                    formatting_regions.append((j, j + 1, "link_url_escape"))
            formatting_regions.append((end - 1, end, "link_url_end"))

        # Сортируем регионы по начальной позиции
        formatting_regions.sort(key=lambda x: x[0])

        # Обрабатываем строку с учетом форматирования
        in_code = False
        in_link_url = False
        i = 0

        while i < len(line):
            # Проверяем, находимся ли мы в форматированной области
            current_region = None
            for region in formatting_regions:
                if region[0] == i:
                    current_region = region
                    break

            if current_region:
                start, end, region_type = current_region

                if region_type == "code_start":
                    in_code = True
                    processed_line += '`'
                    i = end
                elif region_type == "code_end":
                    in_code = False
                    processed_line += '`'
                    i = end
                elif region_type == "link_url_start":
                    in_link_url = True
                    processed_line += '('
                    i = end
                elif region_type == "link_url_end":
                    in_link_url = False
                    processed_line += ')'
                    i = end
                elif region_type == "link_url_escape":
                    # Внутри URL экранируем ) и \
                    processed_line += '\\' + line[i]
                    i = end
                elif region_type in ["format_start", "format_end", "link_text_start", "link_text_end"]:
                    # Добавляем форматирование без изменений
                    processed_line += line[start:end]
                    i = end
                else:
                    # Неизвестный тип региона
                    processed_line += line[i]
                    i += 1
            else:
                # Не в форматированной области
                if in_code:
                    # В коде экранируем только ` и \
                    if line[i] in ['`', '\\']:
                        processed_line += '\\' + line[i]
                    else:
                        processed_line += line[i]
                elif in_link_url:
                    # В URL экранируем только ) и \
                    if line[i] in [')', '\\']:
                        processed_line += '\\' + line[i]
                    else:
                        processed_line += line[i]
                else:
                    # Обычный текст - экранируем специальные символы
                    if line[i] in ['_', '*', '[', ']', '(', ')', '~', '`', '>', '#', '+', '-', '=', '|', '{', '}', '.',
                                   '!']:
                        processed_line += '\\' + line[i]
                    else:
                        processed_line += line[i]
                i += 1

        result_lines.append(processed_line)

    return '\n'.join(result_lines)

