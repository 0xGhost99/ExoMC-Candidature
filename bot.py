import discord
from discord.ext import commands
from discord.ui import View, Modal, TextInput, Select, Button
from datetime import datetime
import re

# ═══════════════════════════════════════════════════
#              CONFIGURAZIONE CORE
# ═══════════════════════════════════════════════════
TOKEN = "MTUwMjUzNDIzNTI3MTk5MTM5Nw.GEdH4w.qPTvFRAMPLMsonFhNoZLmcIiyF5c4-awy8lLVQ"
STAFF_LOGS_CHANNEL_ID = 1502584100060401845
GUILD_ID              = 1404822847343431732
STAFF_ROLE_ID         = 1490640384676859954
MENTIONS_LOGS         = "|| <@&1404829877659631750> / <@&1404830123223679089> ||"

intents = discord.Intents.all()
bot = commands.Bot(command_prefix='!', intents=intents)

# ═══════════════════════════════════════════════════
#           DATABASE DOMANDE CANDIDATURA
# ═══════════════════════════════════════════════════
# FASE 1: Informazioni Generali (Max 5 campi per limitazioni Discord)
RUOLI_INFO = {
    'helper_supporter':  ['Nick in game', 'Nick Discord (@)', 'Età', 'Hai esperienze in questo ambito?', 'Se sì, dove?'],
    'builder':           ['Nick in Game', 'Nick Discord (@)', 'Età', 'Esperienze passate', 'Dove hai avuto esperienze passate?'],
    'developer':         ['Nick in Game', 'Nick Discord (@)', 'Età', 'Esperienze passate come Developer', 'Dove hai avuto esperienze passate?'],
    'helper_screenshare':['Nick in Game', 'Nick DS (@)', 'Età', 'Esperienze passate', 'Parlaci di te'],
    'media':             ['Nick in Game', 'Nick Discord (@)', 'Età', 'Piattaforma principale (YT/Twitch/TikTok)', 'Link al tuo canale/profilo']
}

RUOLI_LABEL = {
    'helper_supporter':  '🛡️ Helper / Supporter',
    'builder':           '🏗️ Builder',
    'developer':         '💻 Developer',
    'helper_screenshare':'🔍 Helper Screenshare',
    'media':             '🎥 Media / Content Creator'
}

# ════════════════════════════════════════════════════════
#   HELPER: trova un utente per menzione, ID o username
# ════════════════════════════════════════════════════════
async def find_user(ctx, raw: str):
    clean_id = re.sub(r'[^0-9]', '', raw)
    if clean_id:
        try:
            return await bot.fetch_user(int(clean_id))
        except Exception:
            pass
    name = raw.replace('@', '').lower()
    for m in ctx.guild.members:
        if m.name.lower() == name or (m.global_name and m.global_name.lower() == name):
            return m
    return None

def is_staff(member: discord.Member) -> bool:
    return any(r.id == STAFF_ROLE_ID for r in member.roles)

# ════════════════════════════════════════════════════════
#   1. PANNELLO SELF-SERVICE — chiunque può candidarsi
# ════════════════════════════════════════════════════════
class SelfApplySelect(Select):
    def __init__(self):
        options = [
            discord.SelectOption(label='Helper / Supporter',  value='helper_supporter',  emoji='🛡️', description='Supporto ai giocatori'),
            discord.SelectOption(label='Builder',             value='builder',            emoji='🏗️', description='Costruzioni e mappe'),
            discord.SelectOption(label='Developer',           value='developer',          emoji='💻', description='Plugin e sviluppo'),
            discord.SelectOption(label='Helper Screenshare',  value='helper_screenshare', emoji='🔍', description='Anti-cheat / SS'),
            discord.SelectOption(label='Media',               value='media',              emoji='🎥', description='Youtuber / Streamer / TikToker'),
        ]
        super().__init__(placeholder='🎯 Seleziona il ruolo per cui vuoi candidarti…', options=options)

    async def callback(self, interaction: discord.Interaction):
        ruolo = self.values[0]
        await interaction.response.send_modal(ApplicationModal(interaction.user, ruolo))

