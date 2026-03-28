# Módulo audio.py

### Propósito
Melhora qualidade de áudio usando cadeia de 7 filtros especializados e gera visualização em espectrograma.

---

### Funções Principais

#### `enhance_audio(video_path, output_dir="audio_output", anlmdn_strength=5e-2, afftdn_nf=-70, afftdn_type="v", highpass_freq=250, lowpass_freq=4000, eq_bands=None, comp_threshold="-24dB", comp_ratio=1.5, comp_attack=15, comp_release=100, declick_threshold=40, audio_bitrate="192k", audio_codec="aac", overwrite=True, dry_run=False)`

**Descrição**: Aplica pipeline de filtros FFmpeg especializados para melhorar qualidade de áudio.

**Cadeia de Filtros Aplicada**:

| # | Filtro | Propósito | Padrão |
|---|--------|----------|--------|
| 1 | **anlmdn** | Denoise (Non-Local Means) | strength=0.05 |
| 2 | **afftdn** | Denoise (FFT-based) | nf=-70dB, type="v" (voice) |
| 3 | **highpass** | Remove baixa frequência | f=250Hz (remove rumble) |
| 4 | **lowpass** | Suaviza frequência alta | f=4000Hz (remove zumbido) |
| 5 | **equalizer** | Equalizador multi-banda | Padrão: [(400, 1, -5), (2500, 1, -3)] |
| 6 | **acompressor** | Compressor dinâmico | threshold=-24dB, ratio=1.5 |
| 7 | **adeclick** | Remove clicks/pops | threshold=40 |

**Parâmetros Principais**:
- `video_path` (str): Caminho do vídeo de entrada
- `output_dir` (str): Diretório de saída (padrão: "audio_output")
- `anlmdn_strength` (float): Força do denoise Non-Local Means (padrão: 0.05)
- `afftdn_nf` (int): Noise floor do afftdn em dB (-20 a -80) (padrão: -70)
- `afftdn_type` (str): Tipo de ruído - "v" (voice) ou "w" (white) (padrão: "v")
- `highpass_freq` (int): Frequência de corte high-pass em Hz (padrão: 250)
- `lowpass_freq` (int): Frequência de corte low-pass em Hz (padrão: 4000)
- `eq_bands` (list): Lista de tuplas (freq, width, gain) para equalizador (padrão: [(400, 1, -5), (2500, 1, -3)])
- `comp_threshold` (str): Threshold do compressor (padrão: "-24dB")
- `comp_ratio` (float): Ratio de compressão (padrão: 1.5)
- `comp_attack` (int): Attack em ms (padrão: 15)
- `comp_release` (int): Release em ms (padrão: 100)
- `declick_threshold` (int): Threshold do declick (1-100) (padrão: 40)
- `audio_bitrate` (str): Bitrate de saída (padrão: "192k")
- `audio_codec` (str): Codec de áudio (padrão: "aac")
- `overwrite` (bool): Sobrescrever ao invés de falhar (padrão: True)
- `dry_run` (bool): Apenas mostra comando sem executar (padrão: False)

**Retorna**: Tupla (output_path, cmd_list)

**Comando FFmpeg Utilizado**:
```
ffmpeg -y -i input.mp4 -af "anlmdn=s=0.05,afftdn=nf=-70:nt=v,highpass=f=250,\
lowpass=f=4000,equalizer=f=400:t=q:w=1:g=-5,equalizer=f=2500:t=q:w=1:g=-3,\
acompressor=threshold=-24dB:ratio=1.5:attack=15:release=100,adeclick=threshold=40" \
-c:v copy -c:a aac -b:a 192k output.mp4
```

**Exemplos**:
```python
# Enhance com configuração padrão
enhance_audio("video.mp4")

# Enhance customizado (mais agressivo em denoise)
enhance_audio(
    video_path="video.mp4",
    anlmdn_strength=0.1,  # Mais forte
    afftdn_nf=-80,        # Mais agressivo
    eq_bands=[(100, 1, -8), (400, 1, -5), (2500, 1, -3)]  # Mais equalizações
)

# Enhance leve (preservar mais nuances)
enhance_audio(
    video_path="video.mp4",
    anlmdn_strength=0.02,
    comp_ratio=1.2  # Menos compressão
)

# Dry-run
enhance_audio("video.mp4", dry_run=True)
```

