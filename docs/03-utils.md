# Módulo utils.py

### Propósito
Centraliza todas as funções de utilitário compartilhadas entre os outros módulos:
- Execução padronizada de comandos FFmpeg
- Extração de informações de vídeos
- Conversão de formatos de cor
- Conversão de timestamps

### Funções Principais

#### `run_ffmpeg(cmd, timeout=None, dry_run=False)`

**Descrição**: Executa comando FFmpeg com logging automático, timing e tratamento de erros.

**Parâmetros**:
- `cmd` (list): Comando como lista Python (ex: `["ffmpeg", "-i", "input.mp4", ...]`)
- `timeout` (int): Timeout em segundos. `None` = sem limite (padrão: None)
- `dry_run` (bool): Se True, apenas mostra comando sem executar (padrão: False)

**Comportamento**:
1. Se `dry_run=True`: Mostra o comando e retorna a lista sem executar
2. Se `dry_run=False`: Executa com captura de output, timing e logging automático
3. Loga comando completo em DEBUG
4. Loga resultado e tempo de execução em INFO

**Retorna**: `list` - O comando FFmpeg executado

**Exemplo**:
```python
cmd = ["ffmpeg", "-i", "input.mp4", "-vf", "scale=1920x1080", "-c:a", "copy", "output.mp4"]
result = run_ffmpeg(cmd)
# Output: ✓ FFmpeg completed in 45.23s

# Com timeout
result = run_ffmpeg(cmd, timeout=60)

# Dry-run
result = run_ffmpeg(cmd, dry_run=True)
# Output: Dry-run. No output created.
#         $ ffmpeg -i input.mp4 -vf scale=1920x1080 -c:a copy output.mp4
```

---

#### `get_video_info(video_path)`

**Descrição**: Extrai todas as informações técnicas de um arquivo de vídeo sem usar FFmpeg.

**Retorna**: Dicionário com: `width`, `height`, `fps`, `duration`, `frame_count`, `fourcc`, `codec_name`

**Exemplo**:
```python
info = get_video_info("video.mp4")
print(info)
# {
#   'width': 1920,
#   'height': 1080,
#   'fps': 30.0,
#   'duration': 120.5,
#   'frame_count': 3615,
#   'fourcc': 875967080,
#   'codec_name': 'H264'
# }
```

---

#### `hex_to_rgb(hex_color)`

**Descrição**: Converte cor HEX em tupla RGB.

**Exemplo**:
```python
hex_to_rgb("#FF0000")  # (255, 0, 0) - vermelho
```

---

#### `hex_to_ass(hex_color)`

**Descrição**: Converta HEX para formato ASS do FFmpeg (Advanced SubStation Alpha).

**Exemplo**:
```python
hex_to_ass("#FFFFFF")  # "&H00FFFFFF&" - branco opaco
```

---

#### `split_text_by_char_limit(text, char_limit=22)`

**Descrição**: Divide texto em duas linhas respeitando um limite de caracteres.

**Parâmetros**:
- `text` (str): Texto a dividir
- `char_limit` (int): Limite de caracteres na primeira linha (padrão: 22)

**Retorna**: `tuple` - `(primeira_linha, segunda_linha)`

**Exemplo**:
```python
split_text_by_char_limit("Texto bem comprido para análise", char_limit=15)
# ("Texto bem", "comprido para análise")
```
