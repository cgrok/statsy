import discord
import random
import copy
from statsbot import InvalidTag
from bs4 import BeautifulSoup

def random_color():
    return random.randint(0, 0xFFFFFF)

def emoji(ctx, name):
    name = name.lower().replace('ricochet', 'rico').replace('el primo', 'primo').replace('jessie', 'jess').replace('dynamike', 'mike')
    e = discord.utils.get(ctx.bot.game_emojis, name=name)
    if e is None:
        return name
    return e

url = 'https://brawlstats.io'

async def format_profile(ctx, soup, tag):
    try:
        profile = soup.find('main') \
                .find('section', attrs={'class':'ui-card pt-4'}) \
                .find('div', attrs={'class':'container'}) \
                .find('div', attrs={'class':'stat-section'})
    except AttributeError:
        raise InvalidTag('Invalid bs-tag passed.')
    name = profile.find('div', attrs={'class':'row'}) \
        .find('div', attrs={'class':'col-12'}) \
        .find('div', attrs={'class':'player-profile text-center'}) \
        .find('div', attrs={'class':'player-info'}) \
        .find('div', {'class':'player-name brawlstars-font'}).getText()

    brawlersraw = profile.find_all('div', attrs={'class':'col-12 mt-1'})[1].find_all('div')
    brawlers = ''
    for brawler in brawlersraw:
        try:
            brawlers += str(emoji(ctx, \
            brawler.find('a').find('div').find('div') \
            .find('div', attrs={'class':'name'}).getText()))
        except AttributeError:
            pass

    pic = url + profile.find('div', attrs={'class':'row'}) \
        .find('div', attrs={'class':'col-12'}) \
        .find('div', attrs={'class':'player-profile text-center'}) \
        .find('div', attrs={'class':'player-info'}) \
        .find('div', {'class':'profile-avatar'}) \
        .find('img')['src']
    
    async with ctx.session.get(pic) as resp:
        with open('data/pic.png', 'wb') as f:
            f.write(await resp.read())

    pic = discord.File('data/pic.png', filename='pic.png')

    trophies = profile.find('div', attrs={'class':'col-6 col-md-4 col-lg-3 mb-2'}).getText().strip('Trophies')
    pb = profile.find_all('div', attrs={'class':'col-6 col-md-4 col-lg-3 mb-2'})[1].getText().strip('Highest trophies')
    victories = profile.find_all('div', attrs={'class':'col-6 col-md-4 col-lg-3 mb-2'})[2].getText().strip('Victories')
    showdown = profile.find_all('div', attrs={'class':'col-6 col-md-4 col-lg-3 mb-2'})[3].getText().strip('Showdown victories')
    expvals = profile.find('div', attrs={'class':'row'}) \
            .find('div', attrs={'class':'col-12'}) \
            .find('div', attrs={'class':'player-profile text-center'}) \
            .find('div', attrs={'class':'experience-bar mt-3'})
    exp = expvals.find('div', attrs={'class':'experience-level'}).getText() + ' (' + \
         expvals.find('div', attrs={'class':'progress-text'}).getText() + ')'
    bandtag = profile.find_all('div', attrs={'class':'col-12 mt-1'})[2] \
                .find('div', attrs={'class':'band-history-entry'}) \
                .find('a')['href'].strip('/bands/')
    bandname = profile.find_all('div', attrs={'class':'col-12 mt-1'})[2] \
                .find('div', attrs={'class':'band-history-entry'}) \
                .find('a') \
                .find('div', attrs={'class':'card jumpc mb-2'}) \
                .find('div', attrs={'class':'band-info'}) \
                .find('div', attrs={'class':'band-name mr-2'}).getText()

    em = discord.Embed(color=random_color())
    if ctx.bot.psa_message:
        em.description = f'*{ctx.bot.psa_message}*'
    em.set_author(name=f'{name} (#{tag})')
    em.set_thumbnail(url='attachment://pic.png')

    embed_fields = [
        ('Trophies', f'{trophies}/{pb} PB {emoji(ctx, "icon_trophy")}', True),
        ('Victories', f'{victories} {emoji(ctx, "star_gold_00")}', True),
        ('Showdown Wins', f'{showdown} {emoji(ctx, "icon_showdown")}', True),
        ('Level', f'{exp} {emoji(ctx, "star_silver")}', True),
        ('Band Name', bandname, True),
        ('Band Tag', '#' + bandtag, True),
        ('Brawlers', brawlers, False),
    ]

    for n, v, i in embed_fields:
        if v:
            em.add_field(name=n, value=v, inline=i)

    return (pic, em)

