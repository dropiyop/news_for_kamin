import re


def escape_markdown(text: str) -> str:
    """Экранирует специальные символы MarkdownV2"""
    escape_chars = r"_*[]()~`>#+-=|{}.!<>"
    return re.sub(r"([%s])" % re.escape(escape_chars), r"\\\1", text)


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

    # Экранируем специальные символы для MarkdownV2
    return re.sub(f"([{re.escape(escape_chars)}])", r"\\\1", text)

