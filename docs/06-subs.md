# Módulo subs.py

### Propósito
Gerencia transcrição de áudio para texto, conversão entre formatos de legendas (JSON/SRT) e gravação de legendas em vídeo.

---

### Funções Principais

#### `transcribe_to_json(video_path, output_dir="json_transcription", model_name="small", language=None, word_timestamps=True, device="cpu", verbose=False, dry_run=False)`

**Descrição**: Transcreve áudio de vídeo para texto usando Whisper da OpenAI, salvando timestamps detalhados em JSON.

**Parâmetros**:
- `video_path` (str): Caminho do arquivo de vídeo
- `output_dir` (str): Diretório de saída para JSON (padrão: "json_transcription")
- `model_name` (str): Modelo Whisper - "tiny", "base", "small", "medium", "large", "turbo" (padrão: "small")
- `language` (str): Idioma - "pt", "en", etc. Se None, auto-detecta (padrão: None)
- `word_timestamps` (bool): Se True, inclui timestamps por palavra (padrão: True)
- `device` (str): "cuda" para GPU ou "cpu" para processador (padrão: "cpu")
- `verbose` (bool): Se True, printa os segmentos transcritos (padrão: False)
- `dry_run` (bool): Se True, retorna path esperado sem executar (padrão: False)

**Formato do JSON Gerado**:
```json
{
  "text": "Texto completo transcrito...",
  "segments": [
    {
      "id": 0,
      "seek": 0,
      "start": 0.0,
      "end": 3.5,
      "text": "Primeira frase...",
      "tokens": [...],
      "temperature": 0.0,
      "avg_logprob": -0.25,
      "compression_ratio": 1.3,
      "no_speech_prob": 0.001,
      "words": [
        {"word": "Primeira", "start": 0.0, "end": 0.5},
        {"word": "frase", "start": 0.5, "end": 1.0}
      ]
    },
    ...
  ],
  "language": "pt"
}
```

**Exemplo**:
```python
# Transcrição com modelo pequeno em CPU
transcribe_to_json("video.mp4")

# Transcrição com modelo grande em GPU
transcribe_to_json("video.mp4", model_name="large", device="cuda", language="pt")
```

**Tempo de Execução**: ~2-3x o tempo do áudio em CPU (ex: 10min de áudio = 20-30min). Com GPU (CUDA): ~1-2x

---

#### `json_to_srt(json_path, output_dir="srt_transcription", max_char=25, dry_run=False)`

**Descrição**: Converte transcrição JSON do Whisper para formato SRT (SubRip), agrupando palavras pelo limite de caracteres.

**Parâmetros**:
- `json_path` (str): Caminho do JSON da transcrição (gerado por `transcribe_to_json`)
- `output_dir` (str): Diretório de saída para o arquivo .srt (padrão: "srt_transcription")
- `max_char` (int): Número máximo de caracteres por legenda (padrão: 25)
- `dry_run` (bool): Se True, retorna path sem gerar arquivo (padrão: False)

**Formato SRT de Saída**:
```
1
00:00:00,000 --> 00:00:03,500
Primeira frase transcrita...

2
00:00:03,500 --> 00:00:07,200
Segunda frase...
```

**Comportamento**:
1. Lê JSON gerado pelo Whisper (com word_timestamps)
2. Agrupa palavras respeitando `max_char` caracteres por linha
3. Respeita limites em pontuação (.!?) e vírgulas
4. Converte tempo de segundos para formato HH:MM:SS,ms
5. Escreve no formato SRT padrão

**Exemplo**:
```python
# Gera SRT com máximo 30 caracteres por linha
json_to_srt("transcription.json", output_dir="legendas", max_char=30)

# Resultado: /legendas/transcription.srt
```

**Nota**: Requer que o JSON tenha sido gerado com `word_timestamps=True` para funcionamento correto

---

#### `burn_subtitles_ffmpeg(video_path, srt_path, output_dir="burn_video", font="Calibri", font_dir=None, font_size=20, primary_colour="#eee0c9", outline_colour="#0f1f24", outline=2, margin_v=65, margin_l=10, margin_r=10, dry_run=False)`

