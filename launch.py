# from playwright.async_api import async_playwright, BrowserContext
from patchright.async_api import async_playwright, BrowserContext
import json
import asyncio
import time
import random
import os
import pickle
import sys
from browserforge.fingerprints import FingerprintGenerator
from browserforge.fingerprints import Fingerprint
from browserforge.headers import Browser
from browserforge.injectors.utils import InjectFunction, only_injectable_headers

import importlib
import pandas as pd

from utilities import random_pause




def load_config(path="parametrs.xlsx"):
    # Получения включённых аков
    acc_df = pd.read_excel(path, sheet_name="Аккаунты")
    acc_df = acc_df[acc_df["Вкл\\выкл (1\\0)"] == 1]
    acc_df['id'] = acc_df['id'].astype(int)

    # Получение конфигурации по функциям
    df_function = pd.read_excel(path, sheet_name="Используемые функции")
    df_function = df_function[df_function["Вкл\\выкл (1\\0)"] == 1]

    function_df = df_function
    # Получение пути к папке расширений
    settings_df = pd.read_excel(path, sheet_name="Общие настройки", header=None)
    folder_row = settings_df[settings_df[0] == "Папка с расширениями"]
    if folder_row.empty:
        raise ValueError("Не найдена строка 'Папка с расширениями' в 'Общие настройки'")
    extensions_folder = folder_row.iloc[0, 1]
    num_threads = int(settings_df[settings_df[0] == "Количество потоков"].iloc[0, 1])


    # Получение включённых расширений
    ext_df = pd.read_excel(path, sheet_name="Используемые расширения")
    enabled_ext_ids = set(ext_df[ext_df["Вкл\\выкл (1\\0)"] == 1]["id"])

    # Из функций достаём нужные расширения
    needed_ext_ids = set()
    needed_column = df_function["Нужные расширения"].dropna().astype(str)
    for entry in needed_column:
        needed_ext_ids.update(map(str.strip, entry.split(";")))

    # Итоговый список: пересечение нужных и включённых
    final_ext_ids = enabled_ext_ids.union(needed_ext_ids)

    # Собираем абсолютные пути
    extension_paths = [get_extension_path(extensions_folder, ext_id) for ext_id in final_ext_ids]

    try:
        pause_start = int(settings_df[settings_df[0] == "Рандомная пауза старт (сек)"].iloc[0, 1])
        pause_end = int(settings_df[settings_df[0] == "Рандомная пауза конец (сек)"].iloc[0, 1])
        if pause_start < 0 or pause_end < 0 or pause_end < pause_start:
            raise ValueError
        use_random_delay = True
    except:
        pause_start = pause_end = 0
        use_random_delay = False

    # Ручной режим
    try:
        manual_mode = int(settings_df[settings_df[0] == "Ручной режим (0/1)"].iloc[0, 1]) == 1
    except:
        manual_mode = False

    return function_df, extension_paths, acc_df, num_threads, use_random_delay, pause_start, pause_end, manual_mode



async def run_enabled_functions_async(function_df, context, account_id):
    # Здесь function_df уже подготовлен с учётом рандомизации для этого аккаунта
    for _, row in function_df.iterrows():
        module_name = row["Название модуля"]
        function_name = row["Название функции"]
        args_raw = row.get("Аргументы", "")

        additional_args = [arg.strip() for arg in str(args_raw).split(";") if arg.strip()] if pd.notna(args_raw) else []
        all_args = [context, account_id] + additional_args

        try:
            module = importlib.import_module(module_name)
            func = getattr(module, function_name)

            print(f"Аккаунт {account_id} ▶ Запуск: {module_name}.{function_name}({', '.join(map(str, all_args[2:]))})")

            if asyncio.iscoroutinefunction(func):
                await func(*all_args)
            else:
                func(*all_args)

        except Exception as e:
            print(f"❌ Ошибка при запуске {module_name}.{function_name}(): {e}")