class SelfApplyView(View):
    def __init__(self):
        super().__init__(timeout=None)
        self.add_item(SelfApplySelect())

# ════════════════════════════════════════════════════════
#   2. SELEZIONE ORARIO COLLOQUIO
# ════════════════════════════════════════════════════════
class ColloquioSelect(Select):
    def __init__(self):
        options = [
            discord.SelectOption(label='Mattina   09:00 – 12:00', value='mattina',    emoji='🌅'),
            discord.SelectOption(label='Pomeriggio 15:00 – 18:00', value='pomeriggio', emoji='☀️'),
            discord.SelectOption(label='Sera      20:00 – 23:00', value='sera',       emoji='🌙'),
        ]
        super().__init__(placeholder='📅 Seleziona la tua fascia oraria…', options=options)

    async def callback(self, interaction: discord.Interaction):
        fasce = {'mattina': '09:00 – 12:00', 'pomeriggio': '15:00 – 18:00', 'sera': '20:00 – 23:00'}
        orario_scelto = fasce[self.values[0]]
        
        logs_channel = bot.get_channel(STAFF_LOGS_CHANNEL_ID)
        if logs_channel:
            log_embed = discord.Embed(
                title='📅 Disponibilità Colloquio Ricevuta',
                color=0x3498DB,
                timestamp=datetime.now()
            )
            log_embed.add_field(name='👤 Candidato', value=interaction.user.mention, inline=True)
            log_embed.add_field(name='⏰ Fascia Oraria', value=f'**{orario_scelto}**', inline=True)
            log_embed.set_footer(text='ExoMC Recruitment System • Made by 0xGhost99')
            await logs_channel.send(content=MENTIONS_LOGS, embed=log_embed)

        user_embed = discord.Embed(
            title='📌 Disponibilità Registrata',
            description=(
                f'**Fascia selezionata:** {orario_scelto}\n\n'
                'Lo staff valuterà la tua disponibilità e ti contatterà a breve per confermare l\'orario esatto.'
            ),
            color=0x2ECC71,
            timestamp=datetime.now()
        )
        user_embed.set_footer(text='ExoMC Deluxe Operational System • Made by 0xGhost99')
        await interaction.response.send_message(embed=user_embed, ephemeral=True)

class ColloquioView(View):
    def __init__(self):
        super().__init__(timeout=None)
        self.add_item(ColloquioSelect())

# ════════════════════════════════════════════════════════
#   3. PULSANTE "APRI QUESTIONARIO TECNICO"
# ════════════════════════════════════════════════════════
class TechButton(Button):
    def __init__(self, ruolo: str, user_id: int):
        super().__init__(label='📋 Procedi alle Domande Tecniche', style=discord.ButtonStyle.blurple,
                         custom_id=f'tech|{ruolo}|{user_id}')

class TechButtonView(View):
    def __init__(self, ruolo: str, user_id: int):
        super().__init__(timeout=None)
        self.add_item(TechButton(ruolo, user_id))

class TechTwoButton(Button):
    def __init__(self, ruolo: str, user_id: int):
        super().__init__(label='📑 Ultima parte del Questionario', style=discord.ButtonStyle.danger,
                         custom_id=f'tech2|{ruolo}|{user_id}')

class TechTwoButtonView(View):
    def __init__(self, ruolo: str, user_id: int):
        super().__init__(timeout=None)
        self.add_item(TechTwoButton(ruolo, user_id))

