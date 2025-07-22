from patchright.async_api import async_playwright, BrowserContext
import asyncio
import time
import random
import string
#Later
from utilities import random_pause


async def galxe_universal(context: BrowserContext, account_id, link, claim_flag = 0, answers=None):
    if type(claim_flag) != 'int':
        claim_flag = int(claim_flag)
    if answers != None:
        answers = answers.split('.')
        for i in range(len(answers)):
            answers[i] = list(map(int, answers[i].split(',')))

    galxe_page = await context.new_page()
    await galxe_page.goto(link)
    await galxe_page.wait_for_load_state()
    await random_pause()
    if await galxe_page.get_by_role("button", name="Log in").count() > 0:
        await galxe_page.get_by_role("button", name="Log in").first.click()
        await random_pause()
        if await galxe_page.get_by_text("Rabby", exact=True).count() > 0:
            async with context.expect_page() as pup:
                await galxe_page.get_by_text("Rabby", exact=True).click()
            pup = await pup.value
            await random_pause()
            if await pup.get_by_text("Ignore all", exact=True).count() > 0:
                await pup.get_by_text("Ignore all", exact=True).click()
                await random_pause()
            async with context.expect_page() as pup2:
                await pup.get_by_text("Connect", exact=True).click()
            pup2 = await pup2.value
            await random_pause()
            if await pup2.get_by_text("Sign", exact=True).count() > 0:
                await pup2.get_by_text("Sign", exact=True).click()
                await random_pause()
            await pup2.get_by_text("Confirm", exact=True).click()
            await random_pause(2, 3)
        if await galxe_page.get_by_text("Recent", exact=True).count() > 0:
            async with context.expect_page() as pup:
                await galxe_page.get_by_text("Recent", exact=True).click()
            pup = await pup.value
            await random_pause()
            if await pup.get_by_text("Ignore all", exact=True).count() > 0:
                await pup.get_by_text("Ignore all", exact=True).click()
                await random_pause()
            await pup.get_by_text("Connect", exact=True).click()
            await random_pause(2, 3)

    if await galxe_page.get_by_text("Close", exact=True).count() > 0:
        await galxe_page.get_by_text("Close", exact=True).click()
    # await galxe_page.reload()
    # await galxe_page.wait_for_load_state()

    x_img = await galxe_page.locator(
        'img[src="https://b.galxestatic.com/new-web-prd/assets/image/credential-types/icon-twitter.svg"]').all()
    for img in x_img:
        if await img.locator('../..').locator('button[type="button"]').count() > 0:
            continue
        async with context.expect_page() as pup:
            await img.click()
        pup = await pup.value
        await random_pause()
        if await pup.locator('button[data-testid="tweetButton"]').count() > 0:
            await pup.locator('button[data-testid="tweetButton"]').click()
        if await pup.locator('button[data-testid="confirmationSheetConfirm"]').count() > 0:
            await pup.locator('button[data-testid="confirmationSheetConfirm"]').click()
        await random_pause()
        await pup.close()
        await random_pause()
        await img.locator('../..').locator('button[data-state="closed"]').click()
        await random_pause()

    if await galxe_page.locator(
            'img[src="https://b.galxestatic.com/new-web-prd/assets/image/credential-types/icon-space-user.svg"]').count() > 0:
        planet_img = galxe_page.locator(
            'img[src="https://b.galxestatic.com/new-web-prd/assets/image/credential-types/icon-space-user.svg"]')
        if await planet_img.locator('../..').locator('button[type="button"]').count() < 1:
            await planet_img.click()
            await random_pause()
            await galxe_page.get_by_role('button', name='Follow', exact=True).click()
            await random_pause()

    page_img = await galxe_page.locator(
        'img[src="https://b.galxestatic.com/new-web-prd/assets/image/credential-types/icon-visit-page2.svg"]').all()
    for img in page_img:
        if await img.locator('../..').locator('button[type="button"]').count() > 0:
            continue
        async with context.expect_page() as pup:
            await img.click()
            await random_pause()
            if await galxe_page.get_by_text("Continue to Access", exact=True).count() > 0:
                await galxe_page.get_by_text("Continue to Access", exact=True).click()
        pup = await pup.value
        await random_pause()
        await pup.close()
        await random_pause()
        await img.locator('../..').locator('button[data-state="closed"]').click()
        await random_pause()

    survey_img = await galxe_page.locator(
        'img[src="https://b.galxestatic.com/new-web-prd/assets/image/credential-types/icon-survey.svg"]').all()
    for img in survey_img:
        if await img.locator("xpath=../..").get_by_text("Start", exact=True).count() < 1:
            continue
        await img.locator("xpath=../..").get_by_text("Start", exact=True).click()
        while await galxe_page.get_by_role('button', name="Submit").count() < 1:
            if await  galxe_page.get_by_role('button', name="Next").count() > 0:
                await galxe_page.get_by_role('button', name="Next").click()
                await random_pause()
            if await galxe_page.locator('button[role="radio"]').count() > 0:
                variant_count = await galxe_page.locator('button[role="radio"]').count()
                await galxe_page.locator('button[role="radio"]').nth(random.randint(0, variant_count)).click()
                await random_pause()

            if await galxe_page.locator('input[placeholder="Enter answer"]').count() > 0:
                await galxe_page.locator('input[placeholder="Enter answer"]').fill(
                    ''.join(random.choices(string.ascii_letters,
                                           k=random.randint(5,
                                                            15))))
                await random_pause()
        else:
            await galxe_page.get_by_role('button', name="Submit").click()
            await random_pause()

    youtube_img = await galxe_page.locator(
        'img[src="https://b.galxestatic.com/new-web-prd/assets/image/credential-types/icon-youtube-watch2.svg"]').all()
    for img in youtube_img:
        if await img.locator('../..').locator('button[type="button"]').count() > 0:
            continue
        await img.click()
        await random_pause(2, 3)
        await galxe_page.keyboard.press("Escape")
        await random_pause()
        await img.locator('../..').locator('button[data-state="closed"]').click()
        await random_pause()

    teleg_img = await galxe_page.locator(
        'img[src="https://b.galxestatic.com/new-web-prd/assets/image/credential-types/icon-telegram-group2.svg"]').all()
    for img in teleg_img:
        if await img.locator('../..').locator('button[type="button"]').count() > 0:
            continue
        async with context.expect_page() as pup:
            await img.click()
        pup = await pup.value
        await random_pause()
        link = await pup.locator('span[class="tgme_action_button_label"]').locator('..').get_attribute('href')
        await random_pause()
        await pup.goto(link)
        await pup.wait_for_load_state()
        await random_pause()
        await pup.locator('button[class="Button tiny primary fluid has-ripple"]').click()
        await random_pause()
        await pup.close()
        await random_pause()
        await img.locator('../..').locator('button[data-state="closed"]').click()
        await random_pause()

    quiz_img = await \
        galxe_page.locator(
            'img[src="https://b.galxestatic.com/new-web-prd/assets/image/credential-types/icon-quiz.svg"]').all()
    for i in range(len(quiz_img)):

        if await quiz_img[i].locator('../..').locator('button[type="button"]').count() < 1:
            answer = answers[i]
            await quiz_img[i].locator("xpath=../..").get_by_text("Start", exact=True).click()
            await random_pause()
            await galxe_page.get_by_text("Start Now", exact=True).click()
            await random_pause()
            for ans in answer:
                await galxe_page.locator('button[role="radio"]').nth(ans - 1).click()
                await random_pause()
                if await galxe_page.get_by_role('button', name="Submit").count() > 0:
                    await galxe_page.get_by_role('button', name="Submit", exact=True).click()
                elif await galxe_page.get_by_role('button', name="Next").count() > 0:
                    await galxe_page.get_by_role('button', name="Next").last.click()


    dis_img = await galxe_page.locator(
        'img[src="https://b.galxestatic.com/new-web-prd/assets/image/credential-types/icon-discord.svg"]').all()
    for img in dis_img:
        if await img.locator('../..').locator('button[type="button"]').count() < 1:
            await random_pause()
            async with context.expect_page() as pup:
                await img.click()
            pup = await pup.value
            await random_pause()
            await pup.locator('button[type="button"]').click()
            await random_pause()

        await img.locator('../..').locator('button[data-state="closed"]').click()
        await random_pause()

    if claim_flag:
        await galxe_page.locator('div[class="flex gap-4 w-full justify-end items-center"]').locator('button').click()
        await random_pause()
        if await galxe_page.get_by_role('button', name='Claim Directly', exact=True).count() > 0:
            async with context.expect_page() as pup:
                await galxe_page.get_by_role('button', name='Claim Directly', exact=True).click()
            pup = await pup.value
            await random_pause()
            await pup.get_by_text("Sign", exact=True).click()
            await random_pause()
            await pup.get_by_text("Confirm", exact=True).click()
            await random_pause()
        if await galxe_page.get_by_role('button', name='Approve', exact=True).count() > 0:
            await galxe_page.get_by_role('button', name='Approve', exact=True).click()
            await random_pause()
    print(f"✅ Аккаунт {account_id}: galxe_universal.galxe_universal({link}) выполнен успешно")
    await galxe_page.close()