def get_extension_path(extensions_folder, extension_id):
    # Путь к папке расширения по его ID
    extension_dir = os.path.join(extensions_folder, extension_id)

    # Получение всех подкаталогов (версий) внутри папки расширения
    version_folders = [folder for folder in os.listdir(extension_dir) if
                       os.path.isdir(os.path.join(extension_dir, folder))]

    # Проверка, есть ли версии
    if not version_folders:
        raise FileNotFoundError(f"Нет версий для расширения {extension_id} в {extension_dir}")

    # Выбираем последнюю версию (по алфавитному порядку, если версии правильно именованы)
    latest_version_folder = sorted(version_folders)[-1]

    # Возвращаем полный путь к последней версии
    return os.path.join(extension_dir, latest_version_folder)

def prepare_function_df_for_account(function_df, account_id):
    # Фиксированная часть — с указанной очередностью
    df_fixed = function_df[pd.to_numeric(function_df["Очерёдность выполнения"], errors="coerce").notnull()].copy()
    df_fixed["Очерёдность выполнения"] = df_fixed["Очерёдность выполнения"].astype(float)
    df_fixed = df_fixed.sort_values("Очерёдность выполнения")

    # Рандомная часть — с null в порядке, перемешиваем по seed
    df_random = function_df[pd.to_numeric(function_df["Очерёдность выполнения"], errors="coerce").isnull()].copy()

    # Создаем генератор случайных чисел с сидом, зависящим от account_id, чтобы получить уникальный порядок для каждого аккаунта
    rnd = random.Random(account_id)
    df_random = df_random.sample(frac=1, random_state=rnd.randint(0, 1 << 30)).reset_index(drop=True)

    # Итог — конкатенация фиксированной и рандомной частей
    result_df = pd.concat([df_fixed, df_random], ignore_index=True)
    return result_df

def load_or_create_fingerprint(account_id: int):
    folder_path = f"./accounts/account_{account_id}/"
    file_path = os.path.join(folder_path, f"account_{account_id}.txt")

    # Создание папки, если её нет
    os.makedirs(folder_path, exist_ok=True)

    folder_path = f"./accounts/account_{account_id}/"
    file_path = os.path.join(folder_path, f"account_{account_id}.pkl")

    os.makedirs(folder_path, exist_ok=True)

    if not os.path.exists(file_path):
        # Генерация fingerprint
        fingerprint = FingerprintGenerator(
            browser=[Browser(name='chrome', min_version=136, max_version=136)],
            os=('windows', 'macos'),
            device='desktop',
            locale=('en-US',),
            http_version=2
            # mock_webrtc=True
        ).generate()

        # Сохранение в файл с помощью pickle
        with open(file_path, "wb") as f:
            pickle.dump(fingerprint, f)

        return fingerprint

    else:
        # Загрузка из файла с помощью pickle
        with open(file_path, "rb") as f:
            fingerprint = pickle.load(f)
        return fingerprint

config_df, extension_paths, acc_df, num_threads, use_random_delay, pause_start, pause_end, manual_mode = load_config()
extensions_arg  = ",".join(extension_paths)