# ════════════════════════════════════════════════════════
#   4. GESTIONE CANDIDATURE — Accetta / Rifiuta / Convoca
# ════════════════════════════════════════════════════════
class ReviewView(View):
    def __init__(self, user: discord.User, ticket_channel_id: int):
        super().__init__(timeout=None)
        self.user = user
        self.ticket_channel_id = ticket_channel_id

    async def _get_channel(self, guild: discord.Guild):
        return guild.get_channel(self.ticket_channel_id)

    @discord.ui.button(label='✅ Accetta', style=discord.ButtonStyle.green)
    async def accept(self, interaction: discord.Interaction, button: Button):
        ch = await self._get_channel(interaction.guild)
        embed = discord.Embed(
            title='🌟 Candidatura Approvata',
            description=(
                f'{self.user.mention},\n\n'
                'Dopo un\'attenta revisione, siamo lieti di comunicarti che la tua candidatura\n'
                'è stata **approvata con esito positivo**. Benvenuto nel team! 🎉'
            ),
            color=0x2ECC71,
            timestamp=datetime.now()
        )
        embed.set_footer(text='Benvenuto nello Staff ExoMC ✨ • Made by 0xGhost99')
        if ch:
            await ch.send(embed=embed)
        await interaction.response.send_message('✅ Candidato accettato.', ephemeral=True)

    @discord.ui.button(label='❌ Rifiuta', style=discord.ButtonStyle.red)
    async def reject(self, interaction: discord.Interaction, button: Button):
        ch = await self._get_channel(interaction.guild)
        embed = discord.Embed(
            title='📌 Esito Revisione Candidatura',
            description=(
                f'{self.user.mention},\n\n'
                'A seguito di una revisione approfondita, il team ha deciso di\n'
                '**non procedere con l\'approvazione** per questa candidatura.\n\n'
                'Non arrenderti: continua a migliorarti e riprova in futuro. 💡'
            ),
            color=0xE74C3C,
            timestamp=datetime.now()
        )
        embed.set_footer(text='Non smettere di migliorarti • Made by 0xGhost99')
        if ch:
            await ch.send(embed=embed)
        await interaction.response.send_message('❌ Candidato rifiutato.', ephemeral=True)

    @discord.ui.button(label='🎤 Richiedi Colloquio', style=discord.ButtonStyle.blurple)
    async def interview(self, interaction: discord.Interaction, button: Button):
        ch = await self._get_channel(interaction.guild)
        embed = discord.Embed(
            title='🎙️ Convocazione al Colloquio',
            description=(
                f'{self.user.mention},\n\n'
                'Il team di selezione desidera approfondire la tua candidatura\n'
                'tramite un **colloquio diretto**.\n\n'
                'Seleziona qui sotto la fascia oraria che preferisci:'
            ),
            color=0x5865F2,
            timestamp=datetime.now()
        )
        embed.set_footer(text='Seleziona con attenzione 📅 • Made by 0xGhost99')
        if ch:
            await ch.send(embed=embed, view=ColloquioView())
        await interaction.response.send_message('🎤 Colloquio avviato nel ticket.', ephemeral=True)

