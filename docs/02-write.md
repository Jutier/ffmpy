# Módulo write.py

### Propósito
Escreve texto dinamicamente em vídeos usando FFmpeg drawtext filter. Suporta:
- Posicionamento via expressões FFmpeg (pixels ou variáveis)
- Customização de fonte (tamanho, cor, família)
- Fonte system ou custom directories
- Timing com formato MM:SS

### Função Principal

#### `add_text(video_path, text, x="(w-text_w)/2", y="(h-text_h)/2", ...)`

**Descrição**: Escreve texto em vídeo com posicionamento por expressões FFmpeg.

**Parâmetros obrigatórios**:
- `video_path` (str): Arquivo de vídeo
- `text` (str): Texto a escrever

**Parâmetros opcionais**:
- `x` (str): Posição horizontal (padrão: "(w-text_w)/2" = centralizado)
  - Valores: inteiros ("100"), expressões ("w-50", "(w-text_w)/2")
  - Variáveis FFmpeg: `w` (largura), `text_w` (largura do texto)
- `y` (str): Posição vertical (padrão: "(h-text_h)/2" = centralizado)
  - Valores: inteiros ("100"), expressões ("h-50", "(h-text_h)/2")
  - Variáveis FFmpeg: `h` (altura), `text_h` (altura do texto)
- `font_size` (int): Tamanho da fonte em pixels (padrão: 30)
- `font_color` (str): Cor ("white", "red", "#FF00FF", etc)
- `font` (str): Nome da fonte ("Arial", "Roboto", etc)
- `font_dir` (str): Diretório com fontes TTF customizadas
- `text_align` (str): Alinhamento do texto (padrão: "center")
  - Opções: "left", "center", "right"
- `start_time` (float): Tempo de início em segundos (opcional)
- `end_time` (float): Tempo de fim em segundos (opcional)
- `output_dir` (str): Diretório de saída

**Retorna**: Tupla (output_path, cmd_list)

### Posicionamento com Expressões FFmpeg

Os parâmetros `x` e `y` aceitam expressões FFmpeg para máxima flexibilidade:

```python
# Variáveis disponíveis:
# w, h = largura/altura do vídeo
# text_w, text_h = largura/altura do texto renderizado
# W, H = aliases para w, h
```

**Exemplos de expressões**:
| Expressão | Resultado |
|-----------|----------|
| `"100"` | 100 pixels fixo |
| `"(w-text_w)/2"` | Centralizado horizontalmente |
| `"(h-text_h)/2"` | Centralizado verticalmente |
| `"w-100"` | 100 pixels da direita |
| `"h-50"` | 50 pixels do bottom |
| `"(w-text_w)/2 + 50"` | Centralizado + 50px |

### Controle de Timing

Os parâmetros `start_time` e `end_time` usam formato MM:SS ou HH:MM:SS:

```python
start_time="0:05"        # 5 segundos
start_time="01:30.500"   # 1min 30s + 500ms
start_time="0:01:30"     # 1 minuto 30 segundos
```

### Implementação do FFmpeg

#### Filtro drawtext
O FFmpeg `drawtext` renderiza texto diretamente no vídeo:

```bash
ffmpeg -i video.mp4 \
  -vf "drawtext=text='Hello':x=(w-text_w)/2:y=(h-text_h)/2:fontsize=30:fontcolor=white" \
  output.mp4
```

**Parâmetros**:
| Parâmetro | Significado |
|-----------|-------------|
| `text` | Texto a escrever (escape caracteres especiais) |
| `x`, `y` | Posição em pixels |
| `fontsize` | Tamanho em pt |
| `fontcolor` | Cor em hex ou nome |
| `fontfile` | Caminho para arquivo .ttf customizado |
| `fontconfig` | 1 = usar fonts system; 0 = fontfile |
| `enable` | Expressão condicional (timing) |

#### Controle de Timing
O parâmetro `enable` controla quando o texto aparece:

```python
# Sem timing (sempre visível)
enable = "1"

# A partir de t segundos
enable = f"gte(t\\,{start_time})"

# Até t segundos
enable = f"lte(t\\,{end_time})"

# Entre start e end
enable = f"gte(t\\,{start_time})*lte(t\\,{end_time})"
```

#### Suporte a Fontes

**Sistema (fontconfig=1)**:
```python
# Usa fontes installadas no sistema
drawtext=text='Hello':fontconfig=1:font='Arial'
```

**Custom (fontfile)**:
```python
# Usa arquivo .ttf específico
fontdir = "./fonts"
fontfile = f"{fontdir}/Roboto-Bold.ttf".replace("\\", "/")
drawtext=text='Hello':fontfile='{fontfile}'
```

### Exemplos

```bash
# Centralizado (padrão)
python main.py write video.mp4 "Hello" --font-size 40

# Canto superior esquerdo, alinhado à esquerda
python main.py write video.mp4 "Hello" --x "10" --y "10" --text-align left

# Centralizado horizontalmente, 50px do topo, alinhado à direita
python main.py write video.mp4 "Hello" --y "50" --text-align right

# Expressões complexas
python main.py write video.mp4 "Hello" --x "(w-text_w)/2 + 100" --y "h-100"

# Texto grande em vermelho, com timing
python main.py write video.mp4 "ATENÇÃO" --font-size 80 --font-color red \
  --start-time "0:05" --end-time "0:10"

# Texto com fonte customizada
python main.py write video.mp4 "Score" --font Roboto --font-dir ./fonts

# Medir tempo incluindo renderização
python main.py -t write video.mp4 "Processado"
```

### Fluxo Interno

```
Entrada: (video.mp4, "Hello")
    ↓
Converte expressões FFmpeg para strings
    ↓
Constrói parâmetros drawtext
    ↓
Cria comando FFmpeg
    ↓
Executa run_ffmpeg()
    ↓
Saída: ./text_output/video_written.mp4
```
