Сделай список из глобальных HR-тем только на основе моих тем
мои темы распредели в subtopics
Если темы одинаковые, то выбери только одну    НЕ СОРТИРУЙ так, чтобы одна и та же тема была в 2 разных глобальных категориях
У тебя нет права придумывать темы и подтемы которые не основываются на словаре, который я тебе присылаю
НЕ ПРИДУМЫВАЙ ПОДТЕМЫ, используй только те, что есть. НЕЛЬЗЯ ПРИДУМЫВАТЬ ДРУГИЕ ПОДТЕМЫ    У тебя есть только словарь с темами, не вздумай придумывать свои подтемы    Если ты добавишь свою подтему, у меня сломается база данных, пожалуйста, сортируй только предоставленные темы!
Если словарь с темами пустой, то ты не должен придумывать темы
Если ты все же случайно придумал подтему 
Группируй темы так, чтобы они как можно лучше соответствовали друг другу по смыслу и области HR    Все темы из словаря должны быть распределены    Если уже есть глобальная тема, которая подходит — ни в коем случае не создавай новую, а добавь в неё    Если подтему можно добавить в уже существующую тему — сделай это    - Название общей темы НИКОГДА НЕ ДОЛЖНО ПОВТОРЯТЬСЯ (`title`)    - Дай список подтем (`subtopics`)    Ты сначала формируешь глобальные темы на основе всего словаря, а затем добавляешь в них подходящие подтемы на основе этого же словаря    Ответ верни **в формате JSON** с ключами `topics`, вложенность должна быть строгой    
Пример JSON:    {    '  topics: ['    '    { id: 1, title: Обучение и развитие, subtopics: ['    '     
{ id: 101, title: Наставничество и менторство },'    '      
{ id: 102, title: Платформы для корпоративного обучения }'        ] },    '  
{ id: 2, title: Управление талантами, subtopics: ['    '     
{ id: 201, title: Оценка эффективности сотрудников },'    '      
{ id: 202, title: Perormance review }'        ] }      ]    }