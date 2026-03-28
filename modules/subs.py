import whisper
from pathlib import Path
import json
import logging
from .utils import hex_to_ass, run_ffmpeg
from .logs import log_function

logger = logging.getLogger(__name__)



@log_function
def transcribe_to_json(
	video_path: str,
	output_dir: str = "json_transcription",
	model_name: str = "small",
	language: str = None,
	word_timestamps: bool = True,
	device: str = "cpu",
	verbose: bool = False,
	dry_run: bool = False,
) -> str:
	"""
	Transcreve um vídeo usando Whisper e salva o resultado em JSON.

	Args:
		video_path (str): Caminho para o vídeo.
		output_dir (str): Diretório de saída para JSON.
		model_name (str): Nome do modelo Whisper (tiny, base, small, medium, large, turbo).
		language (str): Idioma da transcrição.
		word_timestamps (bool): Se True, inclui timestamps por palavra.
		device (str): "cuda" ou "cpu". Se cuda, usa fp16 automaticamente.
		verbose (bool): Se True, printa os segmentos transcritos.
		dry_run (bool): Se True, retorna path esperado sem executar transcrição.
	
	Returns:
		Path do JSON gerado.
	"""

	# Cria pasta de saída
	Path(output_dir).mkdir(parents=True, exist_ok=True)

	# Gera nome do arquivo JSON automaticamente
	video_stem = Path(video_path).stem.split("_")[0]
	json_filename = f"{video_stem}.json"
	json_path = Path(output_dir) / json_filename
	
	if dry_run:
		logger.info(f"Dry-run. No output created.")
		logger.info(f"❕ Some directories may have been created.")
		logger.info(f"JSON Path: {json_path}")
		return str(json_path)

	# Define fp16 baseado no device (True se CUDA, False se CPU)
	fp16 = (device == "cuda")

	logger.info(f"Loading model {model_name}...")
	model = whisper.load_model(model_name, device=device)

	logger.info(f"Transcribing {video_path}...")
	result = model.transcribe(
		video_path,
		language=language,
		word_timestamps=word_timestamps,
		fp16=fp16,
		verbose=verbose
	)

	logger.info(f"Saving JSON to {json_path}...")
	# Salvando manualmente em UTF-8
	with json_path.open("w", encoding="utf-8") as f:
		json.dump(result, f, ensure_ascii=False, indent=2)

	logger.info("Done!")
	return str(json_path)



