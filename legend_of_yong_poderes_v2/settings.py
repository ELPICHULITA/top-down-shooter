# Configurações gerais do jogo

LARGURA = 900
ALTURA = 600
FPS = 60
TITULO = "The Legend of Yong"

# Cores
PRETO = (0, 0, 0)
VERDE = (50, 180, 70)
BRANCO = (255, 255, 255)
VERMELHO = (200, 40, 40)
LARANJA = (230, 120, 30)
AMARELO = (255, 220, 60)
CINZA = (60, 60, 60)

# Jogador
TAM_JOGADOR = 50
ESCALA_JOGADOR = 2  # os sprites do Link são pequenos (28x36)
VEL_JOGADOR = 5
VIDA_JOGADOR = 5
INVULNERAVEL_JOGADOR_MS = 1000

# Ataque de espada (golpe em arco na direção do mouse)
ALCANCE_ATAQUE = 70          # distância do golpe, em pixels
ARCO_ATAQUE = 2.1            # abertura do golpe em radianos (~120 graus)
DURACAO_ATAQUE_MS = 220
RECARGA_ATAQUE_MS = 350
DANO_ATAQUE = 1
ESCALA_ESPADA = 2

# Power-ups
CHANCE_DROP = 0.45           # chance de um inimigo derrotado soltar item
INTERVALO_ITEM_MS = 7000     # a cada quanto tempo nasce um item no chão
MAX_ITENS_NO_CHAO = 3
VIDA_ITEM_MS = 12000         # tempo até o item sumir do chão
AREA_ITENS = (120, 115, 660, 365)   # x, y, largura, altura (chão laranja)
DURACAO_TRIANGULO_MS = 8000  # imunidade total
ESCUDO_MAX = 3               # golpes que o escudo aguenta
MAX_MUNICAO = 9
BUMERANGUES_POR_ITEM = 5
VEL_BUMERANGUE = 9
ALCANCE_BUMERANGUE = 300
DANO_BUMERANGUE = 1
BOMBAS_POR_ITEM = 3
ALCANCE_BOMBA = 260          # até onde a bomba pode ser jogada
PAVIO_BOMBA_MS = 1400
RAIO_BOMBA = 100
DANO_BOMBA = 3
DURACAO_EXPLOSAO_MS = 450
DURACAO_GELO_MS = 4000       # inimigos congelados (não andam nem machucam)
DURACAO_BOTA_MS = 5000       # velocidade aumentada
MULT_BOTA = 1.7
CURA_QTD = 2                 # corações recuperados pela poção

# Inimigos
QTD_INIMIGOS = 6
TAM_INIMIGO = 40
VIDA_INIMIGO = 3
VEL_PATRULHA = 1.5
VEL_PERSEGUICAO = 2.5
RAIO_PERSEGUICAO = 200
