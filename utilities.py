import playwright.async_api
from patchright.async_api import async_playwright, BrowserContext
import asyncio
import time
import random
import json
import logging
import pickle
import site
import sys
import re
from pathlib import Path
import os
import pandas as pd


async def random_pause(min_time=2, max_time=4):
    """Функция для случайной паузы между действиями."""
    await asyncio.sleep(random.uniform(min_time, max_time))


async def rabby_add_network(context, account_id, network):
    page_rabby = await context.new_page()
    await page_rabby.goto(f"chrome-extension://acmacodkjbdgmoleebolmdjonilkdbch/popup.html")
    await page_rabby.wait_for_load_state()
    await page_rabby.locator('img[src="/generated/svgs/1103e6043d20c069143b3b85bd9651ff.svg"]').click()
    await page_rabby.get_by_text("Custom Network", exact=True).click()
    await page_rabby.get_by_text("Network", exact=True).click()
    await page_rabby.get_by_text("Quick add from Chainlist", exact=True).first.click()
    await page_rabby.get_by_placeholder('Search custom network name or ID').fill(network)
    if await page_rabby.get_by_text(network, exact=True).count() < 2:
        await page_rabby.get_by_text(network, exact=True).click()
        if await page_rabby.get_by_text("You've already added this chain", exact=True).count() < 1:
            await page_rabby.get_by_text("Confirm", exact=True).click()
    await page_rabby.close()


async def gas_transaction_checker(check_page: playwright.async_api.Page, maximum):
    text_content = await check_page.locator("div.gas-amount").text_content()
    match = re.search(r"[\d.]+", text_content)
    gas_value = float(match.group())
    return gas_value < maximum

async def rabby_wallet_import(context, account_id, password = '228Aboba1488'):
    df = pd.read_excel("parametrs.xlsx", sheet_name="Аккаунты")

    # Фильтруем по ID и получаем seed phrase
    seed_phrase = df[df["id"] == account_id]["seed phrase"].iloc[0].split()
    page_rabby = await context.new_page()
    await page_rabby.goto(f"chrome-extension://acmacodkjbdgmoleebolmdjonilkdbch/index.html#/new-user/import/seed-phrase")
    await page_rabby.wait_for_load_state()
    # await page_rabby.get_by_text("I already have an address",exact=True).click()
    # await page_rabby.get_by_text("Seed Phrase", exact=True).click()
    await random_pause(2,3)
    for i in range(12):
        await page_rabby.locator('input[type="password"]').nth(i).fill(seed_phrase[i])
    # await page_rabby.locator('button[type="submit"]').hover()
    await random_pause(1,2)
    await page_rabby.locator('button[type="submit"]').click()
    await random_pause(1,2)
    if page_rabby.is_closed():
        print(f"🔁 Аккаунт {account_id}: кошелёк уже был импортирован ранее. Пропускаем.")
        return
    await page_rabby.locator('input[id="password"]').fill(password)
    await page_rabby.locator('input[id="confirmPassword"]').fill(password)
    await random_pause(1,2)
    await page_rabby.get_by_text("Confirm", exact=True).click()
    await random_pause()
    await page_rabby.close()
    print(f"✅ Аккаунт {account_id}: кошелёк успешно импортирован с паролем: {password}")

async def cookie_maker(context, account_id):
    websites = [
        'https://www.google.com',
        'https://www.amazon.com',
        'https://apnews.com',
        'https://www.wikipedia.org',
        'https://www.kickstarter.com',
        'https://www.ieee.org',
        'https://www.foxnews.com',
        'https://www.cnn.com',
        'https://www.facebook.com',
        'https://www.mercedes-benz.com/en',
        'https://www.forbes.com',
        'https://www.bankless.com',
        'https://www.championat.com',
        'https://rumble.com',
        'https://pikabu.ru',
        'https://www.youtube.com',
        'https://docs.google.com',
        'https://github.com',
        'https://www.youtube.com',
        'https://rt.pornhub.com',
        'https://www.icloud.com/mail',
        'https://etherscan.io/gastracker',
        'https://twitter.com/home',
        'https://discord.com',
        'https://www.reddit.com'
    ]

    page = await context.new_page()

    # Переход по каждому сайту
    for website in websites:
        try:
            await page.goto(website, timeout = 120000)
            print(f"Account {account_id}: Переход на {website}")

            scroll_duration = 20  # Длительность скроллинга в секундах
            start_time = asyncio.get_event_loop().time()
            while asyncio.get_event_loop().time() - start_time < scroll_duration:
                await page.mouse.wheel(0, 5)  # Скролл вниз на 10 пикселей
                await asyncio.sleep(0.0005) # Пауза между скроллами
        except Exception as e:
            print(account_id, website)

    await page.close()

    print(f"аккаунт номер {account_id} нагулял куки")

