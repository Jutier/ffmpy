import sys
from pathlib import Path
import logging
from .utils import run_ffmpeg
from .logs import log_function

logger = logging.getLogger(__name__)



@log_function
def trim_video(
	video_path: str,
	start_time: str,
	end_time: str,
	output_dir: str = "trim_output",
	dry_run: bool = False,
) -> tuple[str, list]:
	"""
	Corta um vídeo usando FFmpeg.
	
	Args:
		video_path (str): Caminho do vídeo de entrada
		start_time (str): Hora de início (MM:SS, MM:SS.ms ou HH:MM:SS)
		end_time (str): Hora de fim (MM:SS, MM:SS.ms ou HH:MM:SS)
		output_dir (str): Diretório de saída (padrão: "trim_output")
		dry_run (bool): Se True, retorna o comando sem executar (padrão: False)
	
	Returns:
		tuple[str, list]: (output_file, cmd) - Caminho de saída e comando FFmpeg como lista.
	"""
	# Cria pasta de saída
	output_path = Path(output_dir)
	output_path.mkdir(parents=True, exist_ok=True)
	
	# FFmpeg validará os timestamps automaticamente
	
	# Define nome do arquivo de saída (sempre automático)
	input_path = Path(video_path)
	trim_filename = f"{input_path.stem}_trim{input_path.suffix}"
	output_file = str(output_path / trim_filename)
	
	# Verifica se arquivo de entrada existe
	if not Path(video_path).exists():
		raise FileNotFoundError(f"Input file not found: {video_path}")
	
	# Constrói comando FFmpeg
	# Exemplo: ffmpeg -i input.mp4 -ss 00:01:22 -to 00:04:33 -c copy -y output_trimmed.mp4
	cmd = [
		"ffmpeg",
		"-y",
		"-i", str(video_path),
		"-ss", start_time,
		"-to", end_time,
		"-c", "copy",
		str(output_file),
	]
	
	logger.info(f"Trimming video...")
	
	# Executa FFmpeg
	cmd_result = run_ffmpeg(cmd, dry_run=dry_run)
	
	return output_file, cmd_result
