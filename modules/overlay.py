import logging
from pathlib import Path
from .utils import get_video_info, run_ffmpeg
from .logs import log_function

logger = logging.getLogger(__name__)


@log_function
def add_mark(
	video_path: str,
	mark_path: str,
	output_dir: str = "mark_output",
	ref_x: str = "start",
	ref_y: str = "start",
	margin_x: int = 10,
	margin_y: int = 10,
	dry_run: bool = False,
) -> tuple[str, list]:
	"""
	Adiciona uma imagem sobre um vídeo usando FFmpeg.
	
	Args:
		video_path (str): Caminho do vídeo original.
		mark_path (str): Caminho da imagem.
		output_dir (str): Diretório de saída.
		ref_x (str): Referência horizontal ("start", "center", "end").
		ref_y (str): Referência vertical ("start", "center", "end").
		margin_x (int): Margem horizontal em pixels.
		margin_y (int): Margem vertical em pixels.
		dry_run (bool): Se True, retorna comando sem executar (padrão: False).

	Returns:
		tuple[str, list]: (output_path, cmd) - Caminho de saída e comando FFmpeg como lista.
	"""
	video_path = Path(video_path)
	mark_path = Path(mark_path)
	output_dir = Path(output_dir)

	output_path = output_dir / f"{video_path.stem}_mark{video_path.suffix}"

	video_ffmpeg = video_path.as_posix()
	mark_ffmpeg = mark_path.as_posix()
	output_ffmpeg = output_path.as_posix()

	output_dir.mkdir(exist_ok=True, parents=True)
	
	# Mapeia start/center/end para expressões FFmpeg
	positions_x = {
		"start": f"{margin_x}",
		"center": f"(W-w)/2",
		"end": f"W-w-{margin_x}"
	}

	positions_y = {
		"start": f"{margin_y}",
		"center": f"(H-h)/2",
		"end": f"H-h-{margin_y}"
	}

	x = positions_x.get(ref_x, positions_x["start"])
	y = positions_y.get(ref_y, positions_y["start"])
	
	# Monta comando FFmpeg com overlay
	# Exemplo: ffmpeg -y -i video.mp4 -i watermark.png -filter_complex "overlay=50:50" -c:a copy output.mp4
	cmd = [
		"ffmpeg",
		"-y",
		"-i", str(video_ffmpeg),
		"-i", str(mark_ffmpeg),
		"-filter_complex", f"overlay={x}:{y}",
		"-c:a", "copy",
		str(output_ffmpeg),
	]

	logger.info("Marking video...")
	
	cmd_result = run_ffmpeg(cmd, dry_run=dry_run)
	
	return str(output_path), cmd_result


@log_function
def add_outro(
	video_path: str,
	outro_path: str,
	output_dir: str = "outro_output",
	hex_color: str = "#073b4c",
	fade_duration: float = 1,
	crf: int = 18,
	preset: str = "medium",
	dry_run: bool = False,
) -> tuple[str, list]:
	"""
	Adiciona um overlay com fade e fundo colorido no final de um vídeo usando FFmpeg.

	Args:
		video_path (str): Caminho do vídeo principal de entrada.
		outro_path (str): Caminho do vídeo outro (será sobreposto).
		output_dir (str): Diretório de saída (padrão: "output_overlay").
		hex_color (str): Cor em formato HEX (#RRGGBB) (padrão: "#073b4c").
		fade_duration (float): Duração do fade em segundos (padrão: 1).
		crf (int): CRF para qualidade libx264 (0-51, menor=melhor) (padrão: 18).
		preset (str): Preset de velocidade libx264 (ultrafast, fast, medium, slow) (padrão: "medium").
		dry_run (bool): Se True, retorna o comando sem executar (padrão: False).

	Returns:
		tuple[str, list]: (output_file, cmd) - Caminho de saída e comando FFmpeg como lista.
	"""
	input_path = Path(video_path)
	overlay_path = Path(outro_path)
	
	if not input_path.exists():
		raise FileNotFoundError(f"Input file not found: {video_path}")
	if not overlay_path.exists():
		raise FileNotFoundError(f"Overlay file not found: {outro_path}")

	# Obtém duração e dimensões dos vídeos
	input_info = get_video_info(video_path)
	outro_info = get_video_info(outro_path)
	
	input_duration = input_info['duration']
	outro_duration = outro_info['duration']
	video_width = input_info['width']
	video_height = input_info['height']

	# Calcula fade_start: começa a desaparecer fade_duration antes do fim
	fade_start = input_duration - fade_duration

	# Converte hex para RGB (remove # se houver)
	hex_clean = hex_color.lstrip("#")
	if len(hex_clean) == 6:
		color_hex = f"0x{hex_clean}"
	else:
		raise ValueError("HEX color must be in format #RRGGBB")

	# Cria pasta de saída
	output_path = Path(output_dir)
	output_path.mkdir(parents=True, exist_ok=True)

	input_ffmpeg = input_path.as_posix()
	overlay_ffmpeg = overlay_path.as_posix()
	output_file = output_path / f"{input_path.stem}_outro{input_path.suffix}"
	output_ffmpeg = output_file.as_posix()

	# Monta o filter_complex
	# [0:v] = vídeo principal com fade out
	# [bg] = fundo colorido
	# [1:v] = vídeo overlay com colorkey (transparência)
	# [v0][v1] = concatena os dois vídeos
	filter_complex = (
		f"[0:v]fade=t=out:st={fade_start}:d={fade_duration}:color={color_hex},format=yuv420p[v0];"
		f"color=c={color_hex}:s={video_width}x{video_height}:d={outro_duration}[bg];"
		f"[1:v]colorkey=black:0.2:0.0[ov];"
		f"[bg][ov]overlay[v1];"
		f"[v0][v1]concat=n=2:v=1:a=0[v]"
	)

	# Exemplo: ffmpeg -y -i input.mp4 -i overlay.mp4 -filter_complex "[0:v]fade=...;color=...;[1:v]colorkey=...;[bg][ov]overlay...;[v0][v1]concat..." -map "[v]" -map 0:a -c:v libx264 -c:a copy -crf 18 -preset medium output.mp4
	cmd = [
		"ffmpeg",
		"-y",
		"-i", input_ffmpeg,
		"-i", overlay_ffmpeg,
		"-filter_complex", filter_complex,
		"-map", "[v]",
		"-map", "0:a",
		"-c:v", "libx264",
		"-c:a", "copy",
		"-crf", str(crf),
		"-preset", preset,
		output_ffmpeg,
	]

	logger.info("Adding outro...")
	
	cmd_result = run_ffmpeg(cmd, dry_run=dry_run)
	
	return str(output_file), cmd_result