async def start_browser(account_id):
    fingerprint = load_or_create_fingerprint(account_id)
    acc_row = acc_df[acc_df["id"] == account_id].iloc[0]
    proxy_config = acc_row['proxy (ip:port:username:password)'].split(":")
    proxy_config = {
        "server": f'http://{proxy_config[0]}:{proxy_config[1]}',
        "username": proxy_config[2],
        "password": proxy_config[3]
    }
    seed_phrase = acc_row["seed phrase"]


    # Загружаем config и пути к расширениям
    # config_df, extension_paths = load_config()
    # extensions_arg = ",".join(extension_paths)
    account_function_df = prepare_function_df_for_account(config_df, account_id)

    if sys.platform.startswith("win"):
        chrome_path = "chromium_136/win/chrome.exe"
    elif sys.platform.startswith("darwin"):  # macOS
        chrome_path = "chromium_136/mac/Google Chrome for Testing.app/Contents/MacOS/Google Chrome for Testing"
    else:
        raise RuntimeError("Unsupported platform for Chromium launcher.")

    async with async_playwright() as p:
        context = await p.chromium.launch_persistent_context(
            executable_path=chrome_path,
            user_data_dir=f"./accounts/account_{account_id}/",
            headless=False,
            proxy=proxy_config,
            user_agent=fingerprint.navigator.userAgent,
            extra_http_headers=only_injectable_headers(
                headers={
                    "Accept-Language": fingerprint.headers.get("Accept-Language", "en-US,en;q=0.9"),
                    **fingerprint.headers
                },
                browser_name="chrome"
            ),

            args=[

                # "--enable-features=UserAgentClientHint",
                # "--disable-blink-features=AutomationControlled",
                f"--disable-extensions-except={extensions_arg}",
                f"--load-extension={extensions_arg}"
            ]
        )

        # await context.add_init_script(
        #     InjectFunction(fingerprint)
        # )

        # with open("patch_webgpu_rtc.js", "r", encoding="utf-8") as f:
        #     patch_script = f.read()
        # await context.add_init_script(patch_script)


        pages = context.pages
        if pages:
            page = pages[0]  # Берём первую вкладку
        else:
            # Если вкладок нет, создаём новую
            page = await context.new_page()



        # Устанавливаем заголовок вкладки с номером аккаунта
        await page.evaluate(f"document.title = 'Account ID: {account_id}';")

        await random_pause(3, 4)

        pages = context.pages  # Получаем список всех открытых вкладок
        for p in pages:
            if p != page:  # Если вкладка не является текущей
                await p.close()

        # Запуск функций
        await run_enabled_functions_async(account_function_df, context, account_id)



        if manual_mode:
            print(f"🕹️ Аккаунт {account_id}: ручной режим активирован. Ожидаем закрытия браузера пользователем...")
            try:
                while context.pages:
                    await asyncio.sleep(2)
            except Exception:
                pass  # Может быть вызвано при закрытии браузера вручную
            print(f"✅ Аккаунт {account_id}: браузер закрыт вручную.")
        else:
            await context.close()


async def delayed_enqueue(account_id, queue, delay_range):
    if delay_range:
        delay = random.randint(*delay_range)
        print(f"🕒 Аккаунт {account_id}: отложен на {delay // 60} мин {delay % 60} сек")
        await asyncio.sleep(delay)
    else:
        print(f"🚀 Аккаунт {account_id}: без задержки")
    await queue.put(account_id)
    print(f"✅ Аккаунт {account_id}: добавлен в очередь")

async def worker(queue: asyncio.Queue):
    while True:
        try:
            account_id = await queue.get()
        except asyncio.CancelledError:
            break
        try:
            await start_browser(account_id)
        except Exception as e:
            print(f"❌ Ошибка в аккаунте {account_id}: {e}")
        finally:
            queue.task_done()


async def main():
    account_ids = acc_df["id"].tolist()
    queue = asyncio.Queue()

    delay_range = (pause_start, pause_end) if use_random_delay else None

    # Запускаем отложенные enqueue-задачи
    enqueue_tasks = [
        asyncio.create_task(delayed_enqueue(acc_id, queue, delay_range))
        for acc_id in account_ids
    ]

    # Запускаем воркеры
    tasks = [asyncio.create_task(worker(queue)) for _ in range(num_threads)]

    # Ждём завершения всех enqueue-задач
    await asyncio.gather(*enqueue_tasks)

    # Ждём, пока очередь не опустеет
    await queue.join()

    # Завершаем воркеры
    for task in tasks:
        task.cancel()
    await asyncio.gather(*tasks, return_exceptions=True)


if __name__ == "__main__":
    asyncio.run(main())
