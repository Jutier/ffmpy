# Módulo default.py

**Entrypoint principal** para processamento de vídeo. Executa o **pipeline completo** (9 etapas lógicas) em um vídeo individual OU em lote (múltiplos vídeos de uma vez). Contém **padrões pré-definidos** como modelos de transcrição, configurações de texto, etc.

Pode ser usado via **CLI** (com flags) ou **importado em Python**.

---

### Funções

#### `execute_pipeline(video, start_time, end_time, text1, text2, from_step=1)`

Executa o pipeline completo de 9 etapas em um vídeo.

**Parâmetros obrigatórios**:
- `video` (str): Arquivo de vídeo
- `start_time` (str): Início do recorte (MM:SS ou HH:MM:SS)
- `end_time` (str): Fim do recorte
- `text1` (str): Texto no topo (dividido em duas linhas)
- `text2` (str): Texto na parte inferior

**Parâmetros opcionais**:
- `from_step` (int): Passo inicial (1-9). Passos < from_step usam dry_run (padrão: 1)

**Retorna**: Caminho do vídeo final ou None se houver erro

**As 9 Etapas Lógicas** (11 operações com merge):

| # | Etapa | Entrada | Saída | Operações |
|----|-------|---------|-------|-----------|
| 1 | Recorta tempo | video.mp4 | video_trimmed.mp4 | trim_video |
| 2 | Limpa áudio | video_trimmed.mp4 | video_enhanced.mp4 | enhance_audio |
| 3 | Detecta rosto | video_enhanced.mp4 | video_crop.mp4 | analyze_video |
| 4 | Transcreve | video_crop.mp4 | video.json | transcribe_to_json |
| 5 | JSON → SRT | video.json | video.srt | json_to_srt |
| 6 | Marca Instagram | video_crop.mp4 | (temp) | add_mark (merge) |
| 6b | Marca IF | (temp) | video_marked.mp4 | add_mark (merge) |
| 7 | Adiciona legendas | video_marked.mp4 + video.srt | video_burned.mp4 | burn_subtitles_ffmpeg |
| 8 | Créditos finais | video_burned.mp4 | video_outro.mp4 | add_outro |
| 9 | Texto 1 1a linha | video_outro.mp4 | (temp) | add_text (merge) |
| 9b | Texto 1 2a linha | (temp) | (temp) | add_text (merge) |
| 9c | Texto 2 | (temp) | final.mp4 | add_text (merge) |

**Como funciona**:
- Saída de uma etapa automaticamente vira entrada da próxima
- Etapas 6 (marks) e 9 (texts) usam `merge_*()` para otimizar (único comando FFmpeg)
- Mostra qual etapa falhou se der erro
- Todos parâmetros podem ser customizados via constantes globais no topo do arquivo

**Parametrização Global**:

Todos os parâmetros estão definidos como constantes no topo de `default.py`:

```python
# Transcrição
TRANSCRIPTION_MODEL = "large"
TRANSCRIPTION_LANGUAGE = "pt"
MAX_CHARS_PER_LINE = 25

# Marcas
INSTA_MARK_PATH = "../assets/insta-mark.png"
IF_MARK_PATH = "../assets/if-mark.png"
MARK_MARGIN_X = 30
MARK_MARGIN_Y = 30

# Texto 1 (topo)
TEXT1_CHAR_LIMIT = 22
TEXT1_FONT_COLOR = "#06d6a0"
TEXT1_FONT = "Oswald-Medium"
TEXT1_FONT_DIR = "fonts"
TEXT1_FONT_SIZE = 90

# Texto 2 (baixo)
TEXT2_FONT_COLOR = "#ef476f"
TEXT2_FONT = "Comfortaa-Medium"
TEXT2_FONT_DIR = "fonts"
TEXT2_FONT_SIZE = 70
```

**Divisão automática de text1**:
```python
text1 = "Texto um dois três quatro cinco"
char_limit = 22

Resultado:
  text1_top = "Texto um dois três"       (18 chars)
  text1_bottom = "quatro cinco"          (13 chars)
```