# ════════════════════════════════════════════════════════
#   5. MODALI DOMANDE AGGIORNATE
# ════════════════════════════════════════════════════════
class TecnicoModal(Modal):
    def __init__(self, ruolo: str, user: discord.User):
        super().__init__(title=f'Test Tecnico Parte 1 — {ruolo.upper()}'[:45])
        self.ruolo = ruolo
        self.user  = user

        if ruolo == 'helper_supporter':
            self.add_item(TextInput(label='Cosa vuol dire DDoS?', style=discord.TextStyle.paragraph))
            self.add_item(TextInput(label='Cosa vuol dire Doxare?', style=discord.TextStyle.paragraph))
            self.add_item(TextInput(label='Differenza Spam - Flood - Flame', style=discord.TextStyle.paragraph))
            self.add_item(TextInput(label='3 pregi tuoi:', style=discord.TextStyle.short))
            self.add_item(TextInput(label='3 difetti tuoi:', style=discord.TextStyle.short))

        elif ruolo == 'builder':
            self.add_item(TextInput(label='3 comandi WorldEdit e funzioni', style=discord.TextStyle.paragraph))
            self.add_item(TextInput(label='Plugin building che sai usare meglio', style=discord.TextStyle.short))
            self.add_item(TextInput(label='Manda 3 foto delle tue migliori Build', style=discord.TextStyle.paragraph))

        elif ruolo == 'developer':
            self.add_item(TextInput(label='Linguaggi di programmazione conosciuti', style=discord.TextStyle.short))
            self.add_item(TextInput(label='Qual è il linguaggio in cui sei più bravo?', style=discord.TextStyle.short))
            self.add_item(TextInput(label='Quali plugin hai sviluppato? (Link/Desc)', style=discord.TextStyle.paragraph))
            self.add_item(TextInput(label='Come funziona database su Minecraft?', style=discord.TextStyle.paragraph))
            self.add_item(TextInput(label='Framework comuni conosciuti? (Spigot...)', style=discord.TextStyle.short))

        elif ruolo == 'helper_screenshare':
            self.add_item(TextInput(label='Differenza ghost, injection, external', style=discord.TextStyle.paragraph))
            self.add_item(TextInput(label='Spiega come trovare un autoclicker.jar', style=discord.TextStyle.paragraph))
            self.add_item(TextInput(label='Come vedere se è stato eliminato il cestino', style=discord.TextStyle.paragraph))
            self.add_item(TextInput(label='Spiega alcuni metodi di bypass', style=discord.TextStyle.paragraph))
            self.add_item(TextInput(label='Spiega cosa sono le macro', style=discord.TextStyle.paragraph))
            
        elif ruolo == 'media':
            self.add_item(TextInput(label='Quanti iscritti/follower hai attualmente?', style=discord.TextStyle.short))
            self.add_item(TextInput(label='Quante visualizzazioni fai mediamente?', style=discord.TextStyle.short))
            self.add_item(TextInput(label='Cosa porterai sul nostro server?', style=discord.TextStyle.paragraph))
            self.add_item(TextInput(label='Hai già fatto video in passato qui?', style=discord.TextStyle.short))

    async def on_submit(self, interaction: discord.Interaction):
        logs = bot.get_channel(STAFF_LOGS_CHANNEL_ID)
        embed = discord.Embed(title=f'🎙️ Domande Tecniche [P1] — {self.ruolo.upper()}', color=0xE67E22, timestamp=datetime.now())
        embed.add_field(name='👤 Candidato', value=self.user.mention, inline=True)
        
        for item in self.children:
            campo_nome = getattr(item, 'title', None) or 'Domanda'
            embed.add_field(name=f'🔹 {campo_nome}', value=item.value or '—', inline=False)
            
        if logs:
            await logs.send(embed=embed)

        if self.ruolo in ['helper_supporter', 'developer', 'helper_screenshare']:
            await interaction.response.send_message(
                embed=discord.Embed(title="📝 Quasi finito!", description="Clicca sotto per completare l'ultima parte di domande rimaste.", color=0xF39C12),
                view=TechTwoButtonView(self.ruolo, self.user.id), ephemeral=True
            )
        else:
            # Per i ruoli corti come Builder e Media finisce direttamente qui
            if logs:
                await logs.send(content=MENTIONS_LOGS, embed=discord.Embed(title="📊 Candidatura Completa Ricevuta", description=f"Il candidato {self.user.mention} ha terminato l'invio.", color=0x2ECC71), view=ReviewView(self.user, interaction.channel.id))
            await interaction.response.send_message(embed=discord.Embed(title='✅ Candidatura Inviata', description='Tutte le tue risposte sono state inoltrate allo staff.', color=0x2ECC71))

