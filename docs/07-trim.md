# Módulo trim.py

### Propósito
Recorta (trimma) vídeos em intervalos de tempo específicos usando seek rápido no FFmpeg.

---

### Funções Principais

#### `trim_video(video_path, start_time, end_time, output_dir="trim_output", dry_run=False)`

**Descrição**: Recorta (trimma) vídeo de um timestamp inicial até um final usando FFmpeg.

**Parâmetros**:
- `video_path` (str): Caminho do arquivo de vídeo de entrada
- `start_time` (str): Tempo inicial (formato MM:SS, MM:SS.ms ou HH:MM:SS)
- `end_time` (str): Tempo final (formato MM:SS, MM:SS.ms ou HH:MM:SS)
- `output_dir` (str): Diretório de saída (padrão: "trim_output")
- `dry_run` (bool): Se True, retorna comando sem executar (padrão: False)

**Retorna**: Tupla (output_file, cmd_list) - Caminho de saída e comando FFmpeg como lista

**Formato de Timestamp Aceito**:
```
MM:SS        → "01:30" = 1 minuto e 30 segundos
MM:SS.ms     → "01:30.500" = 1 minuto, 30 segundos e 500ms
HH:MM:SS     → "00:01:30" = 1 minuto e 30 segundos
```

**Comando FFmpeg Utilizado**:
```
ffmpeg -i input.mp4 -ss <start_time> -to <end_time> -c copy -y output.mp4
```

**Comportamento**:
1. Usa `-ss` (seek) antes de `-i` para início rápido (instant seek)
2. Usa `-to` para definir tempo final
3. `-c copy` = cópia sem reencoding (preserva qualidade 100%)
4. Arquivo de saída é nomeado automaticamente: `{nome}_trim.mp4`

**Exemplos**:
```python
# Recorta de 1:30 a 5:45
trim_video("video.mp4", "01:30", "05:45")

# Recorta de 10s a 2 minutos com ms
trim_video("video.mp4", "00:10.000", "02:00.000")

# Recorta de 0:05:30 a 0:10:45 (HH:MM:SS)
trim_video("video.mp4", "00:05:30", "00:10:45", output_dir="meus_trims")

# Dry-run (apenas mostra comando)
trim_video("video.mp4", "01:00", "02:00", dry_run=True)
```

**Tempo de Execução**: <1 segundo (sem reencoding, apenas cópia)

**Estrutura de Saída**:
```
output_dir/
└── video_trim.mp4     # Vídeo recortado
```

---

### Notas Técnicas

#### Precisão de Corte
- Seek FFmpeg não é exato ao frame (pode variar ±200ms em videos com keyframes espaçados)
- Para precisão de frame, use `filter_complex` com trim filter (mais lento, reencoding)

#### Compatibilidade
- Funciona com qualquer codec (H.264, VP9, ProRes, etc)
- Áudio é copiado sem modificação

#### Performance
- Muito rápido porque não reencoda: O(1)
- Seek é instantâneo, apenas corta metadados e streams

---

### Limitações

- Não suporta múltiplos intervalos (um trim por execução)
- Para vários cortes: Executar várias vezes