async def format_band(ctx, soup, tag):
    try:
        band = soup.find('main') \
                .find('section', attrs={'class':'ui-card pt-4'}) \
                .find('div', attrs={'class':'container'}) \
                .find('div', attrs={'class':'stat-section'})
    except AttributeError:
        raise InvalidTag('Invalid bs-tag passed.')
    bandinfo = band.find('div', attrs={'class':'row'}) \
            .find('div', attrs={'class':'col-12'}) \
            .find('div', attrs={'class':'band-profile text-center'}) \
            .find('div', attrs={'class':'col-12'}) \
            .find('div', attrs={'class':'band-profile'})

    name = bandinfo.find('div', attrs={'class':'name'}).getText()
    description = bandinfo.find('div', attrs={'class':'clan-description'}).getText()
    badge = url + bandinfo.find('div', attrs={'class':'badge'}) \
            .find('img', attrs={'class':'band-badge'})['src']

    async with ctx.session.get(badge) as resp:
        with open('data/pic.png', 'wb') as f:
            f.write(await resp.read())

    badge = discord.File('data/pic.png', filename='pic.png')

    score = band.find('div', attrs={'class':'row'}) \
            .find('div', attrs={'class':'col-6'}) \
            .find('div', attrs={'class':'band-profile-card text-center'}).getText().strip('Trophies')
    
    required = band.find('div', attrs={'class':'row'}) \
            .find_all('div', attrs={'class':'col-6'})[1] \
            .find('div', attrs={'class':'band-profile-card text-center'}).getText().strip('Required Trophies')

    members = band.find('div', attrs={'class':'container'}) \
            .find_all('div', attrs={'class':'row'})[2] \
            .find('div', attrs={'class':'col-12'}) \
            .find('div', attrs={'class':'members-list'}) \
            .find('table', attrs={'class':'table brawlstars-table'}) \
            .find('tbody') \
            .find_all('tr')
  
    _experiences = sorted(members, key=lambda x: int(x.find('td', attrs={'class':'experience'}) \
                    .find('span', attrs={'class':'experience-star'}).getText()))
    experiences = []
    pushers = []

    if len(members) >= 3:
        for i in range(3):
            pushername = members[i].find('td', attrs={'class':'player-details'}) \
                    .find('div', attrs={'class':'player'}) \
                    .find('div', attrs={'class':'name'}).getText()
            trophies = members[i].find('td', attrs={'class':'player-details'}) \
                    .find('div', attrs={'class':'trophy-count'}).getText()
            pushers.append(
                f"**{pushername}**"
                f"\n{trophies} " 
                f"{emoji(ctx, 'icon_trophy')}\n" 
                f"#{members[i]['data-href'].strip('/players/')}"
                )

            xpname = _experiences[i].find('td', attrs={'class':'player-details'}) \
                    .find('div', attrs={'class':'player'}) \
                    .find('div', attrs={'class':'name'}).getText()
            xp = _experiences[i].find('td', attrs={'class':'experience'}) \
                    .find('span', attrs={'class':'experience-star'}).getText()
            experiences.append(
                f"**{xpname}**"
                f"\n{emoji(ctx, 'star_silver')}"
                f" {xp}\n" 
                f"#{_experiences[i]['data-href'].strip('/players/')}"
                )

    page1 = discord.Embed(description=description, color=random_color())
    page1.set_author(name=f"{name} (#{tag})")
    if ctx.bot.psa_message:
        page1.description = ctx.bot.psa_message
    page1.set_thumbnail(url='attachment://pic.png')
    page2 = copy.deepcopy(page1)
    page2.description = 'Top Players/Experienced Players for this clan.'

    fields1 = [
        ('Clan Score', f'{score} {emoji(ctx, "icon_trophy")}'),
        ('Required Trophies', f'{required} {emoji(ctx, "icon_trophy")}'),
        ('Members', f'{len(members)}/100')
    ]
    fields2 = [
        ("Top Players", '\n\n'.join(pushers)),
        ("Top Experience", '\n\n'.join(experiences))
    ]

    for f, v in fields1:
        page1.add_field(name=f, value=v)

    for f, v in fields2:
        if v:
            page2.add_field(name=f, value=v)

    return [page1, page2, badge]