# PARTE 2 DEI MODALI LUNGHI
class TecnicoDueModal(Modal):
    def __init__(self, ruolo: str, user: discord.User):
        super().__init__(title=f'Test Tecnico Parte 2 — {ruolo.upper()}'[:45])
        self.ruolo = ruolo
        self.user  = user

        if ruolo == 'helper_supporter':
            self.add_item(TextInput(label='Tempo attivo al giorno & feriali/feste', style=discord.TextStyle.paragraph))
            
        elif ruolo == 'developer':
            self.add_item(TextInput(label='Come gestisci gli errori/bug nel codice?', style=discord.TextStyle.paragraph))
            self.add_item(TextInput(label='Manda 2-3 esempi del tuo codice migliore', style=discord.TextStyle.paragraph))
            self.add_item(TextInput(label='Tempo attivo al giorno', style=discord.TextStyle.short))
            
        elif ruolo == 'helper_screenshare':
            self.add_item(TextInput(label='Cos\'è e come si usa Journal USN', style=discord.TextStyle.paragraph))

    async def on_submit(self, interaction: discord.Interaction):
        logs = bot.get_channel(STAFF_LOGS_CHANNEL_ID)
        embed = discord.Embed(title=f'🎙️ Domande Tecniche [P2 Final] — {self.ruolo.upper()}', color=0x2ECC71, timestamp=datetime.now())
        embed.add_field(name='👤 Candidato', value=self.user.mention, inline=True)
        
        for item in self.children:
            campo_nome = getattr(item, 'title', None) or 'Domanda'
            embed.add_field(name=f'🔹 {campo_nome}', value=item.value or '—', inline=False)
            
        if logs:
            await logs.send(embed=embed)
            await logs.send(content=MENTIONS_LOGS, embed=discord.Embed(title="📊 Candidatura Completa", description=f"Candidatura conclusa con successo per {self.user.mention}.", color=0x2ECC71), view=ReviewView(self.user, interaction.channel.id))

        await interaction.response.send_message(embed=discord.Embed(title='✅ Questionario Concluso', description='I tuoi dati sono ora completi. Attendi una risposta dallo Staff!', color=0x2ECC71))


class ApplicationModal(Modal):
    def __init__(self, user: discord.User, ruolo: str):
        super().__init__(title=f'Fase 1 Anagrafica — {ruolo.upper()}'[:45])
        self.user  = user
        self.ruolo = ruolo
        for q in RUOLI_INFO[ruolo]:
            self.add_item(TextInput(label=q[:45], style=discord.TextStyle.short))

    async def on_submit(self, interaction: discord.Interaction):
        logs = bot.get_channel(STAFF_LOGS_CHANNEL_ID)
        embed = discord.Embed(
            title='📨 Nuova Candidatura — Fase 1 (Anagrafica)',
            color=0x5865F2,
            timestamp=datetime.now()
        )
        embed.add_field(name='👤 Candidato', value=self.user.mention, inline=True)
        embed.add_field(name='💼 Ruolo',     value=RUOLI_LABEL.get(self.ruolo, self.ruolo), inline=True)
        embed.add_field(name='\u200b',       value='\u200b', inline=False)
        for i, item in enumerate(self.children):
            embed.add_field(name=RUOLI_INFO[self.ruolo][i], value=item.value or '—', inline=False)
        embed.set_footer(text='ExoMC System Log • Made by 0xGhost99')

        if logs:
            await logs.send(embed=embed)

        next_embed = discord.Embed(
            title='📝 Fase 1 Completata!',
            description='**Dati anagrafici ricevuti.**\n\nOra devi sbloccare e compilare il **Questionario Tecnico**.\nClicca il pulsante qui sotto.',
            color=0xF39C12
        )
        await interaction.response.send_message(embed=next_embed, view=TechButtonView(self.ruolo, self.user.id), ephemeral=True)

# ════════════════════════════════════════════════════════
#   6. VIEW PER STAFF — avvia candidatura manuale
# ════════════════════════════════════════════════════════
class ApplyView(View):
    def __init__(self, user: discord.User, ruolo: str):
        super().__init__(timeout=None)
        self.user  = user
        self.ruolo = ruolo

    @discord.ui.button(label='📝 Avvia Candidatura', style=discord.ButtonStyle.green)
    async def apply(self, interaction: discord.Interaction, button: Button):
        if interaction.user.id != self.user.id:
            return await interaction.response.send_message('❌ Questo pulsante non è per te.', ephemeral=True)
        await interaction.response.send_modal(ApplicationModal(interaction.user, self.ruolo))

