import discord
from discord import app_commands
from discord.ext import commands
import json
import os
from datetime import datetime

ARQUIVO_DADOS = "dados_conquistas.json"
ARQUIVO_MSG = "contador_msgs.json"
ARQUIVO_CODIGOS = "codigos_usados.json"

COR_JUJUTSU = 0x7B2CFF
CANAL_CONQUISTAS_ID = 1498134533839650838


CONQUISTAS = {
    "primeiro_selo": {"emoji": "🩸", "nome": "Primeiro Selo", "descricao": "Despertou sua primeira marca."},
    "dominio_revelado": {"emoji": "🌀", "nome": "Domínio Revelado", "descricao": "Visualizou suas conquistas."},
    "contrato_aberto": {"emoji": "📜", "nome": "Contrato Aberto", "descricao": "Abriu um ticket."},
    "voz_do_dominio": {"emoji": "📢", "nome": "Voz do Domínio", "descricao": "50 mensagens."},
    "presenca_constante": {"emoji": "👁️", "nome": "Presença Constante", "descricao": "100 mensagens."},
    "energia_instavel": {"emoji": "🔥", "nome": "Energia Instável", "descricao": "200 mensagens."},
    "sangue_familia": {"emoji": "🩸", "nome": "Sangue da Família", "descricao": "Entrou no servidor."},
    "exorcista_vitorioso": {"emoji": "⚔️", "nome": "Exorcista Vitorioso", "descricao": "Venceu evento."},
    "sombra_oculta": {"emoji": "🔒", "nome": "???", "descricao": "Segredo..."},
    "lenda_proibida": {"emoji": "🕯️", "nome": "???", "descricao": "Lenda proibida..."}
}


# ================= JSON =================
def carregar_json(arq):
    if not os.path.exists(arq):
        with open(arq, "w") as f:
            json.dump({}, f)
    with open(arq, "r") as f:
        return json.load(f)

def salvar_json(arq, data):
    with open(arq, "w") as f:
        json.dump(data, f, indent=4)


def carregar_dados(): return carregar_json(ARQUIVO_DADOS)
def salvar_dados(d): salvar_json(ARQUIVO_DADOS, d)

def carregar_msgs(): return carregar_json(ARQUIVO_MSG)
def salvar_msgs(d): salvar_json(ARQUIVO_MSG, d)

def carregar_codigos(): return carregar_json(ARQUIVO_CODIGOS)
def salvar_codigos(d): salvar_json(ARQUIVO_CODIGOS, d)


# ================= CONQUISTA =================
async def liberar_conquista(bot, user, cid, canal=None):
    dados = carregar_dados()
    uid = str(user.id)

    if uid not in dados:
        dados[uid] = {}

    if cid in dados[uid]:
        return False

    dados[uid][cid] = datetime.now().strftime("%d/%m/%Y %H:%M")
    salvar_dados(dados)

    c = CONQUISTAS[cid]

    canal_conq = bot.get_channel(CANAL_CONQUISTAS_ID)
    if canal_conq:
        embed = discord.Embed(
            title="🏆 Nova Conquista",
            description=f"{user.mention}\n\n{c['emoji']} **{c['nome']}**\n{c['descricao']}",
            color=COR_JUJUTSU
        )
        await canal_conq.send(embed=embed)

    return True


# ================= VIEW =================
class ViewConquistas(discord.ui.View):
    def __init__(self, user, paginas):
        super().__init__(timeout=60)
        self.user = user
        self.paginas = paginas
        self.pagina = 0

    async def update(self, i):
        await i.response.edit_message(embed=self.paginas[self.pagina], view=self)

    @discord.ui.button(label="⬅️")
    async def prev(self, i, b):
        if i.user != self.user: return
        self.pagina = max(0, self.pagina-1)
        await self.update(i)

    @discord.ui.button(label="➡️")
    async def next(self, i, b):
        if i.user != self.user: return
        self.pagina = min(len(self.paginas)-1, self.pagina+1)
        await self.update(i)


