# Nome do Arquivo: bot_principal.py
import discord
from discord.ext import commands
from discord import ui, app_commands
import asyncio
import os # [!!!] IMPORTADO PARA LER O TOKEN DE FORMA SEGURA
from webserver import keep_alive # [!!!] IMPORTA O CÓDIGO DO OUTRO ARQUIVO

# --- CONFIGURAÇÃO DO BOT PRINCIPAL ---
# [!!!] O TOKEN AGORA É CARREGADO DE FORMA SEGURA PELO REPLIT
TOKEN = os.environ['TOKEN'] 
STAFF_ROLE_ID = 1402869595399782460
PURCHASE_CATEGORY_ID = 1402895226607239229
FEEDBACK_CHANNEL_ID = 1402855899219099708
LOG_CHANNEL_ID = 1402888843073556500
INITIAL_ROLE_ID = 1402869595966279681
CUSTOMER_ROLE_ID = 1402869595718811769
CHAVE_PIX = "a9564dac-f6e3-47f5-ac1a-a062cc03b560"
# --- FIM DA CONFIGURAÇÃO ---

intents = discord.Intents.default()
intents.members = True
intents.message_content = True
bot = commands.Bot(command_prefix="+", intents=intents)

# --- VIEWS (COMPONENTES INTERATIVOS) ---

class FeedbackView(ui.View):
    def __init__(self):
        super().__init__(timeout=None)
    @ui.button(label="⭐", custom_id="star_1_vfinal_final")
    async def star_1(self, i: discord.Interaction, b: ui.Button): await self.send_feedback(i, 1)
    @ui.button(label="⭐⭐", custom_id="star_2_vfinal_final")
    async def star_2(self, i: discord.Interaction, b: ui.Button): await self.send_feedback(i, 2)
    @ui.button(label="⭐⭐⭐", custom_id="star_3_vfinal_final")
    async def star_3(self, i: discord.Interaction, b: ui.Button): await self.send_feedback(i, 3)
    @ui.button(label="⭐⭐⭐⭐", custom_id="star_4_vfinal_final")
    async def star_4(self, i: discord.Interaction, b: ui.Button): await self.send_feedback(i, 4)
    @ui.button(label="⭐⭐⭐⭐⭐", style=discord.ButtonStyle.primary, custom_id="star_5_vfinal_final")
    async def star_5(self, i: discord.Interaction, b: ui.Button): await self.send_feedback(i, 5)
    async def send_feedback(self, interaction: discord.Interaction, rating: int):
        feedback_channel = interaction.client.get_channel(FEEDBACK_CHANNEL_ID)
        if feedback_channel:
            embed = discord.Embed(title="⭐ Novo Feedback", description=f"{interaction.user.mention} avaliou com **{rating} estrela(s)**.", color=discord.Color.gold())
            await feedback_channel.send(embed=embed)
        for item in self.children: item.disabled = True
        await interaction.message.edit(view=self)
        await interaction.response.send_message("Obrigado!", ephemeral=True)