**Estrutura de Diretórios de Saída**:
```
output_video/                     # Base (nome do vídeo input)
├── videos/                       # Intermediários (etapas 1-8)
│   ├── video_trimmed.mp4
│   ├── video_enhanced.mp4
│   ├── video_crop.mp4
│   ├── video_marked.mp4
│   ├── video_burned.mp4
│   ├── video_outro.mp4
│   └── video_write.mp4
├── transcriptions/               # JSON e SRT (etapas 4-5)
│   ├── video.json
│   └── video.srt
└── final.mp4                     # Saída final (etapa 9c)
```

**Exemplo de Uso**:
```python
from default import execute_pipeline

result = execute_pipeline(
    video="entrada.mp4",
    start_time="0:05",
    end_time="1:30",
    text1="Bem-vindo aqui",
    text2="Inscreva-se"
)

if result:
    print(f"✅ Processado: {result}")
else:
    print("❌ Falha no processamento")
```

Processa múltiplos vídeos a partir de um arquivo de texto.

**Parâmetros**:
- `batch_file` (str): Caminho do arquivo de texto (ex: "batch.txt")

**Formato do Arquivo**:
```
# Comentários com #
# Formato: video|start_time|end_time|text1|text2

video1.mp4|0:05|1:30|Texto um|Legenda 1
video2.mp4|0:10|2:00|Texto dois|Legenda 2
# video3.mp4|0:15|2:45|Deshabilitado|Legenda 3

# Linhas vazias são ignoradas
```

**Regras de Parse**:
- Linhas começando com `#`: ignoradas (comentários)
- Linhas vazias: ignoradas
- Separador: `|` (pipe)
- Ordem fixa: `video|start|end|text1|text2`

**Retorna**: Lista de tuplas `[(video_path, output_path), ...]`
- `output_path` é o caminho final se sucesso
- `output_path` é None se falha

**Exemplo de Uso**:
---

#### `batch_process(input_arg, from_step=1, is_file=False)`

Processa vídeos em modo batch (múltiplos vídeos) ou linha única.

**Parâmetros**:
- `input_arg` (str): Linha única `video|start|end|text1|text2` OU caminho do arquivo `.txt`
- `from_step` (int): Passo inicial (1-9, padrão: 1)
- `is_file` (bool): Se True, trata input como arquivo; se False, como linha única (padrão: False)

**Retorna**: None (processa sequencialmente)

**Formato da Linha Única**:
```
video.mp4|00:05|01:30|Texto um|Legenda
```

**Formato do Arquivo Batch**:
```
# Comentários com #
video1.mp4|0:05|1:30|Texto 1|Legenda 1
video2.mp4|0:10|2:00|Texto 2|Legenda 2
# video3.mp4|deshabilitado|ignore|ignore|ignore

# Linhas vazias são ignoradas
```

**Regras de Parse**:
- Linhas começando com `#`: ignoradas (comentários)
- Linhas vazias: ignoradas
- Separador: `|` (pipe)
- Ordem fixa: `video|start|end|text1|text2`

**Exemplos de Uso Python**:
```python
from default import batch_process

# Linha única
batch_process("video.mp4|0:05|1:30|Bem-vindo|Inscreva-se")

# Arquivo batch
batch_process("batch.txt", is_file=True)

# Com passo inicial (arquivo)
batch_process("batch.txt", from_step=5, is_file=True)

# Com passo inicial (linha única)
batch_process("video.mp4|0:05|1:30|Bem-vindo|Inscreva-se", from_step=5)
```

**Exemplos de Uso CLI**:
```bash
# Linha única
python default.py "video.mp4|00:05|01:30|Texto um|Legenda"

# Arquivo batch
python default.py -f batch.txt

# Com passo inicial
python default.py -f batch.txt -s 5

# Linha única com passo inicial
python default.py "video.mp4|00:05|01:30|Texto um|Legenda" -s 3
```

### Funções Internas

#### `_parse_line(line)`
Parse de uma linha no formato pipe-separated: `video|start_time|end_time|text1|text2`.