# ════════════════════════════════════════════════════════
#   7. PANNELLO RISPOSTE RAPIDE
# ════════════════════════════════════════════════════════
class ReplyPanel(View):
    def __init__(self):
        super().__init__(timeout=None)

    @discord.ui.button(label='Benvenuto', style=discord.ButtonStyle.primary, emoji='👋')
    async def welcome(self, interaction: discord.Interaction, button: Button):
        embed = discord.Embed(title='👋 Staff ExoMC', description='Saluti! Un membro del nostro Staff ha preso in carico il ticket.\nCome possiamo aiutarti?', color=0x3498DB)
        await interaction.response.send_message(embed=embed)

    @discord.ui.button(label='Richiedi Prove', style=discord.ButtonStyle.secondary, emoji='📸')
    async def evidence(self, interaction: discord.Interaction, button: Button):
        embed = discord.Embed(title='📸 Prove Necessarie', description='Ti invitiamo a fornire **prove multimediali valide** (screenshot o video)\nper procedere con la tua segnalazione.', color=0xE67E22)
        await interaction.response.send_message(embed=embed)

    @discord.ui.button(label='In Revisione', style=discord.ButtonStyle.grey, emoji='🔎')
    async def review(self, interaction: discord.Interaction, button: Button):
        embed = discord.Embed(title='🔎 Ticket in Revisione', description='Il tuo ticket è attualmente **sotto esame** da parte del team.\nTi risponderemo al più presto.', color=0x95A5A6)
        await interaction.response.send_message(embed=embed)

    @discord.ui.button(label='Chiudi Ticket', style=discord.ButtonStyle.danger, emoji='🔒')
    async def close(self, interaction: discord.Interaction, button: Button):
        embed = discord.Embed(title='🔒 Ticket Chiuso', description='Questo ticket è stato **chiuso** dallo staff.\nSe hai ancora bisogno di aiuto, apri un nuovo ticket.', color=0xE74C3C)
        await interaction.response.send_message(embed=embed)

# ════════════════════════════════════════════════════════
#   INTERCETTAZIONE PULSANTI DINAMICI
# ════════════════════════════════════════════════════════
@bot.event
async def on_interaction(interaction: discord.Interaction):
    if not (interaction.data and 'custom_id' in interaction.data):
        return

    custom_id = interaction.data['custom_id']

    if custom_id.startswith('tech|'):
        parts = custom_id.split('|')
        if len(parts) == 3:
            _, ruolo, user_id_str = parts
            if interaction.user.id != int(user_id_str):
                return await interaction.response.send_message('❌ Questo questionario non è il tuo.', ephemeral=True)
            await interaction.response.send_modal(TecnicoModal(ruolo, interaction.user))

    elif custom_id.startswith('tech2|'):
        parts = custom_id.split('|')
        if len(parts) == 3:
            _, ruolo, user_id_str = parts
            if interaction.user.id != int(user_id_str):
                return await interaction.response.send_message('❌ Questo questionario non è il tuo.', ephemeral=True)
            await interaction.response.send_modal(TecnicoDueModal(ruolo, interaction.user))

# ════════════════════════════════════════════════════════
#   COMANDI
# ════════════════════════════════════════════════════════
@bot.command()
async def candidatura(ctx, utente_raw: str, ruolo: str):
    if not is_staff(ctx.author):
        return await ctx.send('❌ Solo lo staff può usare questo comando.')

    utente = await find_user(ctx, utente_raw)
    if not utente:
        return await ctx.send(f'❌ Utente `{utente_raw}` non trovato.')

    if ruolo not in RUOLI_INFO:
        return await ctx.send(f'❌ Ruolo non valido. Scegli tra: `{"`, `".join(RUOLI_INFO.keys())}`')

    embed = discord.Embed(
        title='🌟 Invito Candidatura Staff — ExoMC',
        description=f'{utente.mention},\n\nSei stato invitato dallo staff ad avviare la tua candidatura per\n**{RUOLI_LABEL[ruolo]}**.\n\nPremi il pulsante qui sotto per iniziare.',
        color=0x5865F2,
        timestamp=datetime.now()
    )
    embed.set_footer(text='ExoMC Recruitment System • Made by 0xGhost99')
    await ctx.send(embed=embed, view=ApplyView(utente, ruolo))

