import math
import os
import pygame
from settings import *


class Jogador:
    def __init__(self, x, y):
        self.rect = pygame.Rect(x, y, TAM_JOGADOR, TAM_JOGADOR)
        self.pos = pygame.Vector2(self.rect.topleft)
        self.velocidade = VEL_JOGADOR
        self.vida = VIDA_JOGADOR

        # mira: vetor unitário apontando para o mouse
        self.mira = pygame.Vector2(0, 1)
        self.face = "baixo"

        # espada
        self.ataque_inicio = 0
        self.ataque_fim = 0
        self.ataque_pronto = 0
        self.ataque_ang = 0.0

        self.invulneravel_ate = 0

        # power-ups
        self.escudo = 0
        self.invencivel_ate = 0
        self.bota_ate = 0
        self.bumerangues = 0
        self.bombas = 0

        base = os.path.join(os.path.dirname(__file__), "sprites")

        # sprites: 3 quadros de caminhada para cada direção
        self.quadros = {}
        for nome in ("baixo", "cima", "esq", "dir"):
            self.quadros[nome] = []
            for i in range(3):
                img = pygame.image.load(
                    os.path.join(base, "jogador", f"{nome}_{i}.png")).convert_alpha()
                img = pygame.transform.scale(
                    img, (img.get_width() * ESCALA_JOGADOR,
                          img.get_height() * ESCALA_JOGADOR))
                self.quadros[nome].append(img)
        self.andando = False
        self.passo = 0.0

        espada = pygame.image.load(
            os.path.join(base, "itens", "espada.png")).convert_alpha()
        self.espada = pygame.transform.scale(
            espada, (espada.get_width() * ESCALA_ESPADA,
                     espada.get_height() * ESCALA_ESPADA))
        escudo = pygame.image.load(
            os.path.join(base, "itens", "escudo.png")).convert_alpha()
        self.escudo_img = pygame.transform.scale(escudo, (36, 38))

    @property
    def morto(self):
        return self.vida <= 0

    def imune(self, agora):
        return agora < self.invencivel_ate

    def veloz(self, agora):
        return agora < self.bota_ate

    # ------------------------------------------------------------ movimento
    def atualizar(self, teclas, limites, mouse_pos, agora):
        mov = pygame.Vector2(
            teclas[pygame.K_d] - teclas[pygame.K_a],
            teclas[pygame.K_s] - teclas[pygame.K_w],
        )

        self.andando = mov.length_squared() > 0
        if self.andando:
            mult = MULT_BOTA if self.veloz(agora) else 1
            self.passo += 0.15 * mult
            self.pos += mov.normalize() * self.velocidade * mult

        self.rect.topleft = (round(self.pos.x), round(self.pos.y))
        self.rect.clamp_ip(limites)
        self.pos.update(self.rect.topleft)

        # a visão / mira segue o mouse
        ate_mouse = pygame.Vector2(mouse_pos) - pygame.Vector2(self.rect.center)
        if ate_mouse.length_squared() > 4:
            self.mira = ate_mouse.normalize()
        if abs(self.mira.x) >= abs(self.mira.y):
            self.face = "dir" if self.mira.x > 0 else "esq"
        else:
            self.face = "baixo" if self.mira.y > 0 else "cima"

    # --------------------------------------------------------------- espada
    def atacar(self, agora):
        if self.morto or agora < self.ataque_pronto:
            return
        self.ataque_inicio = agora
        self.ataque_fim = agora + DURACAO_ATAQUE_MS
        self.ataque_pronto = agora + RECARGA_ATAQUE_MS
        self.ataque_ang = math.atan2(self.mira.y, self.mira.x)

    def atacando(self, agora):
        return agora < self.ataque_fim

    def acerta(self, alvo_rect, agora):
        """True se o golpe em arco da espada alcança o alvo agora."""
        if not self.atacando(agora):
            return False
        v = pygame.Vector2(alvo_rect.center) - pygame.Vector2(self.rect.center)
        dist = v.length()
        if dist > ALCANCE_ATAQUE + alvo_rect.width / 2:
            return False
        if dist == 0:
            return True
        prog = (agora - self.ataque_inicio) / DURACAO_ATAQUE_MS
        diff = (math.atan2(v.y, v.x) - self.ataque_ang + math.pi) % (2 * math.pi) - math.pi
        inicio = -ARCO_ATAQUE / 2 - 0.3
        fim = -ARCO_ATAQUE / 2 + prog * ARCO_ATAQUE + 0.3
        return inicio <= diff <= fim

    # ----------------------------------------------------------------- dano
    def _empurrar(self, origem, limites, forca):
        empurrao = pygame.Vector2(self.rect.center) - pygame.Vector2(origem)
        if empurrao.length_squared() > 0:
            self.pos += empurrao.normalize() * forca
        self.rect.topleft = (round(self.pos.x), round(self.pos.y))
        self.rect.clamp_ip(limites)
        self.pos.update(self.rect.topleft)

    def receber_dano(self, agora, origem, limites):
        if self.imune(agora) or agora < self.invulneravel_ate:
            return

        if self.escudo > 0:           # o escudo absorve o golpe
            self.escudo -= 1
            self.invulneravel_ate = agora + 600
            self._empurrar(origem, limites, 20)
            return

        self.vida -= 1
        self.invulneravel_ate = agora + INVULNERAVEL_JOGADOR_MS
        self._empurrar(origem, limites, 40)

    # --------------------------------------------------------------- desenho
    def desenhar(self, tela, agora):
        centro = pygame.Vector2(self.rect.center)

        if self.imune(agora):
            self._desenhar_aura(tela, agora, centro)
        if self.veloz(agora):
            self._desenhar_velocidade(tela, agora)

        if agora < self.invulneravel_ate and not self.imune(agora) \
                and (agora // 100) % 2 == 0:
            return  # pisca ao levar dano

        # espada fica atrás do corpo quando a mira aponta para cima
        espada_atras = self.mira.y < -0.3
        if espada_atras:
            self._desenhar_espada(tela, agora, centro)

        indice = (0, 1, 2, 1)[int(self.passo) % 4] if self.andando else 1
        img = self.quadros[self.face][indice]
        pos = img.get_rect(midbottom=(self.rect.centerx, self.rect.bottom + 6))
        tela.blit(img, pos)

        if not espada_atras:
            self._desenhar_espada(tela, agora, centro)

        if self.escudo > 0:
            c = centro + self.mira * 34
            tela.blit(self.escudo_img,
                      self.escudo_img.get_rect(center=(round(c.x), round(c.y))))

    def _desenhar_espada(self, tela, agora, centro):
        if self.atacando(agora):
            prog = (agora - self.ataque_inicio) / DURACAO_ATAQUE_MS
            ang = self.ataque_ang - ARCO_ATAQUE / 2 + prog * ARCO_ATAQUE
            for k, alfa in ((3, 50), (2, 100), (1, 170)):   # rastro do golpe
                self._espada_em(tela, centro, ang - k * 0.18, alfa)
            self._espada_em(tela, centro, ang, 255)
        else:
            self._espada_em(tela, centro, math.atan2(self.mira.y, self.mira.x), 255)

    def _espada_em(self, tela, centro, ang, alfa):
        img = pygame.transform.rotate(self.espada, -math.degrees(ang))
        if alfa < 255:
            img = img.copy()
            img.set_alpha(alfa)
        dist = 16 + self.espada.get_width() / 2
        c = centro + pygame.Vector2(math.cos(ang), math.sin(ang)) * dist
        tela.blit(img, img.get_rect(center=(round(c.x), round(c.y))))

    def _desenhar_velocidade(self, tela, agora):
        restante = self.bota_ate - agora
        if restante < 1500 and (agora // 120) % 2 == 0:
            return  # pisca no final para avisar que está acabando
        w = 46 + int(4 * math.sin(agora / 90))
        s = pygame.Surface((w, 16), pygame.SRCALPHA)
        pygame.draw.ellipse(s, (60, 220, 220, 90), (0, 0, w, 16))
        pygame.draw.ellipse(s, (170, 255, 255, 200), (0, 0, w, 16), 2)
        tela.blit(s, s.get_rect(center=(self.rect.centerx, self.rect.bottom + 4)))

    def _desenhar_aura(self, tela, agora, centro):
        restante = self.invencivel_ate - agora
        if restante < 2000 and (agora // 120) % 2 == 0:
            return  # pisca no final para avisar que está acabando
        r = 44 + int(4 * math.sin(agora / 120))
        s = pygame.Surface((r * 2, r * 2), pygame.SRCALPHA)
        pygame.draw.circle(s, (255, 220, 60, 90), (r, r), r)
        pygame.draw.circle(s, (255, 245, 160, 200), (r, r), r, 3)
        tela.blit(s, (round(centro.x - r), round(centro.y - r)))