@log_function
def json_to_srt(
	json_path: str,
	output_dir: str = "srt_transcription",
	max_char: int = 25,
	dry_run: bool = False,
) -> str:
	"""
	Gera um arquivo SRT a partir de um JSON do Whisper com word_timestamps.

	Args:
		json_path (str): Caminho do JSON do Whisper.
		output_dir (str): Diretório de saída para srt.
		max_char (int): Número máximo de caracteres por legenda.
		dry_run (bool): Se True, retorna path sem gerar arquivo.

	Returns:
		Path do arquivo SRT gerado.
	"""
	# garante que diretório existe
	Path(output_dir).mkdir(parents=True, exist_ok=True)

	# Gera nome do arquivo SRT automaticamente
	srt_filename = Path(json_path).stem.split("_")[0] + ".srt"
	srt_path = Path(output_dir) / srt_filename
	
	if dry_run:
		logger.info(f"Dry-run. No output created.")
		logger.info(f"❕ Some directories may have been created.")
		logger.info(f"SRT Path: {srt_path}.")
		return str(srt_path)
	
	with open(json_path, "r", encoding="utf-8") as f:
		data = json.load(f)

	segments = data.get("segments", [])

	srt_blocks = []
	current_text = ""
	current_start = None
	current_end = None

	def flush_block():
		nonlocal current_text, current_start, current_end

		if current_text.strip():
			srt_blocks.append((current_start, current_end, current_text.strip()))

		current_text = ""
		current_start = None
		current_end = None

	def to_srt_time(seconds):
		h = int(seconds // 3600)
		m = int((seconds % 3600) // 60)
		s = int(seconds % 60)
		ms = int((seconds - int(seconds)) * 1000)
		return f"{h:02}:{m:02}:{s:02},{ms:03}"

	for segment in segments:
		seg_text = segment.get("text", "")

		if len(seg_text) <= max_char:
			current_text = seg_text
			current_start = segment["start"]
			current_end = segment["end"]
			flush_block()
			continue
		
		words = segment.get("words", [])

		for i, word_info in enumerate(words):

			word = word_info["word"]
			start = word_info["start"]
			end = word_info["end"]

			next_word = words[i+1]["word"] if i+1 < len(words) else None

			if next_word and (next_word[-1] in ".!?") and (len(word + next_word) < max_char):
				add2 = current_text + word + next_word

				if len(add2) > max_char:
					flush_block()

			if (len(current_text) + len(word)) > max_char:
				flush_block()

			if current_start is None:
				current_start = start

			current_text += word
			current_end = end

			if word[-1] in ".!?":
				flush_block()

			elif len(current_text) > 0.5*max_char and word[-1] in ",;":
				flush_block()

			elif not next_word:
				flush_block()

	# escreve o SRT
	with open(srt_path, "w", encoding="utf-8") as f:
		for i, (start, end, text) in enumerate(srt_blocks, start=1):

			f.write(f"{i}\n")
			f.write(f"{to_srt_time(start)} --> {to_srt_time(end)}\n")
			f.write(f"{text}\n\n")

	return str(srt_path)



@log_function
def burn_subtitles_ffmpeg(
	video_path: str,
	srt_path: str,
	output_dir: str = "burn_video",
	font: str = "Calibri",
	font_dir: str = None,
	font_size: int = 20,
	primary_colour: str = "#eee0c9",
	outline_colour: str = "#0f1f24",
	outline: int = 2,
	# alignment: int = 10,
	margin_v: int = 65,
	margin_l: int = 10,
	margin_r: int = 10,
	dry_run: bool = False,
) -> tuple[str, list]:
	"""
	Queima legendas SRT em um vídeo usando FFmpeg (libass).

	Args:
		video_path (str): Caminho do vídeo de entrada.
		srt_path (str): Caminho do arquivo SRT.
		output_dir (str): Diretório de saída para vídeo legendado.
		font (str): Nome interno da fonte.
		font_dir (str): Diretório de fontes.
		font_size (int): Tamanho da fonte (pixels).
		primary_colour (str): Cor do texto, hex rgba.
		outline_colour (str): Cor do contorno, hex rgba.
		outline (int): Espessura do contorno (pixels).
		# alignment (int): Alinhamento. Ver: 57869367 stackoverflow
		margin_v (int): Margem vertical (pixels).
		margin_l (int): Margem esquerda (pixels).
		margin_r (int): Margem direita (pixels).
		dry_run (bool): Se True, retorna comando sem executar (padrão: False).

	Returns:
		tuple[str, list]: (output_path, cmd) - Caminho do vídeo e comando FFmpeg como lista.
	"""

	Path(output_dir).mkdir(parents=True, exist_ok=True)

	video_path = Path(video_path)
	srt_path = Path(srt_path)
	output_path = Path(output_dir) / f"{video_path.stem}_burn{video_path.suffix}"

	video_path = video_path.as_posix()
	srt_ffmpeg = srt_path.as_posix()
	output_ffmpeg = output_path.as_posix()

	primary_colour = hex_to_ass(primary_colour)
	outline_colour = hex_to_ass(outline_colour)

	# Prepara fontsdir se fornecido
	font_dir_option = ""
	if font_dir:
		font_dir_option = f":fontsdir={font_dir}"

	# monta a string do estilo ASS
	style = (
		f"FontName={font}"
		f",FontSize={font_size}"
		f",PrimaryColour={primary_colour}"
		f",OutlineColour={outline_colour}"
		f",Outline={outline}"
		# f",Alignment={alignment}"
		f",MarginV={margin_v}"
		f",MarginL={margin_l}"
		f",MarginR={margin_r}"
	)

	# monta o comando ffmpeg
	# Exemplo: ffmpeg -y -i input.mp4 -vf "subtitles='subs.srt':fontdir=fonts:force_style='FontName=Arial,...'" -c:a copy output.mp4
	cmd = [
		"ffmpeg",
		"-y",
		"-i", str(video_path),
		"-vf", f"subtitles='{srt_ffmpeg}'{font_dir_option}:force_style='{style}'",
		"-c:a", "copy",
		str(output_ffmpeg),
	]

	logger.info("Burning subtitles...")
	cmd_result = run_ffmpeg(cmd, dry_run=dry_run)

	return str(output_path), cmd_result
