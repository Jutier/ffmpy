# Módulo overlay.py

### Propósito
Adiciona marcas (watermarks) e outros no final do vídeo usando filtros FFmpeg complexos. Permite composição de múltiplas setas e elementos gráficos.

---

### Funções Principais

#### `add_mark(video_path, mark_path, output_dir="mark_output", ref_x="start", ref_y="start", margin_x=10, margin_y=10, dry_run=False)`

**Descrição**: Adiciona uma imagem (marca d'água) sobre um vídeo usando o filtro overlay do FFmpeg.

**Parâmetros**:
- `video_path` (str): Caminho do vídeo original
- `mark_path` (str): Caminho da imagem (PNG recomendado para transparência)
- `output_dir` (str): Diretório de saída (padrão: "mark_output")
- `ref_x` (str): Referência horizontal - "start", "center" ou "end" (padrão: "start")
- `ref_y` (str): Referência vertical - "start", "center" ou "end" (padrão: "start")
- `margin_x` (int): Margem horizontal em pixels (padrão: 10)
- `margin_y` (int): Margem vertical em pixels (padrão: 10)
- `dry_run` (bool): Se True, retorna comando sem executar (padrão: False)

**Retorna**: Tupla (output_path, cmd_list)

**Posicionamento**:
```
ref_x="start"   + margin_x → Esquerda (X pixels da borda esquerda)
ref_x="center"  + margin_x → Centralizado horizontalmente
ref_x="end"     + margin_x → Direita (X pixels da borda direita)

ref_y="start"   + margin_y → Topo (Y pixels do topo)
ref_y="center"  + margin_y → Centralizado verticalmente
ref_y="end"     + margin_y → Fundo (Y pixels do fundo)
```

**Comando FFmpeg Utilizado**:
```
ffmpeg -y -i video.mp4 -i watermark.png -filter_complex "overlay=x:y" -c:a copy output.mp4
```

**Exemplos**:
```python
# Marca no canto superior esquerdo
add_mark("video.mp4", "logo.png", margin_x=20, margin_y=20)

# Marca no canto inferior direito
add_mark("video.mp4", "logo.png", ref_x="end", ref_y="end", margin_x=20, margin_y=20)

# Marca centralizada
add_mark("video.mp4", "watermark.png", ref_x="center", ref_y="center")

# Marca superior centralizada
add_mark("video.mp4", "title.png", ref_x="center", ref_y="start", margin_y=50)
```

**Arquivo de Saída**: `{nome_video}_mark.mp4`

**Notas**:
- Imagem PNG com transparência é recomendada
- Imagens maiores que o vídeo são automaticamente redimensionadas
- Áudio é copiado sem reencoding (preserva qualidade)

---

#### `add_outro(video_path, outro_path, output_dir="outro_output", hex_color="#073b4c", fade_duration=1.0, crf=18, preset="medium", dry_run=False)`

**Descrição**: Adiciona um overlay de vídeo no final com fade e fundo colorido usando FFmpeg.

**Parâmetros**:
- `video_path` (str): Caminho do vídeo principal de entrada
- `outro_path` (str): Caminho do vídeo outro (será sobreposto no final)
- `output_dir` (str): Diretório de saída (padrão: "outro_output")
- `hex_color` (str): Cor de fundo em hex RGBA (padrão: "#073b4c" = azul escuro)
- `fade_duration` (float): Duração do fade em segundos (padrão: 1.0)
- `crf` (int): Qualidade libx264 (0-51, menor=melhor, 18=bom padrão) (padrão: 18)
- `preset` (str): Velocidade de encoding - "ultrafast", "fast", "medium", "slow" (padrão: "medium")
- `dry_run` (bool): Se True, retorna comando sem executar (padrão: False)

**Retorna**: Tupla (output_file, cmd_list)

**Comportamento**:
1. Obtém duração de ambos os vídeos
2. Cria transição de fade-out no vídeo principal
3. Sobrepõe o vídeo outro no final
4. Aplica fade-in no outro
5. Sincroniza áudio
6. Encoda com qualidade especificada

**Comando FFmpeg Utilizado (simplificado)**:
```
ffmpeg -filter_complex "[0:v]fade=t=out:st=<duration-fade>:d=<fade_duration>[v0];
[1:v]fade=t=in:st=0:d=<fade_duration>[v1];
[v0][1:a:0][v1][1:a:0]concat=n=2:v=1:a=1" \
-c:v libx264 -crf 18 -preset medium output.mp4
```

**Exemplos**:
```python
# Outro customizado com configuração padrão
add_outro("video.mp4", "outro.mp4")

# Outro com fade mais longo
add_outro("video.mp4", "outro.mp4", fade_duration=2.0)

# Outro com cor de fundo customizada (ouro)
add_outro("video.mp4", "outro.mp4", hex_color="#FFD700FF", fade_duration=1.5)

# Outro com qualidade alta (lento)
add_outro("video.mp4", "outro.mp4", crf=23, preset="slow")

# Outro rápido (qualidade reduzida)
add_outro("video.mp4", "outro.mp4", crf=28, preset="ultrafast")

# Dry-run
add_outro("video.mp4", "outro.mp4", dry_run=True)
```

**Arquivo de Saída**: `{nome_video}_outro.mp4`

**Tempo de Execução**: Depende do CRF e tamanho da outro. CRF 18 geralmente leva 1-3x o tempo total dos vídeos.

**Cores Recomendadas**:
- Azul escuro: "#073b4cFF"
- Preto: "#000000FF"
- Branco: "#FFFFFFFF"
- Transparente: "#00000000"

#### Troubleshooting
- Se marca não aparece: Verifique posição (mark_x, mark_y) e dimensões
- Se outro não sincroniza: Verifique compatibilidade de framerates e resoluções