class StaffPurchaseInteractionView(ui.View):
    def __init__(self, product_title: str, product_link: str or None):
        super().__init__(timeout=None)
        self.product_title = product_title
        self.product_link = product_link

    @ui.button(label="PIX Copia e Cola", style=discord.ButtonStyle.blurple, emoji="📋", custom_id="staff_pix_copy_final_final")
    async def pix_copy(self, interaction: discord.Interaction, button: ui.Button):
        await interaction.response.send_message(f"```{CHAVE_PIX}```", ephemeral=True)

    @ui.button(label="Aprovar Pagamento", style=discord.ButtonStyle.success, emoji="✅", custom_id="staff_approve_payment_final_final")
    async def approve_payment(self, interaction: discord.Interaction, button: ui.Button):
        staff_role = interaction.guild.get_role(STAFF_ROLE_ID)
        if staff_role not in interaction.user.roles:
            return await interaction.response.send_message("❌ Apenas membros da Staff podem aprovar pagamentos.", ephemeral=True)
        await interaction.response.defer()
        try:
            member_id_str = interaction.channel.topic.split("ID: ")[1]
            member = interaction.guild.get_member(int(member_id_str))
            if not member: raise ValueError
        except (IndexError, ValueError):
            return await interaction.followup.send("❌ Não foi possível encontrar o criador do ticket. Feche manualmente.", ephemeral=True)
        
        for item in self.children: item.disabled = True
        await interaction.message.edit(view=self)
        
        log_channel = bot.get_channel(LOG_CHANNEL_ID)
        if log_channel:
            await log_channel.send(embed=discord.Embed(title="✔️ Compra Aprovada", description=f"O pagamento de {member.mention} por **{self.product_title}** foi aprovado por {interaction.user.mention}.", color=discord.Color.green()))
        
        try:
            customer_role = interaction.guild.get_role(CUSTOMER_ROLE_ID)
            if customer_role: await member.add_roles(customer_role)
        except discord.Forbidden:
            if log_channel: await log_channel.send(f"⚠️ Erro ao dar cargo de cliente para {member.mention}.")

        if self.product_link:
            try:
                await member.send(embed=discord.Embed(title="✅ Compra Realizada!", description=f"Seu pagamento foi aprovado! Link de download (Mega.nz):\n{self.product_link}", color=discord.Color.green()))
                await member.send(embed=discord.Embed(title="Avalie sua Compra", description="Sua opinião é importante!", color=discord.Color.blue()), view=FeedbackView())
                await interaction.followup.send(f"✅ Pagamento aprovado. Produto enviado para a DM de {member.mention}.", ephemeral=False)
                await interaction.channel.send("Este ticket será fechado em 10 segundos.")
                await asyncio.sleep(10)
                await interaction.channel.delete()
            except discord.Forbidden:
                await interaction.followup.send(f"⚠️ Não consegui enviar a DM para {member.mention}! A entrega não pôde ser concluída.", ephemeral=False)
        else:
            try:
                await member.send(embed=discord.Embed(title="✅ Pagamento Aprovado!", description=f"Seu pagamento por **{self.product_title}** foi aprovado!\n\nUm membro da staff irá contatá-lo(a) em breve para realizar a entrega do serviço.", color=discord.Color.green()))
                await member.send(embed=discord.Embed(title="Avalie sua Compra", description="Sua opinião é importante!", color=discord.Color.blue()), view=FeedbackView())
            except discord.Forbidden:
                await interaction.followup.send(f"⚠️ Não consegui notificar o membro na DM!", ephemeral=False)
            
            await interaction.followup.send(f"Pagamento aprovado. O ticket foi mantido aberto para a entrega manual. Use `+close` para fechar quando terminar.", ephemeral=False)

class ProductPurchaseView(ui.View):
    def __init__(self):
        super().__init__(timeout=None)
    @ui.button(label="Comprar Agora", style=discord.ButtonStyle.success, emoji="🛒", custom_id="final_buy_now_vfinal_final")
    async def buy_now_button(self, interaction: discord.Interaction, button: ui.Button):
        await interaction.response.defer(ephemeral=True)
        original_embed = interaction.message.embeds[0]
        product_title = original_embed.title
        product_link = original_embed.footer.icon_url
        if product_link == "http://example.com/a.png": product_link = None
        guild, user = interaction.guild, interaction.user
        category = guild.get_channel(PURCHASE_CATEGORY_ID)
        staff_role = guild.get_role(STAFF_ROLE_ID)
        overwrites = {guild.default_role: discord.PermissionOverwrite(read_messages=False), user: discord.PermissionOverwrite(read_messages=True), staff_role: discord.PermissionOverwrite(read_messages=True)}
        channel = await guild.create_text_channel(name=f"compra-{user.name}", category=category, overwrites=overwrites, topic=f"ID: {user.id}")
        await interaction.followup.send(f"✅ Seu ticket foi criado em {channel.mention}!", ephemeral=True)
        embed = discord.Embed(title=f"🛒 Compra: {product_title}", description=f"Olá {user.mention}! Para prosseguir, pague o PIX e **envie o comprovante aqui**.\n\nAguarde um staff aprovar seu pagamento.", color=0x3498db)
        await channel.send(content=f"{user.mention} {staff_role.mention}", embed=embed, view=StaffPurchaseInteractionView(product_title, product_link))