async def rabby_login(context, account_id, password ='228Aboba1488'):
    page_rabby = await context.new_page()
    await page_rabby.goto(f"chrome-extension://acmacodkjbdgmoleebolmdjonilkdbch/popup.html")
    await page_rabby.wait_for_load_state()
    await random_pause(2,3)
    if page_rabby.is_closed():
        await rabby_wallet_import(context, account_id, password)
        page_rabby = await context.new_page()
        await page_rabby.goto(f"chrome-extension://acmacodkjbdgmoleebolmdjonilkdbch/popup.html")
        await page_rabby.wait_for_load_state()
        await random_pause(2, 3)
        print(f'🔓 Аккаунт {account_id}: успешный вход в Rabby Wallet.')
        return
    await page_rabby.get_by_placeholder('Enter the Password to Unlock').fill(password)
    await random_pause()
    await page_rabby.locator('button[type="submit"]').click()
    await random_pause()
    await page_rabby.close()
    print(f'🔓 Аккаунт {account_id}: успешный вход в Rabby Wallet.')


async def x_token_auth(context, account_id):
    try:
        acc_df = pd.read_excel("parametrs.xlsx", sheet_name="Аккаунты")
        token = acc_df[acc_df["id"] == account_id].iloc[0]["ct0"]

        page_x = await context.new_page()
        await page_x.goto("https://x.com/")
        await page_x.wait_for_load_state()

        if await page_x.get_by_text("Create account", exact=True).count()< 1:
            print("🔁 Аккаунт {account_id}: X уже авторизован. Пропускаем.")
            return

        if account_id not in acc_df["id"].values:
            print(f"❌ x_token_auth | Аккаунт {account_id}: не найден в таблице аккаунтов!")
            return



        if not isinstance(token, str) or len(token.strip()) == 0:
            print(f"❌ x_token_auth | Аккаунт {account_id}: токен отсутствует или пуст!")
            return

        await context.add_cookies([{
            "name": "ct0",
            "value": token,
            "domain": ".x.com",
            "path": "/",
            "httpOnly": True,
            "secure": True,
            "sameSite": "Lax"
        }])
        await random_pause(3,4)
        await page_x.reload()
        await page_x.wait_for_load_state()
        await random_pause(3, 4)

        print(f"✅ x_token_auth | Аккаунт {account_id}: токен установлен, страница перезагружена")

    except Exception as e:
        print(f"❌ x_token_auth | Аккаунт {account_id}: неожиданная ошибка — {e}")
    finally:
        try:
            await page_x.close()
        except:
            pass

async def x_password_auth(context, account_id):
    page_x = await context.new_page()
    await page_x.goto("https://x.com")
    await page_x.wait_for_load_state()
    await random_pause(2,3)
    if await page_x.get_by_text("Sign in", exact=True).count() < 1:
        print("🔁 Аккаунт {account_id}: X уже авторизован. Пропускаем.")
        return

    acc_df = pd.read_excel("parametrs.xlsx", sheet_name="Аккаунты")
    acc_df = acc_df[acc_df["id"] == account_id].iloc[0]
    username = acc_df["x username"]
    password = acc_df["x password"]

    await page_x.get_by_text("Sign in", exact=True).click()
    await random_pause()
    await page_x.locator('input[autocomplete="username"]').fill(username)
    await random_pause()
    await page_x.get_by_text("Next", exact=True).click()
    await random_pause()
    await page_x.locator('input[autocomplete="current-password"]').fill(password)
    await random_pause()
    await page_x.locator('button[data-testid="LoginForm_Login_Button"]').click()
    await random_pause()
    await page_x.close()
    print(f"✅ x_password_auth | Аккаунт {account_id}: Успешно вошли в X")

async def discord_password_auth(context, account_id):
    page_dis = await context.new_page()
    await page_dis.goto("https://discord.com/login")
    await page_dis.wait_for_load_state()
    await random_pause(3,5)
    if await page_dis.locator('input[name="email"]').count() < 1:
        print(f"🔁 Аккаунт {account_id}: Discord уже авторизован. Пропускаем.")
        return

    acc_df = pd.read_excel("parametrs.xlsx", sheet_name="Аккаунты")
    acc_df = acc_df[acc_df["id"] == account_id].iloc[0]
    username = acc_df["discord username"]
    password = acc_df["discord password"]

    await page_dis.locator('input[name="email"]').fill(username)
    await random_pause()
    await page_dis.locator('input[name="password"]').type(password, delay=100)
    await random_pause()
    await page_dis.locator('button[type="submit"]').click()
    await random_pause()
    await page_dis.close()
    print(f"✅ discord_password_auth | Аккаунт {account_id}: Успешно вошли в Discord")