# ================= COG =================
class Conquistas(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.Cog.listener()
    async def on_message(self, msg):
        if msg.author.bot:
            return

        data = carregar_msgs()
        uid = str(msg.author.id)
        data[uid] = data.get(uid, 0) + 1
        salvar_msgs(data)

        t = data[uid]

        if t == 1:
            await liberar_conquista(self.bot, msg.author, "primeiro_selo")
        elif t == 50:
            await liberar_conquista(self.bot, msg.author, "voz_do_dominio")
        elif t == 100:
            await liberar_conquista(self.bot, msg.author, "presenca_constante")
        elif t == 200:
            await liberar_conquista(self.bot, msg.author, "energia_instavel")

    @commands.Cog.listener()
    async def on_member_join(self, m):
        await liberar_conquista(self.bot, m, "sangue_familia")

    @app_commands.command(name="conquistas")
    async def conquistas(self, i: discord.Interaction):
        await liberar_conquista(self.bot, i.user, "dominio_revelado")

        d = carregar_dados().get(str(i.user.id), {})
        lista = []

        for cid, c in CONQUISTAS.items():
            lista.append(f"{c['emoji']} {c['nome']}" if cid in d else "🔒 Bloqueado")

        pags = []
        for x in range(0, len(lista), 4):
            pags.append(discord.Embed(
                title="🌀 Conquistas",
                description="\n".join(lista[x:x+4]),
                color=COR_JUJUTSU
            ))

        await i.response.send_message(
            embed=pags[0],
            view=ViewConquistas(i.user, pags),
            ephemeral=True
        )

    # ================= CÓDIGOS =================
    @app_commands.command(name="codigo")
    async def codigo(self, i: discord.Interaction, codigo: str):

        codigos = {
            "MAHORAGA": {"c": "sombra_oculta", "limite": 1},
            "SUKUNAHEIAN": {"c": "lenda_proibida", "limite": 5}
        }

        codigo = codigo.upper().replace(" ", "")

        if codigo not in codigos:
            return await i.response.send_message("❌ Código inválido.", ephemeral=True)

        data = carregar_codigos()
        usados = data.get(codigo, [])
        uid = str(i.user.id)

        if uid in usados:
            return await i.response.send_message("❌ Você já usou.", ephemeral=True)

        if len(usados) >= codigos[codigo]["limite"]:
            return await i.response.send_message("❌ Código esgotado.", ephemeral=True)

        await liberar_conquista(self.bot, i.user, codigos[codigo]["c"])

        usados.append(uid)
        data[codigo] = usados
        salvar_codigos(data)

        limite = codigos[codigo]["limite"]
        restantes = limite - len(usados)

        tipo = "LENDÁRIO 🔥" if limite == 1 else "RARO ⚡"

        await i.response.send_message(
            f"✅ Código aceito!\n\n"
            f"🏆 Tipo: **{tipo}**\n"
            f"🔢 Restantes: **{restantes}/{limite}**",
            ephemeral=True
        )

        # 👑 EVENTO LENDÁRIO
        if limite == 1:
            canal_conq = self.bot.get_channel(CANAL_CONQUISTAS_ID)

            if canal_conq:
                embed_lenda = discord.Embed(
                    title="👑 O ESCOLHIDO DESPERTOU",
                    description=(
                        f"{i.user.mention} foi o **único** capaz de romper a barreira.\n\n"
                        f"🔥 Código Lendário: **{codigo}**\n"
                        f"🏆 Conquista exclusiva liberada.\n\n"
                        f"Uma lenda proibida acaba de nascer dentro da Família Sant’s."
                    ),
                    color=0xFF0000
                )

                embed_lenda.set_thumbnail(url=i.user.display_avatar.url)
                embed_lenda.set_footer(text="Família Sant’s • Evento Lendário")

                await canal_conq.send(embed=embed_lenda)


async def setup(bot):
    await bot.add_cog(Conquistas(bot))