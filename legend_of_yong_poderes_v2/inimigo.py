import os
import random
import pygame
from settings import *


_cache = {}


def _sprite(nome):
    if nome not in _cache:
        caminho = os.path.join(os.path.dirname(__file__),
                               "sprites", "inimigo", nome + ".png")
        img = pygame.image.load(caminho).convert_alpha()
        _cache[nome] = pygame.transform.scale(img, (TAM_INIMIGO, TAM_INIMIGO))
    return _cache[nome]


class Inimigo:
    def __init__(self, x, y):
        self.rect = pygame.Rect(x, y, TAM_INIMIGO, TAM_INIMIGO)
        self.pos = pygame.Vector2(self.rect.topleft)
        self.vida = VIDA_INIMIGO
        self.direcao = pygame.Vector2(0, 0)
        self.proxima_mudanca = 0
        self.invulneravel_ate = 0
        self.congelado_ate = 0
        self.empurrao = pygame.Vector2(0, 0)
        self.perseguindo = False

    @property
    def morto(self):
        return self.vida <= 0

    def congelado(self, agora):
        return agora < self.congelado_ate

    def atualizar(self, alvo_centro, limites, agora):
        ate_alvo = pygame.Vector2(alvo_centro) - pygame.Vector2(self.rect.center)
        distancia = ate_alvo.length()

        if self.congelado(agora):
            # congelado: fica parado (só o empurrão de um golpe ainda o move)
            self.perseguindo = False
            vel = 0
        elif 0 < distancia <= RAIO_PERSEGUICAO:
            # perseguição
            self.perseguindo = True
            vel = VEL_PERSEGUICAO
            self.direcao = ate_alvo.normalize()
        else:
            # patrulha: troca de direção de tempos em tempos
            self.perseguindo = False
            vel = VEL_PATRULHA
            if agora >= self.proxima_mudanca:
                self.direcao = random.choice([
                    pygame.Vector2(1, 0), pygame.Vector2(-1, 0),
                    pygame.Vector2(0, 1), pygame.Vector2(0, -1),
                    pygame.Vector2(0, 0),
                ])
                self.proxima_mudanca = agora + random.randint(800, 2000)

        self.pos += self.direcao * vel

        # empurrão ao levar dano, que vai diminuindo
        self.pos += self.empurrao
        self.empurrao *= 0.8
        if self.empurrao.length() < 0.5:
            self.empurrao.update(0, 0)

        self.rect.topleft = (round(self.pos.x), round(self.pos.y))
        antes = self.rect.copy()
        self.rect.clamp_ip(limites)
        if self.rect != antes:  # bateu na borda: volta pelo outro lado
            self.direcao *= -1
        self.pos.update(self.rect.topleft)

    def receber_dano(self, dano, origem, agora):
        if agora < self.invulneravel_ate:
            return
        self.vida -= dano
        self.invulneravel_ate = agora + 300
        fuga = pygame.Vector2(self.rect.center) - pygame.Vector2(origem)
        if fuga.length_squared() > 0:
            self.empurrao = fuga.normalize() * 12

    def desenhar(self, tela, agora):
        img = _sprite("perseguicao" if self.perseguindo else "patrulha")
        if self.congelado(agora):
            # tom azul de gelo (pisca no final para avisar que vai descongelar)
            img = img.copy()
            if self.congelado_ate - agora > 1000 or (agora // 120) % 2 == 0:
                img.fill((50, 120, 200, 0), special_flags=pygame.BLEND_RGB_ADD)
        if agora < self.invulneravel_ate:
            # pisca em branco ao levar dano
            img = img.copy()
            img.fill((255, 255, 255, 0), special_flags=pygame.BLEND_RGB_ADD)
        tela.blit(img, self.rect)
        if self.congelado(agora):
            pygame.draw.rect(tela, (200, 240, 255), self.rect.inflate(4, 4), 2)
        # barra de vida
        barra = pygame.Rect(self.rect.x, self.rect.y - 8, self.rect.width, 5)
        pygame.draw.rect(tela, CINZA, barra)
        cheia = barra.copy()
        cheia.width = int(barra.width * max(self.vida, 0) / VIDA_INIMIGO)
        pygame.draw.rect(tela, VERMELHO, cheia)