**Descrição**: Grava (hardcodes) legendas no vídeo usando o filtro `subtitles` do FFmpeg com libass.

**Parâmetros**:
- `video_path` (str): Caminho do vídeo de entrada
- `srt_path` (str): Caminho do arquivo .srt com legendas
- `output_dir` (str): Diretório de saída (padrão: "burn_video")  
- `font` (str): Nome da fonte no sistema (padrão: "Calibri")
- `font_dir` (str): Diretório com arquivos .ttf customizados (padrão: None = fonts do sistema)
- `font_size` (int): Tamanho da fonte em pixels (padrão: 20)
- `primary_colour` (str): Cor do texto em hex RGBA (padrão: "#eee0c9" = bege claro)
- `outline_colour` (str): Cor do contorno em hex RGBA (padrão: "#0f1f24" = azul escuro)
- `outline` (int): Espessura do contorno em pixels (padrão: 2)
- `margin_v` (int): Margem vertical em pixels (padrão: 65)
- `margin_l` (int): Margem esquerda em pixels (padrão: 10)
- `margin_r` (int): Margem direita em pixels (padrão: 10)
- `dry_run` (bool): Se True, retorna comando sem executar (padrão: False)

**Retorna**: Tupla (output_path, cmd_list)

**Comando FFmpeg Utilizado**:
```
ffmpeg -i video.mp4 -vf subtitles=subtitles.srt:force_style='FontName=Calibri,\
FontSize=20,PrimaryColour=&H00eee0c9,OutlineColour=&H00000f1f24,\
Outline=2,MarginV=65,MarginL=10,MarginR=10' -c:a copy output.mp4
```

**Cores em Formato HEX**: 
- Usa padrão RGBA hex: #RRGGBBAA
- Convertidas para formato ASS (&HAABBGGRR&) automaticamente

**Exemplos**:
```python
# Burn com configuração padrão
burn_subtitles_ffmpeg("video.mp4", "legendas.srt")

# Burn customizado (maior, dourado com contorno preto)
burn_subtitles_ffmpeg(
    video_path="video.mp4",
    srt_path="legendas.srt",
    font_size=28,
    primary_colour="#FFD700FF",      # Dourado opaco
    outline_colour="#000000FF",       # Preto opaco
    outline=3
)

# Burn com fonte customizada
burn_subtitles_ffmpeg(
    video_path="video.mp4",
    srt_path="legendas.srt",
    font="Arial",
    font_dir="custom_fonts/",
    font_size=24
)
```

**Performance**: ~1-2x o tempo do vídeo (dependendo do tamanho e codec)
- HEX: `#FFFFFF` (convertido para formato ASS)

**Exemplo**:
```python
burn_subtitles_ffmpeg("video.mp4", "subs.srt", "video_with_subs.mp4", 
                      font_size=32, font_color="#FFFF00")
```

**Retorna**: `list` - Comando FFmpeg executado

**Tempo de Execução**: ~1x o tempo do vídeo em CPU (realtime)

---

### Fluxo Típico de Legendagem

```python
from subs import transcribe_to_json, json_to_srt, burn_subtitles_ffmpeg

# Passo 1: Transcrever áudio
transcribe_to_json("audio.mp3", "transcription.json")

# Passo 2: Converter para SRT
json_to_srt("transcription.json", "subtitles.srt")

# Passo 4: Editar SRT
# Abra o .srt gerado em qualquer editor de texto,
# você pode fazer as correções que desejar.

# Passo 4: Gravar legendas no vídeo
burn_subtitles_ffmpeg("video.mp4", "subtitles.srt", "video_with_subs.mp4")
```

---

### Limitações e Notas

- **Whisper**: Requer conexão com OpenAI API (ou modelo local)
- **SRT**: Suporta apenas texto simples (sem formatação)
- **FFmpeg**: Legendas são permanentes (hardcoded) no vídeo final
- **Idiomas**: Whisper detecta automaticamente o idioma
