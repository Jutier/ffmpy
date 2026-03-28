# FFmpeg - Referência Rápida

Flags e filtros usados neste projeto.

---

## Flags Principais

| Flag | Significado | Exemplo |
|------|-------------|---------|
| `-i` | Input file | `-i video.mp4` |
| `-vf` | Video filter | `-vf "scale=1920:1080"` |
| `-af` | Audio filter | `-af "anlmdn=s=0.00005"` |
| `-ss` | Seek (tempo inicial) | `-ss 10` |
| `-to` | Trim até (tempo final) | `-to 120` |
| `-c copy` | Copy sem reencoding | `-c copy` |
| `-c:v` | Video codec | `-c:v libx264` |
| `-c:a` | Audio codec | `-c:a aac` |
| `-r` | Framerate | `-r 30` |

---

## Filtros de Vídeo

| Filtro | Sintaxe | Uso |
|--------|---------|-----|
| **scale** | `scale=1920:1080` | Redimensionar |
| **crop** | `crop=425:600:x:y` | Cortar área |
| **overlay** | `overlay=x:y` | Sobrepor imagem |
| **drawtext** | `drawtext=file=...` | Queimar texto/legendas |
| **fps** | `fps=30` | Ajustar framerate |
| **pad** | `pad=w:h:x:y` | Adicionar bordas |

---

## Filtros de Áudio

| Filtro | Uso | Exemplo |
|--------|-----|---------|
| **anlmdn** | Ruído de fundo | `anlmdn=s=0.00005` |
| **afftdn** | Denoiser FFT | `afftdn=nf=-25` |
| **equalizer** | EQ 3 bandas | `equalizer=f=1000:g=5:bw=2000` |
| **acompressor** | Compressor | `acompressor=ratio=2` |
| **adeclick** | Remove clicks | `adeclick` |

---

## Exemplos Usados

### Recortar Vídeo (Trim)
```bash
ffmpeg -ss 10 -i input.mp4 -to 120 -c copy output.mp4
```

### Redimensionar com AspectRatio
```bash
ffmpeg -i input.mp4 -vf "scale=425:-1" output.mp4
```

### Queimar Legendas
```bash
ffmpeg -i video.mp4 -vf "subtitles=subs.srt" output.mp4
```

### Melhorar Áudio (7 filtros)
```bash
ffmpeg -i input.mp4 -af "anlmdn=s=0.00005,afftdn=nf=-25,\
equalizer=f=1000:g=5:bw=2000,acompressor=ratio=2,adeclick" \
-c:v copy output.mp4
```

### Cortar Face com Overlay
```bash
ffmpeg -i input.mp4 -vf "crop=425:600:x:y" -c:v libx264 output.mp4
```

### Sobrepor Imagem
```bash
ffmpeg -i video.mp4 -i watermark.png -filter_complex "overlay=10:10" output.mp4
```

---

## Dicas Rápidas

- **Sempre use `-c copy`** quando possível (mais rápido)
- **Filtros de vídeo**: `-vf "filter1,filter2,filter3"` (usar vírgula para encadear)
- **Filtros de áudio**: `-af "filter1,filter2"` (mesmo padrão)
- **Manter qualidade**: Use `-c:v libx264` ou `copy` dependendo da necessidade
