import psutil

text_info = """
Информация о системе:

Кол-во ядер: %s
Кол-во ОЗУ: %s МБ

Загруженность ОЗУ: %s %%
Загруженность ЦП: %s %%
"""


class SystemInfo:
    @staticmethod
    def get_info_text():
        cpu = psutil.cpu_percent(interval=1)
        memory = psutil.virtual_memory()
        memory_percent = memory.percent
        memory_amount = '{:.2f}'.format(memory.total / 1024 / 1024)

        text = text_info % (
            psutil.cpu_count(),
            memory_amount,
            memory_percent,
            cpu)

        return text


