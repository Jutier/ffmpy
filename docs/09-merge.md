# Módulo merge.py

### Propósito
Combina múltiplos comandos FFmpeg em um único comando otimizado, evitando recodificação múltipla do vídeo ao aplicar múltiplos filtros drawable ou overlay.

---

### Funções Principais

#### `merge_write(cmds, video_path=None, output_dir="text_output", dry_run=False)`

**Descrição**: Mescla múltiplos comandos `add_text()` em um único comando FFmpeg. Extrai todos os filtros drawtext e os combina em uma única passada, economizando tempo e qualidade.

**Parâmetros**:
- `cmds` (list): Lista de comandos FFmpeg (cada um é uma lista como retornado por `add_text()` com `dry_run=True`)
- `video_path` (str): Caminho do vídeo de entrada original. Se None, extrai do primeiro comando (padrão: None)
- `output_dir` (str): Diretório de saída (padrão: "text_output")
- `dry_run` (bool): Se True, retorna comando sem executar (padrão: False)

**Retorna**: Tupla (output_path, cmd_list)

**Processo Interno**:
1. Extrai todos os filtros `-vf "drawtext=..."` dos comandos
2. Combina em um único filtro separado por vírgulas
3. Cria comando unificado que processa tudo em uma passada
4. Evita recodificação múltipla do vídeo

**Arquivo de Saída**: `{nome_video}_write.mp4`

**Comando FFmpeg Gerado (exemplo)**:
```
ffmpeg -y -i video.mp4 \
  -vf "drawtext=text='Linha1':x=100:y=100:...,drawtext=text='Linha2':x=100:y=200:..." \
  -c:a copy output.mp4
```

**Exemplo de Uso**:
```python
from write import add_text
from merge import merge_write

# Preparar múltiplos textos (com dry_run=True para pegar comandos)
cmd1, _ = add_text("video.mp4", "Título", x="(w-text_w)/2", y="100", dry_run=True)
cmd2, _ = add_text("video.mp4", "Subtítulo", x="(w-text_w)/2", y="200", font_size=40, dry_run=True)
cmd3, _ = add_text("video.mp4", "Crédito", x="(w-text_w)/2", y="(h-100)", dry_run=True)

# Mesclar em uma passada
output_path, cmd = merge_write([cmd1, cmd2, cmd3], output_dir="resultados")

# Executar comando unificado
run_ffmpeg(cmd)
```

**Performance**:
- Sem merge: 3 vídeos processados = 3x o tempo do vídeo
- Com merge: Todos processados em 1x o tempo do vídeo
- **Economia: ~66% do tempo de processamento**

---

#### `merge_mark(cmds, video_path=None, output_dir="mark_output", dry_run=False)`

**Descrição**: Mescla múltiplos comandos `add_mark()` em um único comando FFmpeg. Extrai todas as imagens e os filtros overlay, combinando-os eficientemente.

**Parâmetros**:
- `cmds` (list): Lista de comandos add_mark (cada um é uma lista como retornado por `add_mark()` com `dry_run=True`)
- `video_path` (str): Caminho do vídeo de entrada original. Se None, extrai do primeiro comando (padrão: None)  
- `output_dir` (str): Diretório de saída (padrão: "mark_output")
- `dry_run` (bool): Se True, retorna comando sem executar (padrão: False)

**Retorna**: Tupla (output_path, cmd_list)

**Processo Interno**:
1. Extrai todas as imagens (`-i marca1.png -i marca2.png ...`)
2. Extrai todos os filtros overlay (`overlay=...`)
3. Cria cadeia de filtros interligada com labels
4. Cria comando unificado com múltiplas imagens de entrada

**Arquivo de Saída**: `{nome_video}_marked.mp4`

**Comando FFmpeg Gerado (exemplo)**:
```
ffmpeg -y -i video.mp4 -i logo1.png -i logo2.png \
  -filter_complex "[0:v][1:v]overlay=10:10[v1];[v1][2:v]overlay=END-w-10:END-h-10[v]" \
  -map "[v]" -map "0:a" -c:a copy output.mp4
```

**Exemplo de Uso**:
```python
from overlay import add_mark
from merge import merge_mark

# Preparar múltiplas marcas (com dry_run=True)
cmd1, _ = add_mark("video.mp4", "logo_insta.png", ref_x="start", ref_y="start", dry_run=True)
cmd2, _ = add_mark("video.mp4", "logo_if.png", ref_x="end", ref_y="end", dry_run=True)

# Mesclar em uma passada
output_path, cmd = merge_mark([cmd1, cmd2], output_dir="resultados")

# Executar comando unificado
run_ffmpeg(cmd)
```

**Performance**:
- Sem merge: 2 overlays = 2x o tempo do vídeo
- Com merge: Ambos em 1x o tempo do vídeo
- **Economia: ~50% do tempo de processamento**

---

### Pipeline Completo com Merge

```python
from default import execute_pipeline

# execute_pipeline() usa merge_write() e merge_mark() internamente
# para otimizar processamento de múltiplos textos e marcas

result = execute_pipeline(
    video="entrada.mp4",
    start_time="0:05",
    end_time="1:30",
    text1="Texto 1ª linha",
    text2="Texto 2ª linha",
    # Internamente:
    # 1. Trim + enhance audio (2 etapas)
    # 2. Crop automático (1 etapa)
    # 3. Transcrição (2 etapas: JSON + SRT)
    # 4. Burn subtitles (1 etapa)
    # 5. Merge marks (Instagram + IF em 1 etapa)
    # 6. Merge writes (Texto 1ª + 2ª + créditos em 1 etapa)
    # Total: ~9 etapas ao invés de 12
)
```
