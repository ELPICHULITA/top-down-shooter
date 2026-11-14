import os
import random
import sys
import pygame

from settings import *
from jogador import Jogador
from inimigo import Inimigo
import itens
from itens import Pickup, Bumerangue, Bomba, Explosao, TIPOS

NOMES = {
    "triangulo": "Triângulo! Imune por 8s",
    "bumerangue": "Bumerangue +{}".format(BUMERANGUES_POR_ITEM),
    "bomba": "Bombas +{}".format(BOMBAS_POR_ITEM),
    "escudo": "Escudo! Aguenta {} golpes".format(ESCUDO_MAX),
    "gelo": "Gelo! Inimigos congelados por {}s".format(DURACAO_GELO_MS // 1000),
    "cura": "Poção! +{} de vida".format(CURA_QTD),
    "bota": "Bota! Velocidade por {}s".format(DURACAO_BOTA_MS // 1000),
}


class Jogo:
    def __init__(self):
        pygame.init()
        self.tela = pygame.display.set_mode((LARGURA, ALTURA))
        pygame.display.set_caption(TITULO)
        pygame.mouse.set_visible(False)   # usamos a mira desenhada
        self.relogio = pygame.time.Clock()
        self.fonte = pygame.font.SysFont(None, 48)
        self.fonte_pequena = pygame.font.SysFont(None, 28)
        self.fonte_mini = pygame.font.SysFont(None, 22)
        self.limites = self.tela.get_rect()
        self.area_itens = pygame.Rect(*AREA_ITENS)
        fundo = pygame.image.load(os.path.join(
            os.path.dirname(__file__), "sprites", "fundo", "sala.png"))
        self.fundo = pygame.transform.scale(
            fundo.convert(), (LARGURA, ALTURA))
        itens.sprites()
        self.reiniciar()

    def reiniciar(self):
        self.jogador = Jogador(425, 275)
        self.inimigos = []
        while len(self.inimigos) < QTD_INIMIGOS:
            x = random.randint(0, LARGURA - TAM_INIMIGO)
            y = random.randint(0, ALTURA - TAM_INIMIGO)
            # não nasce em cima do jogador
            if pygame.Vector2(x, y).distance_to(self.jogador.rect.center) > 250:
                self.inimigos.append(Inimigo(x, y))
        self.pickups = []
        self.bumerangue = None
        self.bombas = []
        self.explosoes = []
        self.proximo_item = pygame.time.get_ticks() + 4000
        self.aviso = ""
        self.aviso_ate = 0

    # ---------------------------------------------------------------- ações
    def jogando(self):
        return not self.jogador.morto and bool(self.inimigos)

    def lancar_bumerangue(self):
        j = self.jogador
        if not self.jogando() or self.bumerangue or j.bumerangues <= 0:
            return
        j.bumerangues -= 1
        self.bumerangue = Bumerangue(j.rect.center, j.mira)

    def jogar_bomba(self, agora):
        j = self.jogador
        if not self.jogando() or j.bombas <= 0:
            return
        j.bombas -= 1
        origem = pygame.Vector2(j.rect.center)
        v = pygame.Vector2(pygame.mouse.get_pos()) - origem
        if v.length() > ALCANCE_BOMBA:
            v = v.normalize() * ALCANCE_BOMBA
        alvo = origem + v
        alvo.x = max(20, min(LARGURA - 20, alvo.x))
        alvo.y = max(20, min(ALTURA - 20, alvo.y))
        self.bombas.append(Bomba(origem, alvo, agora))

    def pegar(self, pickup, agora):
        j = self.jogador
        if pickup.tipo == "triangulo":
            j.invencivel_ate = agora + DURACAO_TRIANGULO_MS
        elif pickup.tipo == "escudo":
            j.escudo = ESCUDO_MAX
        elif pickup.tipo == "bumerangue":
            j.bumerangues = min(MAX_MUNICAO, j.bumerangues + BUMERANGUES_POR_ITEM)
        elif pickup.tipo == "bomba":
            j.bombas = min(MAX_MUNICAO, j.bombas + BOMBAS_POR_ITEM)
        elif pickup.tipo == "gelo":
            for inimigo in self.inimigos:
                inimigo.congelado_ate = agora + DURACAO_GELO_MS
        elif pickup.tipo == "cura":
            j.vida = min(VIDA_JOGADOR, j.vida + CURA_QTD)
        elif pickup.tipo == "bota":
            j.bota_ate = agora + DURACAO_BOTA_MS
        self.aviso = NOMES[pickup.tipo]
        self.aviso_ate = agora + 1500

    # --------------------------------------------------------------- eventos
    def eventos(self):
        agora = pygame.time.get_ticks()
        for evento in pygame.event.get():
            if evento.type == pygame.QUIT:
                pygame.quit()
                sys.exit()
            if evento.type == pygame.MOUSEBUTTONDOWN:
                if evento.button == 1 and self.jogando():
                    self.jogador.atacar(agora)
                elif evento.button == 3:
                    self.lancar_bumerangue()
            if evento.type == pygame.KEYDOWN:
                if evento.key in (pygame.K_SPACE, pygame.K_j) and self.jogando():
                    self.jogador.atacar(agora)
                elif evento.key == pygame.K_q:
                    self.lancar_bumerangue()
                elif evento.key == pygame.K_e:
                    self.jogar_bomba(agora)
                elif evento.key == pygame.K_r:
                    self.reiniciar()

    # ------------------------------------------------------------ atualização
    def atualizar(self):
        if not self.jogando():
            return
        agora = pygame.time.get_ticks()
        j = self.jogador
        j.atualizar(pygame.key.get_pressed(), self.limites,
                    pygame.mouse.get_pos(), agora)

        for inimigo in self.inimigos:
            inimigo.atualizar(j.rect.center, self.limites, agora)

            # inimigo encosta no jogador (congelado não machuca)
            if not inimigo.congelado(agora) and inimigo.rect.colliderect(j.rect):
                j.receber_dano(agora, inimigo.rect.center, self.limites)

            # espada acerta o inimigo
            if j.acerta(inimigo.rect, agora):
                inimigo.receber_dano(DANO_ATAQUE, j.rect.center, agora)

        self.atualizar_bumerangue(agora)
        self.atualizar_bombas(agora)
        self.atualizar_itens(agora)

        # inimigos derrotados podem soltar um power-up
        for inimigo in self.inimigos:
            if inimigo.morto and random.random() < CHANCE_DROP:
                self.pickups.append(
                    Pickup(random.choice(TIPOS), inimigo.rect.center, agora))
        self.inimigos = [i for i in self.inimigos if not i.morto]

    def atualizar_bumerangue(self, agora):
        b = self.bumerangue
        if not b:
            return
        b.atualizar(self.jogador.rect.center, self.limites)
        for inimigo in self.inimigos:
            if id(inimigo) not in b.acertados and b.rect.colliderect(inimigo.rect):
                b.acertados.add(id(inimigo))
                inimigo.receber_dano(DANO_BUMERANGUE, b.pos, agora)
        if b.fim:
            self.bumerangue = None

    def atualizar_bombas(self, agora):
        for b in self.bombas:
            b.atualizar(agora)
        for b in self.bombas:
            if not b.explodiu:
                continue
            self.explosoes.append(Explosao(b.pos, agora))
            for inimigo in self.inimigos:
                d = pygame.Vector2(inimigo.rect.center).distance_to(b.pos)
                if d <= RAIO_BOMBA + TAM_INIMIGO / 2:
                    inimigo.invulneravel_ate = 0
                    inimigo.receber_dano(DANO_BOMBA, b.pos, agora)
        self.bombas = [b for b in self.bombas if not b.explodiu]
        self.explosoes = [e for e in self.explosoes if e.ativa(agora)]

    def atualizar_itens(self, agora):
        if agora >= self.proximo_item:
            self.proximo_item = agora + INTERVALO_ITEM_MS
            if len(self.pickups) < MAX_ITENS_NO_CHAO:
                x = random.randint(self.area_itens.left, self.area_itens.right)
                y = random.randint(self.area_itens.top, self.area_itens.bottom)
                self.pickups.append(Pickup(random.choice(TIPOS), (x, y), agora))
        restantes = []
        for p in self.pickups:
            if p.expirou(agora):
                continue
            if self.jogador.rect.colliderect(p.rect):
                if p.tipo == "cura" and self.jogador.vida >= VIDA_JOGADOR:
                    restantes.append(p)   # vida cheia: a poção espera no chão
                    continue
                self.pegar(p, agora)
                continue
            restantes.append(p)
        self.pickups = restantes

    # ---------------------------------------------------------------- desenho
    def texto(self, fonte, msg, pos, cor=BRANCO, centro=False):
        sombra = fonte.render(msg, True, PRETO)
        img = fonte.render(msg, True, cor)
        r = img.get_rect(center=pos) if centro else img.get_rect(topleft=pos)
        self.tela.blit(sombra, (r.x + 2, r.y + 2))
        self.tela.blit(img, r)
        return r

    def desenhar_hud(self, agora):
        j = self.jogador
        for i in range(VIDA_JOGADOR):
            cor = VERMELHO if i < j.vida else CINZA
            pygame.draw.rect(self.tela, cor, (10 + i * 28, 10, 22, 22))
        t = self.fonte_pequena.render(f"Inimigos: {len(self.inimigos)}", True, BRANCO)
        self.tela.blit(t, (LARGURA - t.get_width() - 10, 12))

        # munição e escudo
        x = 10
        for tipo, qtd in (("bumerangue", j.bumerangues), ("bomba", j.bombas)):
            icone = itens.icone_hud(tipo)
            self.tela.blit(icone, (x, 40 + (26 - icone.get_height()) // 2))
            r = self.texto(self.fonte_pequena, f"x{qtd}", (x + 30, 44))
            x = r.right + 18
        icone = itens.icone_hud("escudo", 22)
        for i in range(ESCUDO_MAX):
            img = icone if i < j.escudo else icone.copy()
            if i >= j.escudo:
                img.set_alpha(60)
            self.tela.blit(img, (x + i * 24, 42))

        # tempo dos efeitos ativos: imunidade, gelo e bota
        efeitos = [
            ("triangulo", j.invencivel_ate, DURACAO_TRIANGULO_MS, AMARELO),
            ("gelo", max((i.congelado_ate for i in self.inimigos), default=0),
             DURACAO_GELO_MS, (120, 200, 240)),
            ("bota", j.bota_ate, DURACAO_BOTA_MS, (60, 220, 220)),
        ]
        y = 72
        for tipo, fim, total, cor in efeitos:
            if agora >= fim:
                continue
            restante = (fim - agora) / total
            self.tela.blit(itens.icone_hud(tipo, 24), (10, y))
            pygame.draw.rect(self.tela, CINZA, (42, y + 6, 120, 10))
            pygame.draw.rect(self.tela, cor, (42, y + 6, int(120 * restante), 10))
            y += 28

        if agora < self.aviso_ate:
            self.texto(self.fonte_pequena, self.aviso,
                       (LARGURA // 2, 130), AMARELO, centro=True)

        self.texto(
            self.fonte_mini,
            "WASD mover   |   Mouse mira   |   Clique esq. espada   |"
            "   Clique dir. bumerangue   |   E bomba",
            (LARGURA // 2, ALTURA - 20), centro=True)

    def desenhar_mira(self):
        mx, my = pygame.mouse.get_pos()
        pygame.draw.circle(self.tela, BRANCO, (mx, my), 11, 2)
        for dx, dy in ((-18, 0), (7, 0), (0, -18), (0, 7)):
            if dx:
                pygame.draw.line(self.tela, BRANCO, (mx + dx, my), (mx + dx + 11, my), 2)
            else:
                pygame.draw.line(self.tela, BRANCO, (mx, my + dy), (mx, my + dy + 11), 2)
        pygame.draw.circle(self.tela, VERMELHO, (mx, my), 2)

    def mensagem(self, titulo):
        t = self.fonte.render(titulo, True, BRANCO)
        s = self.fonte_pequena.render("Pressione R para jogar de novo", True, BRANCO)
        self.tela.blit(t, t.get_rect(center=(LARGURA // 2, ALTURA // 2 - 20)))
        self.tela.blit(s, s.get_rect(center=(LARGURA // 2, ALTURA // 2 + 25)))

    def desenhar(self):
        agora = pygame.time.get_ticks()
        self.tela.blit(self.fundo, (0, 0))
        for p in self.pickups:
            p.desenhar(self.tela, agora)
        for b in self.bombas:
            b.desenhar(self.tela, agora)
        for e in self.explosoes:
            if e.ativa(agora):
                e.desenhar(self.tela, agora)
        for inimigo in self.inimigos:
            inimigo.desenhar(self.tela, agora)
        if self.bumerangue:
            self.bumerangue.desenhar(self.tela, agora)
        self.jogador.desenhar(self.tela, agora)
        self.desenhar_hud(agora)
        if self.jogador.morto:
            self.mensagem("Game Over")
        elif not self.inimigos:
            self.mensagem("Você venceu!")
        self.desenhar_mira()
        pygame.display.update()

    def rodar(self):
        while True:
            self.eventos()
            self.atualizar()
            self.desenhar()
            self.relogio.tick(FPS)


if __name__ == "__main__":
    Jogo().rodar()