class EmbedCreatorModal(ui.Modal, title="Criador de Embed de Produto"):
    embed_title = ui.TextInput(label="Nome do Produto / Título da Embed", required=True)
    embed_description = ui.TextInput(label="Descrição", style=discord.TextStyle.paragraph, required=True)
    price_and_stock = ui.TextInput(label="Preço e Estoque (separados por |)", placeholder="Ex: 19,99 | 10", required=True)
    product_link = ui.TextInput(label="Link do Produto (Mega.nz)", placeholder="Deixe em branco se for um serviço", required=False)
    embed_image_url = ui.TextInput(label="URL da Imagem (PNG/JPG, Opcional)", placeholder="https://i.imgur.com/exemplo.png", required=False)

    async def on_submit(self, interaction: discord.Interaction):
        await interaction.response.defer(ephemeral=True)
        try:
            price_str, stock_str = self.price_and_stock.value.split('|')
            price = price_str.strip()
            stock = stock_str.strip()
        except ValueError:
            await interaction.followup.send("❌ **Erro de Formato!** Use o formato `Preço | Estoque` (Ex: `19,99 | 10`).", ephemeral=True)
            return

        link = self.product_link.value or None
        image_url = self.embed_image_url.value or None

        if link and not link.startswith("https://mega.nz/"):
            return await interaction.followup.send("❌ Erro: Se for fornecer um link, ele deve ser do Mega.nz.", ephemeral=True)
        
        embed = discord.Embed(title=self.embed_title.value, description=self.embed_description.value, color=0x2b2d31)
        embed.add_field(name="📝 Produto", value=f"```{self.embed_title.value}```", inline=True)
        embed.add_field(name="💲 Preço", value=f"```R$ {price}```", inline=True)
        embed.add_field(name="📦 Estoque", value=f"```{stock}```", inline=True)
        if image_url:
            embed.set_image(url=image_url)
        icon_url_for_footer = link if link else "http://example.com/a.png"
        embed.set_footer(text="Clique em Comprar Agora para adquirir.", icon_url=icon_url_for_footer)
        
        await interaction.channel.send(embed=embed, view=ProductPurchaseView())
        await interaction.followup.send("✅ Embed criada com sucesso!", ephemeral=True)

# --- EVENTOS E COMANDOS ---
@bot.event
async def on_ready():
    print(f'Bot Principal conectado como {bot.user}')
    await bot.change_presence(activity=discord.Game(name="Ajudando na CyberStore"))
    print("Status do bot atualizado com sucesso.")
    bot.add_view(ProductPurchaseView())
    bot.add_view(FeedbackView())
    bot.add_view(StaffPurchaseInteractionView("",""))
    try:
        synced = await bot.tree.sync()
        print(f"Sincronizados {len(synced)} comandos.")
    except Exception as e: print(f"Erro ao sincronizar comandos: {e}")

@bot.event
async def on_member_join(member: discord.Member):
    try:
        role = member.guild.get_role(INITIAL_ROLE_ID)
        if role: await member.add_roles(role)
    except Exception as e: print(f"Erro ao dar cargo: {e}")

@bot.tree.command(name="criarembed", description="Cria uma embed de produto (com ou sem link).")
@app_commands.checks.has_permissions(administrator=True)
async def create_embed_command(interaction: discord.Interaction):
    await interaction.response.send_modal(EmbedCreatorModal())

@bot.tree.error
async def on_app_command_error(interaction: discord.Interaction, error: app_commands.AppCommandError):
    if isinstance(error, app_commands.MissingPermissions):
        await interaction.response.send_message("❌ Você não tem permissão para usar este comando.", ephemeral=True)
    else:
        raise error

@bot.command(name="lock")
@commands.has_permissions(manage_channels=True)
async def lock(ctx: commands.Context):
    await ctx.channel.set_permissions(ctx.guild.default_role, send_messages=False)
    await ctx.send(embed=discord.Embed(description="🔒 Canal bloqueado.", color=0xff0000))

@bot.command(name="unlock")
@commands.has_permissions(manage_channels=True)
async def unlock(ctx: commands.Context):
    await ctx.channel.set_permissions(ctx.guild.default_role, send_messages=True)
    await ctx.send(embed=discord.Embed(description="🔓 Canal desbloqueado.", color=0x00ff00))

@bot.command(name="close")
@commands.has_permissions(manage_messages=True)
async def close(ctx: commands.Context):
    await ctx.send("Este ticket será fechado em 5 segundos...")
    await asyncio.sleep(5)
    await ctx.channel.delete()

@bot.event
async def on_command_error(ctx, error):
    if isinstance(error, commands.MissingPermissions):
        await ctx.send("❌ Você não tem permissão para usar este comando.")
    else: print(f"Erro em comando de prefixo: {error}")


# [!!!] ESTAS DUAS LINHAS INICIAM O SERVIDOR WEB E O BOT
keep_alive()
bot.run(TOKEN)