**Tempo de Execução**: ~0.5-1.5x o tempo do vídeo

**Resultado Esperado**:
- ✅ Ruído de fundo reduzido ~50-70%
- ✅ Voz mais clara e presente
- ✅ Volume normalizado
- ✅ Clicks/pops removidos

---

#### `generate_spectrum(video_path, output_dir="spectrum_output", width=1280, height=720, scale="log", gain=10, start_freq=None, stop_freq=None, overwrite=True, dry_run=False)`

**Descrição**: Gera visualização em espectrograma do áudio de um vídeo (imagem do espectro de frequências).

**Parâmetros**:
- `video_path` (str): Caminho do vídeo de entrada
- `output_dir` (str): Diretório de saída para PNG (padrão: "spectrum_output")
- `width` (int): Largura da imagem em pixels (padrão: 1280)
- `height` (int): Altura da imagem em pixels (padrão: 720)
- `scale` (str): Escala do espectro - "log" (logarítmica) ou "lin" (linear) (padrão: "log")
- `gain` (int): Ganho visual do espectro (padrão: 10)
- `start_freq` (int): Frequência mínima em Hz (zoom inferior, opcional)
- `stop_freq` (int): Frequência máxima em Hz (zoom superior, opcional)
- `overwrite` (bool): Sobrescrever arquivo existente (padrão: True)
- `dry_run` (bool): Se True, retorna comando sem executar (padrão: False)

**Retorna**: Tupla (output_path, cmd_list)

**Comando FFmpeg Utilizado**:
```
ffmpeg -i video.mp4 -af "showspectrum=s=1280x720:scale=log:gain=10" \
-vframes 1 spectrum.png
```

**Cores do Espectrograma**:
- Azul (esquerda) = Frequências baixas (graves/baixo 20-250Hz)
- Verde (meio) = Frequências médias (corpo/presença 250-4000Hz)
- Vermelho (direita) = Frequências altas (agudos/treble 4000-20000Hz)
- Brilho = Intensidade (amplitude/volume)

**Exemplos**:
```python
# Gera espectro com configuração padrão (log scale)
generate_spectrum("video.mp4")

# Espectro linear (mostra amplitudes sem logaritmo)
generate_spectrum("video.mp4", scale="lin", gain=5)

# Zoom em frequências médias (200Hz a 8kHz)
generate_spectrum(
    video_path="interview.mp4",
    start_freq=200,
    stop_freq=8000,
    gain=15
)

# Alta resolução 4K
generate_spectrum("video.mp4", width=3840, height=2160)

# Dry-run
generate_spectrum("video.mp4", dry_run=True)
```

**Tempo de Execução**: ~5-10 segundos

**Resolução Output**: Customizável (padrão: 1280x720px)

---

### Casos de Uso

#### Cenário 1: Melhorar Áudio de Entrevista
```python
enhance_audio("entrevista_original.mp4", "entrevista_limpa.mp4")
```
Resultado: Voz mais clara, ruído de fundo minimizado

#### Cenário 2: Visualizar Qualidade Sonora
```python
generate_spectrum("lecture.mp3", "lecture_spectrum.png")
```
Resultado: PNG mostrando distribuição de frequências

#### Cenário 3: Pipeline Completo
```python
# 1. Melhorar áudio
enhance_audio("raw_video.mp4", "enhanced_video.mp4")

# 2. Visualizar resultado
generate_spectrum("enhanced_video.mp4", "spectrum.png")

# 3. Usar em next step do pipeline
# Exemplo: burn_subtitles_ffmpeg("enhanced_video.mp4", ...)
```

---

### Limitações

- Filtros são fixos (não configuráveis por parâmetro)
- Para customização: Modifique `enhance_audio()` diretamente
- Compressão pode soar artificial em áudio de música
- Ideal para: Fala, entrevistas, palestras