@bot.command()
async def apply(ctx):
    embed = discord.Embed(
        title='🎯 Candidati allo Staff — ExoMC',
        description='Vuoi far parte del nostro team?\n\nSeleziona il ruolo dal menu qui sotto e compila il modulo in pochi semplici passi.',
        color=0x5865F2,
        timestamp=datetime.now()
    )
    for k, v in RUOLI_LABEL.items():
        embed.add_field(name=v, value=f'Invia modulo per {k.upper()}', inline=True)
    embed.set_footer(text='ExoMC Recruitment System • Made by 0xGhost99')
    await ctx.send(embed=embed, view=SelfApplyView())

@bot.command()
async def risposte(ctx):
    if not is_staff(ctx.author): return await ctx.send('❌ Errore permessi.')
    await ctx.send(embed=discord.Embed(title='📥 Pannello Risposte Rapide', description='Usa i pulsanti per rispondere.', color=0x2C3E50), view=ReplyPanel())

@bot.command()
async def urgenza(ctx):
    if not is_staff(ctx.author): return
    if not ctx.channel.name.startswith('🚨'): await ctx.channel.edit(name=f'🚨-{ctx.channel.name}')
    await ctx.send(embed=discord.Embed(title='🚨 Ticket Impostato su URGENTE', color=0xE74C3C))

@bot.command()
async def add_staff(ctx, membro_raw: str):
    if not is_staff(ctx.author): return
    membro = await find_user(ctx, membro_raw)
    if miembro:
        await ctx.channel.set_permissions(membro, read_messages=True, send_messages=True, view_channel=True)
        await ctx.send(embed=discord.Embed(title='✅ Membro Aggiunto', description=f'{membro.mention} aggiunto.', color=0x2ECC71))

@bot.command()
async def nota(ctx, *, messaggio: str):
    if not is_staff(ctx.author): return
    embed = discord.Embed(title='🗂️ Nota Interna Staff', color=0xF39C12, timestamp=datetime.now())
    embed.add_field(name='✍️ Staff', value=ctx.author.mention)
    embed.add_field(name='📝 Nota', value=messaggio, inline=False)
    await ctx.send(embed=embed)

@bot.command()
async def valutazione(ctx):
    if not is_staff(ctx.author): return
    await ctx.send(embed=discord.Embed(title='📊 Scheda di Valutazione', description='• 🎯 Chiarezza\n• 🧠 Maturità\n• ⚙️ Tecnica\n• ⏱️ Disponibilità', color=0x5865F2))

@bot.command()
async def sospendi(ctx):
    if not is_staff(ctx.author): return
    await ctx.send(embed=discord.Embed(title='⏸️ Revisione Sospesa', description='La candidatura è momentaneamente sospesa.', color=0xF1C40F))

@bot.command()
async def remind(ctx):
    if not is_staff(ctx.author): return
    await ctx.send(embed=discord.Embed(title='🔔 Promemoria Staff', description='Verificare risposte, copia-incolla e comportamento.', color=0x9B59B6))

@bot.command(name='help_exo')
async def help_exo(ctx):
    embed = discord.Embed(title='📖 Comandi ExoMC Bot', color=0x5865F2)
    embed.add_field(name='🛡️ Comandi Staff', value='`!candidatura` `!risposte` `!urgenza` `!add_staff` `!nota` `!valutazione` `!sospendi` `!remind`', inline=False)
    await ctx.send(embed=embed)

@bot.event
async def on_ready():
    await bot.change_presence(status=discord.Status.online, activity=discord.Activity(type=discord.ActivityType.watching, name='ExoMC • !apply'))
    print(f'[✓] ExoMC Bot online.')

bot.run(TOKEN)
