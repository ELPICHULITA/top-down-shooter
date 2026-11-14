import math
import os
import random
import pygame
from settings import *

TIPOS = ("triangulo", "bumerangue", "bomba", "escudo", "gelo", "cura", "bota")

_img = {}
_pequenos = {}


def _carregar(nome):
    caminho = os.path.join(os.path.dirname(__file__), "sprites", "itens", nome + ".png")
    return pygame.image.load(caminho).convert_alpha()


def _escalar(img, largura, suave):
    altura = max(1, round(img.get_height() * largura / img.get_width()))
    if suave:
        return pygame.transform.smoothscale(img, (largura, altura))
    return pygame.transform.scale(img, (largura, altura))


def sprites():
    """Carrega os sprites dos power-ups (precisa do display já criado)."""
    if not _img:
        _img["triangulo"] = _escalar(_carregar("triangulo"), 34, False)
        _img["bumerangue"] = _escalar(_carregar("bumerangue"), 38, True)
        _img["escudo"] = _escalar(_carregar("escudo"), 30, False)
        _img["gelo"] = _escalar(_carregar("gelo"), 30, False)
        _img["cura"] = _escalar(_carregar("cura"), 26, False)
        _img["bota"] = _escalar(_carregar("bota"), 36, False)
        _img["bomba"] = [_escalar(_carregar(f"bomba_{i}"), 34, True)
                         for i in range(8)]
    return _img


def icone(tipo):
    s = sprites()
    return s["bomba"][0] if tipo == "bomba" else s[tipo]


def icone_hud(tipo, lado=26):
    if tipo not in _pequenos:
        img = icone(tipo)
        k = lado / max(img.get_width(), img.get_height())
        _pequenos[tipo] = pygame.transform.smoothscale(
            img, (max(1, round(img.get_width() * k)),
                  max(1, round(img.get_height() * k))))
    return _pequenos[tipo]


class Pickup:
    """Item no chão que o jogador pega encostando."""

    def __init__(self, tipo, centro, agora):
        self.tipo = tipo
        self.centro = pygame.Vector2(centro)
        self.nasceu = agora
        img = icone(tipo)
        self.rect = pygame.Rect(0, 0, img.get_width() + 12, img.get_height() + 12)
        self.rect.center = (round(self.centro.x), round(self.centro.y))

    def expirou(self, agora):
        return agora - self.nasceu >= VIDA_ITEM_MS

    def desenhar(self, tela, agora):
        restante = VIDA_ITEM_MS - (agora - self.nasceu)
        if restante < 3000 and (agora // 150) % 2 == 0:
            return  # pisca antes de sumir
        img = icone(self.tipo)
        balanco = math.sin((agora - self.nasceu) / 250) * 4
        cx, cy = round(self.centro.x), round(self.centro.y)
        pygame.draw.ellipse(tela, (150, 70, 20), (cx - 13, cy + 16, 26, 8))
        tela.blit(img, img.get_rect(center=(cx, round(cy + balanco))))


class Bumerangue:
    """Vai na direção da mira, volta até o jogador e machuca na ida e na volta."""

    def __init__(self, origem, direcao):
        self.pos = pygame.Vector2(origem)
        self.direcao = pygame.Vector2(direcao)
        self.percorrido = 0
        self.voltando = False
        self.acertados = set()
        self.angulo = 0
        self.fim = False
        self.rect = pygame.Rect(0, 0, 34, 34)
        self.rect.center = (round(self.pos.x), round(self.pos.y))

    def atualizar(self, alvo, limites):
        self.angulo = (self.angulo + 28) % 360
        if not self.voltando:
            self.pos += self.direcao * VEL_BUMERANGUE
            self.percorrido += VEL_BUMERANGUE
            if self.percorrido >= ALCANCE_BUMERANGUE \
                    or not limites.collidepoint(round(self.pos.x), round(self.pos.y)):
                self.voltando = True
                self.acertados.clear()   # pode acertar de novo na volta
        else:
            v = pygame.Vector2(alvo) - self.pos
            if v.length() <= 24:
                self.fim = True
            else:
                self.pos += v.normalize() * (VEL_BUMERANGUE + 3)
        self.rect.center = (round(self.pos.x), round(self.pos.y))

    def desenhar(self, tela, agora):
        img = pygame.transform.rotate(sprites()["bumerangue"], self.angulo)
        tela.blit(img, img.get_rect(center=(round(self.pos.x), round(self.pos.y))))


class Bomba:
    """Voa até o ponto da mira, pisca e explode depois do pavio."""

    def __init__(self, origem, alvo, agora):
        self.pos = pygame.Vector2(origem)
        self.alvo = pygame.Vector2(alvo)
        self.detona_em = agora + PAVIO_BOMBA_MS
        self.explodiu = False

    def atualizar(self, agora):
        v = self.alvo - self.pos
        if v.length() > 8:
            self.pos += v.normalize() * 8
        else:
            self.pos.update(self.alvo.x, self.alvo.y)
        if agora >= self.detona_em:
            self.explodiu = True

    def desenhar(self, tela, agora):
        img = sprites()["bomba"][(agora // 80) % 8]
        if self.detona_em - agora < 500 and (agora // 100) % 2 == 0:
            img = img.copy()
            img.fill((90, 90, 90, 0), special_flags=pygame.BLEND_RGB_ADD)
        x, y = round(self.pos.x), round(self.pos.y)
        pygame.draw.ellipse(tela, (150, 70, 20), (x - 14, y + 12, 28, 9))
        tela.blit(img, img.get_rect(center=(x, y)))


class Explosao:
    def __init__(self, centro, agora):
        self.centro = pygame.Vector2(centro)
        self.inicio = agora

    def ativa(self, agora):
        return agora - self.inicio < DURACAO_EXPLOSAO_MS

    def desenhar(self, tela, agora):
        t = min(1.0, (agora - self.inicio) / DURACAO_EXPLOSAO_MS)
        R = RAIO_BOMBA
        r = max(2, int(R * (0.4 + 0.6 * min(1.0, t * 2))))
        alfa = max(0, int(200 * (1 - t)))
        s = pygame.Surface((R * 2, R * 2), pygame.SRCALPHA)
        pygame.draw.circle(s, (255, 140, 30, alfa), (R, R), r)
        pygame.draw.circle(s, (255, 230, 120, alfa), (R, R), max(1, int(r * 0.6)))
        pygame.draw.circle(s, (255, 255, 255, alfa), (R, R), r, 4)
        tela.blit(s, (round(self.centro.x - R), round(self.centro.y - R)))
